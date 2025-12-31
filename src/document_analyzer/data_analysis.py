import os
import sys
from utils.model_loader import ModelLoader
from logger import GLOBAL_LOGGER as log
from exception.custom_exception import DocumentPortalException
from model.models import *
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import OutputFixingParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from prompt.prompt_library import PROMPT_REGISTRY # type: ignore


class DocumentAnalyzer:
    """
    Analyzes documents using a pre-trained model.
    Automatically logs all actions and supports session-based organization.
    """
    def __init__(self):
        try:
            self.loader=ModelLoader()
            self.llm=self.loader.load_llm()
            
            # Prepare parsers
            self.parser = JsonOutputParser(pydantic_object=Metadata)
            self.fixing_parser = OutputFixingParser.from_llm(parser=self.parser, llm=self.llm)
            
            self.prompt = PROMPT_REGISTRY["document_analysis"]
            
            # Text splitter (CRITICAL for token safety)
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1200,
                chunk_overlap=200
            )
            log.info("DocumentAnalyzer initialized successfully")
            
            
        except Exception as e:
            log.error(f"Error initializing DocumentAnalyzer: {e}")
            raise DocumentPortalException("Error in DocumentAnalyzer initialization", sys)
        
    def _chunk_text(self, document_text: str) -> List[str]:
        """
        Split document into LLM-safe chunks
        """
        chunks = self.text_splitter.split_text(document_text)
        log.info("Document chunked", chunks=len(chunks))
        return chunks    
    
    def analyze_document(self, document_text:str)-> dict:
        """
        Analyze a document by chunking → per-chunk extraction → merge results.
        """
        try:
            chunks = self._chunk_text(document_text)
            
            chain = self.prompt | self.llm | self.fixing_parser
            
            log.info("Meta-data analysis chain initialized")
            
            responses = []

            for idx, chunk in enumerate(chunks, start=1):
                log.info("Analyzing chunk", chunk_number=idx)

                response = chain.invoke({
                    "format_instructions": self.parser.get_format_instructions(),
                    "document_text": chunk
                })

                responses.append(response)
                
            final_response = self._merge_metadata(responses)
            log.info("Metadata extraction successful", keys=list(final_response.keys()))
            
            return final_response

        except Exception as e:
            log.error("Metadata analysis failed", error=str(e))
            raise DocumentPortalException("Metadata extraction failed",sys)
        
    def _merge_metadata(self, responses: list[dict]) -> dict:
        merged: dict = {}

        for response in responses:
            for key, value in response.items():
                if value is None:
                    continue

                # First occurrence
                if key not in merged:
                    merged[key] = value
                    continue

                existing = merged[key]

                # ---- STRING ----
                if isinstance(existing, str) and isinstance(value, str):
                    if value not in existing:
                        merged[key] = existing + " | " + value

                # ---- NUMBER (int / float) ----
                elif isinstance(existing, (int, float)) and isinstance(value, (int, float)):
                    # Keep the first or max — choose one strategy
                    merged[key] = max(existing, value)

                # ---- LIST ----
                elif isinstance(existing, list):
                    if value not in existing:
                        merged[key].append(value)

                # ---- FALLBACK ----
                else:
                    merged[key] = existing

        return merged

        
    
