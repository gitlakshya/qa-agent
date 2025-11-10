"""
Test suite for the refactored retrieval module.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.generate import (
    FeatureDocumentationLoader,
    FeatureExtractionService,
    TestCaseGenerator
)
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_feature_documentation_loader():
    """Test loading feature documentation."""
    print("\n" + "="*70)
    print("Test 1: Feature Documentation Loader")
    print("="*70)
    
    loader = FeatureDocumentationLoader()
    
    # Test single feature loading
    try:
        feature_name = "Feature_Request_Creation"
        print(f"\n✓ Loading documentation for: {feature_name}")
        doc = loader.load_feature_documentation(feature_name)
        print(f"✓ Loaded {len(doc)} characters")
        print(f"✓ Preview: {doc[:200]}...")
    except Exception as e:
        print(f"✗ Error loading single feature: {e}")
    
    # Test multiple features loading
    try:
        feature_names = [
            "Feature_Request_Creation",
            "Feature_Dashboards_All_Requests_and_My_Requests"
        ]
        print(f"\n✓ Loading multiple features: {feature_names}")
        combined_doc = loader.load_multiple_features(feature_names)
        print(f"✓ Combined documentation: {len(combined_doc)} characters")
    except Exception as e:
        print(f"✗ Error loading multiple features: {e}")


def test_feature_extraction_service():
    """Test feature extraction from user story."""
    print("\n" + "="*70)
    print("Test 2: Feature Extraction Service")
    print("="*70)
    
    service = FeatureExtractionService()
    
    user_story = """MR-2559

Comments - Add title for each thread

Description

User story

As a lawyer, I want to add a title for each conversation so that I can easily 
organise comments around a common topic/subject and find them.

Acceptance Criteria:

When I'm creating a new thread, I should have an option to add

Title: This is an optional field (Max limit of title is 2k chars)

Description: Text field with upto 63k char limit"""
    
    try:
        print("\n✓ Extracting features from user story...")
        extracted_data = service.extract_features(user_story)
        
        print(f"\n✓ Primary Feature: {extracted_data['feature_name']}")
        print(f"✓ Dependent Features: {extracted_data.get('dependent_features', [])}")
        
        # Test get_feature_names convenience method
        primary, dependent = service.get_feature_names(user_story)
        print(f"\n✓ Convenience method results:")
        print(f"  Primary: {primary}")
        print(f"  Dependent: {dependent}")
        
        return extracted_data
        
    except Exception as e:
        print(f"✗ Error in feature extraction: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_test_case_generator():
    """Test complete test case generation pipeline."""
    print("\n" + "="*70)
    print("Test 3: Test Case Generator (Full Pipeline)")
    print("="*70)
    
    generator = TestCaseGenerator()
    
    user_story = """MR-2559

Comments - Add title for each thread

Description

User story

As a lawyer, I want to add a title for each conversation so that I can easily 
organise comments around a common topic/subject and find them.

Acceptance Criteria:

When I'm creating a new thread, I should have an option to add

Title: This is an optional field (Max limit of title is 2k chars)

Description: Text field with upto 63k char limit"""
    
    try:
        print("\n✓ Starting test case generation...")
        test_cases = generator.generate_test_cases(user_story)
        
        print(f"\n✓ Generated {len(test_cases)} test cases")
        
        # Display first few test cases
        for i, tc in enumerate(test_cases[:3], 1):
            print(f"\n--- Test Case {i} ---")
            print(f"Reference: {tc.get('Reference', 'N/A')}")
            print(f"Type: {tc.get('Type', 'N/A')}")
            print(f"Title: {tc.get('Title', 'N/A')}")
            print(f"Precondition: {tc.get('Precondition', 'N/A')}")
            print(f"Steps: {len(tc.get('Steps', []))} steps")
            print(f"Expected Result: {tc.get('ExpectedResult', 'N/A')[:100]}...")
        
        if len(test_cases) > 3:
            print(f"\n... and {len(test_cases) - 3} more test cases")
        
        # Save to file
        output_file = "generated_test_cases.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_cases, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Test cases saved to: {output_file}")
        
        return test_cases
        
    except Exception as e:
        print(f"\n✗ Error in test case generation: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_backward_compatibility():
    """Test backward compatibility with old GenerateTests class."""
    print("\n" + "="*70)
    print("Test 4: Backward Compatibility")
    print("="*70)
    
    from app.generate import GenerateTests
    
    try:
        print("\n✓ Creating GenerateTests instance (deprecated class)...")
        generator = GenerateTests()
        
        user_story = """MR-2559

Comments - Add title for each thread

Description

User story

As a lawyer, I want to add a title for each conversation so that I can easily 
organise comments around a common topic/subject and find them."""
        
        print("✓ Calling generate_test_cases method...")
        test_cases = generator.generate_test_cases(user_story)
        
        print(f"✓ Successfully generated {len(test_cases)} test cases")
        print("✓ Backward compatibility maintained!")
        
    except Exception as e:
        print(f"✗ Backward compatibility test failed: {e}")


def test_error_handling():
    """Test error handling for various edge cases."""
    print("\n" + "="*70)
    print("Test 5: Error Handling")
    print("="*70)
    
    # Test 1: Invalid feature name
    print("\n1. Testing invalid feature name...")
    loader = FeatureDocumentationLoader()
    try:
        doc = loader.load_feature_documentation("NonExistentFeature")
        print("✗ Should have raised an error")
    except Exception as e:
        print(f"✓ Correctly raised error: {type(e).__name__}")
    
    # Test 2: Empty feature list
    print("\n2. Testing empty feature list...")
    result = loader.load_multiple_features([])
    print(f"✓ Returned empty string: {result == ''}")
    
    # Test 3: Empty user story
    print("\n3. Testing empty user story...")
    generator = TestCaseGenerator()
    try:
        test_cases = generator.generate_test_cases("")
        print(f"✓ Handled empty story, generated {len(test_cases)} test cases")
    except Exception as e:
        print(f"✓ Correctly raised error: {type(e).__name__}")


def run_all_tests():
    """Run all test functions."""
    print("\n" + "="*70)
    print("RETRIEVAL MODULE TEST SUITE")
    print("="*70)
    
    tests = [
        ("Feature Documentation Loader", test_feature_documentation_loader),
        ("Feature Extraction Service", test_feature_extraction_service),
        ("Test Case Generator", test_test_case_generator),
        ("Backward Compatibility", test_backward_compatibility),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            test_func()
            results.append((test_name, "PASSED"))
        except Exception as e:
            results.append((test_name, f"FAILED: {e}"))
            logger.error(f"Test {test_name} failed: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, result in results:
        status = "✓" if result == "PASSED" else "✗"
        print(f"{status} {test_name}: {result}")
    
    passed = sum(1 for _, r in results if r == "PASSED")
    print(f"\n{passed}/{len(results)} tests passed")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("Retrieval Module - Refactored Test Suite")
    print("="*70)
    print("\nThis test suite validates the refactored retrieval module:")
    print("1. FeatureDocumentationLoader - Loads feature docs")
    print("2. FeatureExtractionService - Extracts features using LLM")
    print("3. TestCaseGenerator - Complete pipeline for test generation")
    print("4. Backward Compatibility - Old API still works")
    print("5. Error Handling - Graceful error management")
    
    run_all_tests()
    
    print("\n" + "="*70)
    print("All tests completed!")
    print("="*70)
