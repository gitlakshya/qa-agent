import asyncio
from llm.connector import azurellm
from llm.prompt import build_chain
from app.generate import retrieve_info
import json

async def run_example():
    # Sample inputs
    user_story = (
        """User story

As a request doer, I want to receive notification when there is no assignment so that I can act on the query.

Precondition

Request assignee is blank

An external/internal comment is added

Acceptance criteria

Case 1 - Notify req based on user profile

Given that the request data matches BU, Region, Req type then

all users with that should receive a notification with the comment"""
    )

    context = retrieve_info(user_story)

    
    chain = build_chain(azurellm)
    # Invoke the chain asynchronously (assuming an async context)
    output = await chain.ainvoke({
        "user_story": user_story,
        "context": context,
    })
    print(json.dumps(output))


asyncio.run(run_example())
