import os
import json
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from tavily import AsyncTavilyClient

load_dotenv()

tavily = AsyncTavilyClient(os.getenv("TAVILY_API_KEY"))
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
  )

async def search_web(query: str):
    response = await tavily.search(
        query=query,
        max_results=3,
        search_depth='advanced')
    content_list = []
    for result in response['results']:
        content_list.append(f"Source: {result['url']}\nContent: {result['content']}")
    return "\n\n".join(content_list)

tool_schema = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the internet for up-to-the-minute real-time information, news, dates, and live events.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query keywords to look up on the web."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

async def main():
  
  messages = [
    {"role": "user", "content": "What major FIFA football matches are scheduled for tonight?"}
  ]

  stream = await client.chat.completions.create(
      model="nex-agi/nex-n2-pro:free",
      messages=messages,
      tools=tool_schema,
      tool_choice='auto',
      stream=True,
      extra_body={"reasoning": {"enabled": True}}
  )

  tool_call_detected = False
  tool_name = ""
  tool_arguments_stream = ""

  async for chunk in stream:
      if chunk.choices:
          content = chunk.choices[0].delta.content
          if content:
              print(content, end="", flush=True)

          tool_calls = chunk.choices[0].delta.tool_calls
          if tool_calls:
              tool_call_detected = True
              delta_tool = tool_calls[0]

              if delta_tool.function.name:
                  tool_name += delta_tool.function.name

              if delta_tool.function.arguments:
                  tool_arguments_stream += delta_tool.function.arguments
                  print(".", end="", flush=True)

  if tool_call_detected:
      print(f"\n\n[Tool Triggered]: Model requested function '{tool_name}'")
      try:
          parsed_args = json.loads(tool_arguments_stream)
          search_query = parsed_args.get("query", "")
          print(f"[Tool Executing]: Searching Tavily for: \"{search_query}\"")
          
          search_result_context = await search_web(search_query)

          call_id = "call_" + os.urandom(4).hex()

          messages.append({
              "role": "assistant", 
              "content": "", 
              "tool_calls": [{
                  "id": call_id, 
                  "type": "function",
                  "function": {"name": tool_name, "arguments": tool_arguments_stream}
              }]
          })
          messages.append({
              "role": "tool", 
              "tool_call_id": call_id, 
              "name": tool_name, 
              "content": search_result_context
          })

          messages.append({
                "role": "system",
                "content": "Answer the user's question directly using the context data given above."
            })

          print("[System]: Sending web context back to model for final answer...\n")
          final_stream = await client.chat.completions.create(
              model="openai/gpt-oss-120b:free",
              messages=messages,
              stream=True,
              extra_body={"reasoning": {"enabled": True}}
          )
          
          async for chunk in final_stream:
              if chunk.choices and chunk.choices[0].delta.content:
                  print(chunk.choices[0].delta.content, end="", flush=True)
                  
      except json.JSONDecodeError:
          print("\n[Error]: Failed to parse tool argument strings from model.")
          
  print()
if __name__ == "__main__":
    asyncio.run(main())
