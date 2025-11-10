from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

import json
from langchain_core.output_parsers import JsonOutputParser 


class testGenerationChain:
    def __init__(self):
        pass

    def testGenerationPrompt(self):
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
            """
            You are a Senior QA Architect specializing in Impact Analysis and Automated Test Design.
            Your core task: **Analyze the provided user story and related documentation to generate a detailed suite of test cases**.

            ## Responsibilities
            - Perform **thorough impact analysis** to identify direct, indirect, and regression impacts.
            - Design test cases with **maximum scenario coverage** across all feature interactions.
            - Explicitly consider business logic, integrations, boundaries, security, and negative cases.

            ## Approach
            1. **Primary Feature**: Validate all new or modified functionality from the user story.
            2. **Integration**: Examine modules and services interacting with the primary feature.
            3. **Impact & Regression**: Uncover all downstream/upstream dependencies or regressions across impacted features.
            4. **Comprehensive Coverage**: Include positive, negative, edge, permission, error-handling, and data integrity scenarios.
            5. **Security & Permissions**: Ensure validation on authentication, access control, and data validation points.

            ## Impact Analysis Guidelines
            - Map all **data flows, triggers, shared entities, and inter-module dependencies**.
            - Identify **all UI, API, workflow, service, background process, and DB interactions**.
            - Highlight any logic likely to break or regress.

            ## Test Case Categories (each must be covered)
            - **Functional**: Acceptance criteria & core requirements
            - **Integration**: Interactions among modules/services/APIs
            - **Negative**: Invalid, misuse, or error scenarios
            - **Edge**: Boundary/value extremes, special cases, concurrency/timing
            - **Regression**: Historical flows that must stay unbroken
            - **Security**: Access, authorization, injection, data protection

            ## Quality Standards
            - Each test case must state intent, preconditions, clear steps, and a verifiable expected result.
            - Every impact point must be covered by at least one unique test.
            - Reference IDs must be sequential: TC-001, TC-002, ...

            ## Output
            - Output **only** a valid JSON array (no explanations/markdown).
            - Each element is a dict with these keys (and no others):
            "Reference", "Type", "Title", "Precondition", "Steps", "ExpectedResult"
            - Keep titles/steps concise, results explicit, and preconditions practical.

            [
                [
                    "Reference": "TC-001",
                    "Type": "Functional|Integration|Negative|Edge|Regression|Security",
                    "Title": "Brief test case description",
                    "Precondition": "System state or setup before execution",
                    "Steps": ["Step 1", "Step 2", "Step 3"],
                    "ExpectedResult": "Expected system behavior or output"
                ]
            ]

            Only output the JSON array. No explanations, reasoning, or commentary.
            """
            ),
            HumanMessagePromptTemplate.from_template(
            """
            User Story:
            {user_story}
            
            Primary Feature Documentation:
            {primary_feature_doc}
            
            Impacted Features Documentation:
            {impacted_features_doc}
            
            Perform step-by-step deep impact analysis (internally) and generate a thorough test suite.
            Only output the list of test cases as a valid JSON array.
            """
            )
        ])
        return prompt


    
    def build_chain(self, llm):
        parser = JsonOutputParser()
        prompt = self.testGenerationPrompt()
        chain = prompt | llm | parser
        return chain

class FeatureExtractionChain:
    def __init__(self):
        pass

    def featureExtractionPrompt(self, available_features=None):
        """
        Create prompt template for feature extraction with dynamic available features list.
        
        Args:
            available_features: List of available feature document names (without .pdf extension)
        """
        # Format available features as bullet list
        if available_features and len(available_features) > 0:
            features_list = "\n                ".join([f"- {feature}" for feature in available_features])
        else:
            # Fallback to default list if not provided
            features_list = """- Feature_Dashboards_All_Requests_and_My_Requests
                - Feature_Documents_Management
                - Feature_Comments
                - Feature_Request_and_Replies_via_Email
                - Feature_Request_Creation
                - Feature_Request_Type_Configurable_Forms
                - Feature_Tasks
                - Feature_Team_Management"""
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                f"""
                You are a Product Feature Mapping Expert with deep knowledge of software systems.
                Your task is to analyze a user story and product documentation to:
                1. Identify the **primary feature** being described.
                2. Identify any **dependent or impacted features** from the same list.

                ### Available Features (use EXACT names)
                {features_list}

                ### Decision Rules
                - The **primary feature** is the one that directly alignes with the area/feature being ammended or implemented.
                - A **dependent feature** is one that either:
                * provides supporting functionality required by the primary feature,
                * is triggered or updated as a result of the primary feature's workflow,
                * shares a direct data or UI linkage based on the product documentation.
                - If a feature is not clearly linked, **do not include it**.
                - Use only feature names from the list above.

                ### Reasoning
                - Think step-by-step about the story's purpose, input/output flow, and what core module it represents.
                - Map the user story's verbs and nouns to features logically.
                - Identify cross-feature interactions carefully (e.g., requests impacting tasks or dashboards).

                ### Output
                Return ONLY valid JSON in this exact format (no explanations, no markdown):

                "feature_name": "<primary_feature_name>",
                "dependent_features": ["<feature1>", "<feature2>"]

                If no dependent features are found, return an empty list.
                """
            ),
            HumanMessagePromptTemplate.from_template(
                """
                User Story:
                {user_story}

                Product Documentation:
                {product_documentation}

                Based on the documentation and story, extract the primary feature and its dependent/impacted features.
                Think internally step-by-step but return ONLY the JSON output.
                """
            )
        ])
        return prompt

    
    def build_chain(self, llm, available_features=None):
        """
        Build the complete feature extraction chain.
        
        Args:
            llm: Language model instance
            available_features: List of available feature document names
        """
        parser = JsonOutputParser()
        prompt = self.featureExtractionPrompt(available_features)
        chain = prompt | llm | parser
        return chain


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



