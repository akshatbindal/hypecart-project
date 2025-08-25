import asyncio
import json
from google.genai import types as genai_types

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Import the agents defined in the 'agents' package
from agents import (
    user_profiler_agent,
    cart_inspector_agent,
    video_production_agent,
    # We import the other agents to show they are part of the system,
    # but we will mock their output for deterministic orchestration.
    narrative_generator_agent,
    veo_prompt_generator_agent,
)

async def run_agent(runner, session, prompt_text):
    """Helper function to run an agent and extract the final text response."""
    print(f"\n----- Running Agent: {runner.agent.name} -----")
    print(f"Prompt: {prompt_text}")

    content = genai_types.Content(role="user", parts=[genai_types.Part(text=prompt_text)])

    final_event = None
    async for event in runner.run_async(session_id=session.id, user_id=session.user_id, new_message=content):
        print(f"Event from {runner.agent.name}: {event.type}...")
        final_event = event

    # The final output is in the 'text' part of the last event's content
    if final_event and final_event.content and final_event.content.parts:
        # The tool output is often a JSON string in the text field
        raw_text = ""
        # The response can have multiple parts, we need to find the text part from the tool
        for part in final_event.content.parts:
            if hasattr(part, 'text'):
                raw_text = part.text
                break
            # Tool output is in a function_response
            if hasattr(part, 'function_response'):
                # The actual data is often in a 'text_output' field inside the response
                if 'text_output' in part.function_response.response:
                    raw_text = part.function_response.response['text_output'][0]['text']
                    break

        print(f"Raw Output: {raw_text}")
        try:
            # Try to parse it as JSON
            return json.loads(raw_text)
        except (json.JSONDecodeError, TypeError):
            # If not JSON, return the raw text
            return raw_text
    return None

async def main():
    """Main orchestrator for the HypeCart agent pipeline."""
    print("🚀 Starting HypeCart Agent Pipeline...")

    # Setup session and services for the run
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name="hypecart_mvp", user_id="user123")

    # --- Step 1: Get User Profile ---
    profiler_runner = Runner(agent=user_profiler_agent, session_service=session_service)
    user_profile = await run_agent(profiler_runner, session, "Fetch profile for user_id 'user123'")
    print(f"✅ User Profile Fetched: {json.dumps(user_profile, indent=2)}")

    # --- Step 2: Get User Cart ---
    cart_runner = Runner(agent=cart_inspector_agent, session_service=session_service)
    user_cart = await run_agent(cart_runner, session, "Fetch cart for user_id 'user123'")
    print(f"✅ Cart Data Fetched: {json.dumps(user_cart, indent=2)}")

    if not user_profile or not user_cart or "error" in user_profile or "error" in user_cart:
        print("🔴 Could not retrieve user or cart data. Aborting pipeline.")
        return

    # --- Step 3: Generate Narrative (Mocked) ---
    print(f"\n----- Running Agent: {narrative_generator_agent.name} (Mocked) -----")
    product_name = user_cart['items'][0]['name']
    user_name = user_profile['name']
    generated_script = f"{user_name}, your {product_name} are waiting to hit the road."
    print(f"✅ Narrative Generated: '{generated_script}'")

    # --- Step 4: Generate Veo Prompt (Mocked) ---
    print(f"\n----- Running Agent: {veo_prompt_generator_agent.name} (Mocked) -----")
    veo_prompt = (
        f"Cinematic 4K shot of '{product_name}' on wet Mumbai streets during monsoon, "
        "dynamic movement through puddles, rain drops on the lens, urban landscape, "
        "ending with a hero shot. "
        "Audio: Ambient city rain sounds with upbeat, adventurous music. Duration: 8 seconds."
    )
    print(f"✅ Veo Prompt Generated: '{veo_prompt}'")

    # --- Step 5: Produce Video ---
    video_runner = Runner(agent=video_production_agent, session_service=session_service)
    video_prompt = (
        "Generate a video ad using the following details:\n"
        f"Prompt: {veo_prompt}\n"
        f"User Profile: {json.dumps(user_profile)}\n"
        f"Product Info: {json.dumps(user_cart['items'][0])}"
    )
    video_result = await run_agent(video_runner, session, video_prompt)
    print(f"✅ Video Production Triggered: {json.dumps(video_result, indent=2)}")

    if video_result and "video_url" in video_result:
        print(f"\n🎉 HypeCart Pipeline Complete! Generated Video URL: {video_result['video_url']}")
    else:
        print("\n🔴 HypeCart Pipeline Failed. Could not generate video.")

    # Gracefully close the toolsets to terminate the MCP server subprocesses
    print("\nShutting down API toolsets...")
    # The toolset is the first and only tool in the list for these agents
    await profiler_runner.agent.tools[0].close()
    await cart_runner.agent.to_proto().tools[0].close()
    await video_runner.agent.tools[0].close()
    print("Shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
