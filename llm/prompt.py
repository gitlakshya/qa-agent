from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate,
)

import json
from langchain_core.output_parsers import JsonOutputParser 

examples = [
    {
        "input": "User Story: As a user, I want to reset my password if I forget it.\nMaster Doc: Password recovery via email.\nFeature Doc: Reset link sent to email.",
        "output": json.dumps({
            "testcases": [
                {
                    "Reference": "JIRA-123-TC01",
                    "Type": "Functional",
                    "Title": "Password reset via email",
                    "Precondition": "User has an account and forgot password",
                    "Steps": [
                        "Click 'Forgot password'",
                        "Enter registered email",
                        "Click link in email"
                    ],
                    "ExpectedResult": "User can set new password successfully"
                }
            ]
        }, indent=2)
    },
    {
        "input": "User Story: As a shopper, I want to add items to my cart.\nMaster Doc: Cart supports multiple items.\nFeature Doc: Add item, show cart contents.",
        "output": json.dumps({
            "testcases": [
                {
                    "Reference": "JIRA-321-TC01",
                    "Type": "Functional",
                    "Title": "Add item to empty cart",
                    "Precondition": "User logged in, product available",
                    "Steps": [
                        "Click 'Add to Cart'",
                        "Open cart page"
                    ],
                    "ExpectedResult": "Cart shows item with correct price"
                }
            ]
        }, indent=2)
    }
]

example_prompt = ChatPromptTemplate.from_messages([
    HumanMessagePromptTemplate.from_template("{input}"),
    AIMessagePromptTemplate.from_template("{output}")
])

few_shot_prompt = FewShotChatMessagePromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
)


# ---------- Full Prompt ----------
def get_prompt():
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
            "You are an Expert QA engineer AI. The input will include a user story (with its JIRA ID) and any related feature details." \
            "Your task is to thoroughly analyze this feature and produce a complete set of test cases covering every relevant scenario."
            "Deep Impact Analysis: Analyze the feature’s impact on the system. Consider related modules, dependencies, and how this feature integrates with or affects existing functionality. Think of all possible interactions and side effects."
            "Test Coverage Requirements: Generate test cases for all aspects of testing, including: Functional, Positive (Happy Paths), Negative (Unhappy Paths), Edge Cases, Regression, Security, UI/UX"
            "Return **ONLY valid JSON** in the following schema:\n\n"
            "[ {{\n      \"Reference\": \"<JIRA-ID-TC#>\",\n      \"Type\": \"Functional | Negative | Edge | Security | UI/UX | Regression\",\n      \"Title\": \"<short title>\",\n      \"Precondition\": \"<precondition>\",\n      \"Steps\": [\"<step1>\", \"<step2>\", ...],\n      \"ExpectedResult\": \"<expected result>\"\n    }}\n  ]"
        ),
        few_shot_prompt, 
        HumanMessagePromptTemplate.from_template(
            "User Story: {user_story}\n"
            "Context: {context}\n"
            "Generate the corresponding JSON test cases:"
        )
    ])
    return prompt

# # ---------- Schema ----------
# class TestCase(BaseModel):
#     Reference: str = Field(description="Unique ID of the test case")
#     Type: str = Field(description="Category (Functional, Negative, Edge, Security, UI/UX, Regression, etc.)")
#     Title: str = Field(description="Short descriptive title of the test case")
#     Precondition: str = Field(description="Preconditions for running the test")
#     Steps: List[str] = Field(description="Step-by-step instructions")
#     ExpectedResult: str = Field(description="Expected result after execution")

# class TestCaseList(BaseModel):
#     testcases: List[TestCase] = Field(
#         description="List of all generated test cases"
#     )

# ---------- Chain Builder ----------
def build_chain(llm):
    parser = JsonOutputParser()
    prompt = get_prompt()
    chain = prompt | llm | parser
    return chain