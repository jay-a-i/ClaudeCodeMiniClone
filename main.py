import os
import json
import time
import asyncio
import inspect
from dotenv import load_dotenv
from openai import AsyncOpenAI, RateLimitError
from sys_prompts import system_prompt
from tools import TOOLS
from tool_schemas import tool_schema

load_dotenv()

client = AsyncOpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv("GOOGLE_API_KEY")
  )

async def execute_tool(tool_name, args):
    tool_func = TOOLS[tool_name]

    if inspect.iscoroutinefunction(tool_func):
        return await tool_func(**args)

    return tool_func(**args)


async def main(user_input):
    MAX_ITERATIONS = 50
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_input
        }
    ]

    for iteration in range(MAX_ITERATIONS):

        print(f"\n--- Iteration {iteration+1} ---")

        tool_calls_accumulator = {}

        try:
            stream = await client.chat.completions.create(
                model="gemini-2.5-flash",
                messages=messages,
                tools=tool_schema,
                tool_choice="auto",
                stream=True,
                #extra_body={"reasoning": {"enabled": True}}
            )

            async for chunk in stream:
                if not chunk.choices:
                    continue
                
                delta = chunk.choices[0].delta

                if delta.content:
                    print(delta.content, end="", flush=True)

                if delta.tool_calls:
                    for tc in delta.tool_calls:

                        idx = tc.index

                        if idx not in tool_calls_accumulator:

                            tool_calls_accumulator[idx] = {
                                "id": "",
                                "name": "",
                                "arguments": ""
                            }

                        if tc.id:
                            tool_calls_accumulator[idx]["id"] += tc.id

                        if tc.function.name:
                            tool_calls_accumulator[idx]["name"] += tc.function.name

                        if tc.function.arguments:
                            tool_calls_accumulator[idx]["arguments"] += tc.function.arguments
        
        except RateLimitError as e:
            print("[Hit Rate Limit]: Staring in a moment...")
            time.sleep(36)
            asyncio.run(main(user_input=messages))

        except Exception as e:
            print(f"\n[Model Error]: {e}")
            return
        
        if not tool_calls_accumulator:
            print("\n\n[Agent Finished]")
            break

        messages.append(
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": tool["id"],
                        "type": "function",
                        "function": {
                            "name": tool["name"],
                            "arguments": tool["arguments"]
                        }
                    }
                    for tool in tool_calls_accumulator.values()
                ]
            }
        )
        for tool in tool_calls_accumulator.values():
            print(f"\n[Executing Tool] {tool['name']}")

            try:
                args = json.loads(tool["arguments"])
                result = await execute_tool(tool["name"], args)
            except Exception as e:
                result = {"error": str(e)}
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool["id"],
                    "content": json.dumps(result)
                }
            )
    
    else:
        print("\n[Max iterations reached]")

if __name__ == "__main__":
    user_input = input("Enter a prompt:  ")
    asyncio.run(main(user_input=user_input))