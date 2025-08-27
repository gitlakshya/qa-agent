import json
from typing import List, Dict, Optional
import streamlit as st
import asyncio

# LangChain & community loaders
from langchain_community.document_loaders import PyPDFLoader, UnstructuredHTMLLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm.connector import azurellm
from llm.prompt import build_chain
from langchain_core.output_parsers import JsonOutputParser
from langchain.schema import BaseOutputParser
from retrieval import retrieve_info
from load_chunk import LoadandChunk

# ---------- Utils ----------
def truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars-3] + "..."


class DocumentLoader(LoadandChunk):
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def load_pdf(self, path: str):
        loader = PyPDFLoader(path)
        docs = loader.load()
        return self.splitter.split_documents(docs)

    def load_html(self, path: str):
        loader = UnstructuredHTMLLoader(path)
        docs = loader.load()
        return self.splitter.split_documents(docs)

    def load_text(self, path: str):
        loader = TextLoader(path, encoding="utf-8")
        docs = loader.load()
        return self.splitter.split_documents(docs)

    def load_any(self, path: str):
        path = path.lower()
        if path.endswith(".pdf"):
            return self.load_pdf(path)
        if path.endswith(".html") or path.endswith(".htm"):
            return self.load_html(path)
        if path.endswith(".txt") or path.endswith(".md"):
            return self.load_text(path)
        raise ValueError(f"Unsupported file type for {path}")


class FeatureRouter:
    def __init__(self, llm, keyword_map: Dict[str, str], router_prompt_max_chars: int = 5000):
        self.llm = llm
        self.keyword_map = keyword_map
        self.router_template = PromptTemplate(
            input_variables=["story", "candidates"],
            template=(
                "You are a smart document router. Given the USER STORY, return a JSON array of "
                "the NAMES (not full paths) of the feature documents that are relevant. "
                "Only return the JSON array and nothing else.\n\n"
                "USER STORY:\n{story}\n\n"
                "AVAILABLE FEATURE DOCS:\n{candidates}\n\n"
                "Pick the most relevant 1-3 feature doc names."
            )
        )
        self.router_prompt_max_chars = router_prompt_max_chars
        self.output_parser: BaseOutputParser = JsonOutputParser()

    def _build_candidates_text(self) -> str:
        return "\n".join(f"- {name}" for name in self.keyword_map.keys())

    async def route(self, story: str, max_retries: int = 2) -> List[str]:
        candidates = self._build_candidates_text()
        prompt = self.router_template.format(
            story=truncate_text(story, self.router_prompt_max_chars),
            candidates=candidates
        )

        for attempt in range(max_retries):
            raw = await self.llm.ainvoke(prompt)
            try:
                parsed = self.output_parser.parse(raw.content if hasattr(raw, 'content') else str(raw))
                if isinstance(parsed, list) and len(parsed) > 0:
                    result = [str(x).strip() for x in parsed]
                    selected = [r for r in result if r in self.keyword_map]
                    if selected:
                        return selected
            except Exception:
                pass

            lowers = story.lower()
            hits = [name for name in self.keyword_map if name.lower() in lowers]
            if hits:
                return hits
        return []

class RetrieverlessQAPipeline:
    def __init__(self, llm, doc_loader: DocumentLoader, max_context_chars: int = 32000):
        self.llm = llm
        self.doc_loader = doc_loader
        self.max_context_chars = max_context_chars
        self.qa_template = PromptTemplate(
            input_variables=["story", "master", "features"],
            template=(
                "You are an Expert AI QA Agent and product SME. Your task is to analyse the user story for logical challenges, impacted areas, etc.\n\n"
                "USER STORY:\n{story}\n\n"
                "MASTER DOCUMENT (overview):\n{master}\n\n"
                "SELECTED FEATURE DOCUMENTS (detailed):\n{features}\n\n"
                "TASK:\n1) Analyse the features story and impacted modules/features .\n"
                "2) Generate all possible detailed test cases (Positive, Negative, Edge, security, etc.). Each test case must have:\n"
                "  - Reference, Type, Title, Preconditions, Steps, ExpectedResult\n\n"
                "Output ONLY a JSON array (no explanations)."
                "Return a single valid JSON array with those test cases."
            )
        )
        self.output_parser: BaseOutputParser = JsonOutputParser()

    def _join_docs_content(self, docs) -> str:
        return "\n\n".join([d.page_content for d in docs])

    async def generate(self, story: str, master_path: str, feature_paths: List[str]) -> Optional[List[Dict]]:
        master_chunks = self.doc_loader.load_any(master_path)
        master_text = self._join_docs_content(master_chunks)

        feature_texts = []
        for p in feature_paths:
            try:
                chunks = self.doc_loader.load_any(p)
                feature_texts.append(self._join_docs_content(chunks))
            except Exception as e:
                feature_texts.append(f"[Failed to load {p}: {e}]")

        combined_context = master_text + "\n\n" + "\n\n".join(feature_texts)
        combined_context = truncate_text(combined_context, self.max_context_chars)

        prompt = self.qa_template.format(
            story=truncate_text(story, 2000),
            master=truncate_text(master_text, 2000),
            features=truncate_text("\n\n".join(feature_texts), 4000)
        )

        raw = await self.llm.ainvoke(prompt)
        try:
            parsed = self.output_parser.parse(raw.content if hasattr(raw, 'content') else str(raw))
            return parsed
        except Exception:
            return None


def main():
    st.title("QA Agent - Test Case Generator")

    story = st.text_area("Enter User Story", height=300)
    approach = st.radio("Choose Approach", ("Router (No Vector DB)", "Vector DB"))

    if st.button("Generate Test Cases"):
        if not story.strip():
            st.warning("Please enter a user story.")
            return

        doc_loader = DocumentLoader()

        keyword_map = {
            "Documents": r"./Related_docs/Documents Feature.pdf",
            "Comments": r"./Related_docs/Comments Feature.pdf",
            "Request Type Form Builder": r"./Related_docs/Request Type Configurable Form.pdf",
            "Request via email": r"./Related_docs/Request_via_Email_Feature.pdf"
        }

        master_doc_path = r"./Related_docs/MR.pdf"

        async def run_pipeline():
            if approach == "Router (No Vector DB)":
                router = FeatureRouter(llm=azurellm, keyword_map=keyword_map)
                qa = RetrieverlessQAPipeline(llm=azurellm, doc_loader=doc_loader)

                selected_feature_names = await router.route(story)
                st.write("Router chose:", selected_feature_names)

                selected_paths = [keyword_map[name] for name in selected_feature_names if name in keyword_map]
                testcases = await qa.generate(story, master_doc_path, selected_paths)

                if testcases:
                    st.json(testcases)
                else:
                    st.error("Failed to generate valid JSON test cases.")

            elif approach == "Vector DB":
                st.write("### Vector DB Chunks")

                chain = build_chain(azurellm)

                context = retrieve_info(story)
                st.write("### Context", context)
                
                raw = chain.invoke({"user_story": story, "context": context})

                try:
                    output_parser = JsonOutputParser()
                    testcases = output_parser.parse(raw.content if hasattr(raw, 'content') else str(raw))
                    st.json(testcases)
                except Exception:
                    st.error("Failed to parse JSON test cases.")

        asyncio.run(run_pipeline())

if __name__ == "__main__":
    main()
