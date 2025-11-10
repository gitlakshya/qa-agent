import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.generate import TestCaseGenerator
from data_pipeline import VectorStoreNotFoundError, VectorStoreCorruptedError
import json


user_story = """MR-2559
Comments - Add title for each thread

Description

User story

As a lawyer, I want to add a title for each conversation so that I can easily ogranise comments around a common topic/subject and find them.

Acceptance Criteria:

When I’m creating a new thread, I should have an option to add

Title: This is an optional field (Max limit of title is 2k chars)

Description: Text field with upto 63k char limit"""

def test_directsearch():
    test = TestCaseGenerator()
    result = test.generate_test_cases(user_story)
    print(json.dump(result))

    return json.dump(result)

test_directsearch()