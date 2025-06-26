import os
from langgraph_sdk import get_client
from langgraph_sdk.schema import Command
import asyncio
# from wayflowcore.tools import tool


async def hitl_call_async() -> str:
    # Connect to langgraph instance
    langgraph_url="http://localhost:2024"

    if not langgraph_url:
        raise ValueError(" Environment variable 'langgraph_url' is not set.")
    
    client = get_client(url=langgraph_url)
    # Using the graph deployed with the name "hitl"
    assistant_id = "agent"
    

    # create a thread
    thread = await client.threads.create()
    thread_id = thread["thread_id"]

    # Run the graph until the interrupt is hit.
    await client.runs.wait(
        thread_id,
        assistant_id,
        input={}   
    )

    return "triggered_hitl_call"


    
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
result = loop.run_until_complete(hitl_call_async())
loop.close()
print(result)