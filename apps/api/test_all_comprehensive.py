import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api"

async def test_agent_creation():
    print("\n--- Testing Agent Creation ---")
    async with httpx.AsyncClient() as client:
        payload = {
            "name": "TestBot",
            "description": "A test agent created dynamically",
            "template": "blank",
            "custom_prompt": "You are a test bot."
        }
        # Note: /api/agents/create requires auth (get_current_user).
        # We might get 401 if we don't pass a token, but let's check.
        try:
            # First let's do a simple unauthenticated request to see if it works or fails with 401/403
            resp = await client.post(f"{BASE_URL}/agents/create", json=payload)
            print("Create Agent Response Status:", resp.status_code)
            if resp.status_code == 401 or resp.status_code == 403:
                print("Agent creation requires authentication as expected.")
            else:
                print("Agent Create Response:", resp.json())
        except Exception as e:
            print("Error creating agent:", str(e))

async def test_agents_list():
    print("\n--- Testing Agents List ---")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{BASE_URL}/agents/list")
            print("Agents List Status:", resp.status_code)
            data = resp.json()
            if "agents" in data:
                print(f"Successfully retrieved {len(data['agents'])} agents.")
                for a in data["agents"][:3]:
                    print(f" - {a.get('name')} ({a.get('category', 'unknown')})")
            else:
                print("Agents List Response:", data)
        except Exception as e:
            print("Error listing agents:", str(e))

async def test_computer_use():
    print("\n--- Testing Computer Use Module ---")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{BASE_URL}/computer/info")
            print("Computer Info Status:", resp.status_code)
            print("Computer Capabilities:", resp.json().get('capabilities'))
            
            resp_shot = await client.post(f"{BASE_URL}/computer/screenshot")
            print("Screenshot Status:", resp_shot.status_code)
            shot_data = resp_shot.json()
            if shot_data.get("success"):
                print(f"Screenshot taken successfully! Size: {shot_data.get('width')}x{shot_data.get('height')}")
            else:
                print("Screenshot failed:", shot_data)
        except Exception as e:
            print("Error in computer use:", str(e))

async def main():
    await test_agents_list()
    await test_agent_creation()
    await test_computer_use()
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
