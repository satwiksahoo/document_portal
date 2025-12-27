import sys
from dotenv import load_dotenv
import pandas as pd
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentportalException
from models.models import *
from prompt.prompt_library import PROMPT_REGISTRY
from utils.model_loader import ModelLoader
from langchain_core.output_parsers import JsonOutputParser



class DocumentComparatorLLM:
    
    def __init__(self):
        load_dotenv()
        self.log = CustomLogger().get_logger(__name__)
        self.loader = ModelLoader()
        
        self.llm = self.loader.load_llm()
        self.parser = JsonOutputParser(pydantic_object=SummaryResponse)
        # self.fixing_parser = 
        self.prompt = PROMPT_REGISTRY['document_comparison']
        
        self.chain = self.prompt | self.llm | self.parser
        
        self.log.info('Document Comparator LLM initialized')
        
        
    
    
    def compare_documents(self, combined_docs):
        
        try:
            inputs = {
                "combined_docs":combined_docs,
                "format_instruction" : self.parser.get_format_instructions()
            }
            self.log.info("started document comparison" , inputs = inputs)
            response = self.chain.invoke(inputs)
            
            self.log.info('Document comparison completed' , response = response)
            
            return self._format_response(response)
        except Exception as e:
            self.log.error(f'error in document compare {e}')
            raise DocumentportalException('an error occured in comparing document' , sys)
        
    
    
    
    def _format_response(self ,response_parsed : list[dict]) -> pd.DataFrame:
        try:
            df = pd.DataFrame(response_parsed)
            self.log.info('Response formatted into Dataframe', dataframe = df)
            
            return df
        except Exception as e:
            self.log.error(f'error in format response {e}')
            raise DocumentportalException('an error occured in format response' , sys)
    