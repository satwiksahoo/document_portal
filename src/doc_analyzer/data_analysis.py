import os
from utils.model_loader import ModelLoader
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentportalException
from datetime import datetime
from models.models import *
import sys
from langchain_core.output_parsers import JsonOutputParser

# from langchain.output_parsers.fix import OutputFixingParser


from prompt.prompt_library import PROMPT_REGISTRY
class DocumentAnalyzer:
    
    
    def __init__(self):
        self.log = CustomLogger().get_logger(__name__)
        
        try:
            self.loader = ModelLoader()
            self.llm = self.loader.load_llm()
            
            self.parser = JsonOutputParser(pydantic_object=Metadata)

         
            
            self.prompt = PROMPT_REGISTRY['document_analysis']
            
            self.log.info(f' initialized document successfully ')
            
            
            
            
            
            pass
        except Exception as e:
            self.log.error(f'error initializing document error:{e}')
            raise DocumentportalException('error in document analyzer initialization' , sys)
    
    def analyze_document(self ,document_text):
        try:
            chain = self.prompt | self.llm | self.parser
            
            self.log.info("Meta-data analysis chain initialized")

            response = chain.invoke({
                "format_instructions": self.parser.get_format_instructions(),
                "document_text": document_text
            })

            self.log.info("Metadata extraction successful", keys=list(response.keys()))
            
            return response

        except Exception as e:
            self.log.error("Metadata analysis failed", error=str(e))
            raise DocumentportalException("Metadata extraction failed",sys)
            