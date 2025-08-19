from langchain.prompts import PromptTemplate

qa_prompt = PromptTemplate(
    input_variables=["story", "context"],
    template="""
You are an expert AI Software QA.

USER STORY:
{story}

RELATED DOCUMENTATION:
{context}

TASK:
1. Analyze the feature story for impacted areas, logical challenges
2. Generate  comprehensive test cases in detail with fields:
   - Reference, Category (Functional/Negative/Edge/Regression),
   - Title, Preconditions, Steps, ExpectedResult

Return JSON array only.
"""
)
