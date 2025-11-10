from llm.prompt import FeatureExtractionChain
from .document_loader import DocumentLoader


class FeatureExtractor:
    """ Extracts the feature list from user story and return the feature in change and its impacted features"""
    def __init__(self):
        pass

    def load_product_documentation(self, filePath):
        doc_loader = DocumentLoader()
        chunks = doc_loader.load_file(filePath)
        product_doc = doc_loader.join_docs_content(chunks)
        return product_doc

    def extract_features(self, user_story, filePath, azurellm, available_features=None):
        """
        Extract features from user story using product documentation.
        
        Args:
            user_story: The user story text
            filePath: Path to the product documentation
            azurellm: Azure LLM instance
            available_features: List of available feature document names
            
        Returns:
            Dictionary with feature_name and dependent_features
        """
        try:
            doc_loader = DocumentLoader()
            chunks = doc_loader.load_file(filePath)
            product_documentation = doc_loader.join_docs_content(chunks)
            
            feature_chain = FeatureExtractionChain()
            chain = feature_chain.build_chain(azurellm, available_features=available_features)
            
            response = chain.invoke({
                "user_story": user_story, 
                "product_documentation": product_documentation
            })
            return response
        except Exception as e:
            print(f"Error in extract_features: {e}")
            raise