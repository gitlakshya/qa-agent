import logging
from llm.prompt import build_chain
from app.embed import vectorstore
from llm.connector import azurellm


logger = logging.getLogger(__name__)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

def retrieve_info(query):
    related_docs = retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in related_docs])
    return context

def generate_test_cases(user_story):
    context = retrieve_info(user_story)
    prompt = build_chain.format(story=user_story, context=context)
    
    logger.info("About to invoke LLM...")
    
    response = azurellm.invoke(prompt)
    logger.debug("Response type: %s", type(response))
    logger.info("Response received from LLM")
    return response
 

if __name__ == "__main__":
    user_story = """Background

Admin currently has access to all data within the application even when they do not have access to all metadata. For accurate data access control, admin roles in other ELM modules only show data based on user profile.

Acceptance criteria
Case 1 - Request data access for admin roles

Given: I’m a Tenant admin/Super admin role
When: I’m on all request page
Then:
I should only see the request based on my metadata access (BU, Geo, Request type)

The data in KPI charts should be based on the data visible to my user
"""
    import json
    test_cases = generate_test_cases(user_story)
    logger.info("Test cases generated: %s", test_cases)
    if test_cases:
        try:
            json.loads(test_cases.content)
            logger.info("Test cases generated successfully")
        except json.JSONDecodeError:
            logger.warning("LLM output is not valid JSON")
    else:
        logger.error("Failed to generate test cases")