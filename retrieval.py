from prompt import qa_prompt
from embed import vectorstore
from connector import llm


retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

def retrieve_info(query):
    related_docs = retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in related_docs])
    return context

def generate_test_cases(user_story):
    context = retrieve_info(user_story)
    prompt = qa_prompt.format(story=user_story, context=context)
    
    print("About to invoke LLM...")
    
    response = llm.invoke(prompt)
    print(f"Response type: {type(response)}")
    print(f"Response: {response}")
    return response
 

if __name__ == "__main__":
    user_story = """Background

Admin currently has access to all data within the application even when they do not have access to all metadata. For accurate data access control, admin roles in other ELM modules only show data based on user profile.

Acceptance criteria

Case 1 - Request data access for admin roles

Given

When

Then

I’m a Tenant admin/Super admin role

I’m on all request page

I should only see the request based on my metadata access (BU, Geo, Request type)

The data in KPI charts should be based on the data visible to my user

"""
    import json
    test_cases = generate_test_cases(user_story)
    if test_cases:
        try:
            json.loads(test_cases)
            print("Test cases generated successfully")
        except json.JSONDecodeError:
            print("JSON Failure")
    else:
        print("Failed to generate test cases")