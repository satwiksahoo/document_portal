import sys
import os
from operator import itemgetter
from typing import List, Optional, Dict, Any
from logger.custom_logger import CustomLogger
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_core.runnables.history import RunnableWithMessageHistory
# from langchain.chains import create_history_aware_retriever , create_retrieval_chain
# from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from typing import Dict
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain


from langchain_core.prompts import ChatPromptTemplate
from utils.model_loader import ModelLoader
from exception.custom_exception import DocumentportalException
# from logger import GLOBAL_LOGGER as log
from prompt.prompt_library import PROMPT_REGISTRY
from models.models import PromptType
from exception.custom_exception import DocumentportalException
class ConversationalRAG:
    
    def __init__(self ,session_id : str , retriever = None):
        
        try:
        
            self.log = CustomLogger().get_logger(__name__)
            self.session_id = session_id
            self.llm = self._load_llm()
            
            self.contextualize_prompt: ChatPromptTemplate = PROMPT_REGISTRY[PromptType.CONTEXTUALIZE_QUESTION.value]
            self.qa_prompt : ChatPromptTemplate = PROMPT_REGISTRY[PromptType.CONTEXT_QA.value]
            if retriever is None:
                raise ValueError('retriever cannot ne None')
            
            self.retriever = retriever
            
            self._build_lcel_chain()
            self.log.info("conversational RAG initialized")
            
            
            
        
        except Exception as e:
            self.log.error('error in intializing')
            raise DocumentportalException('error in initializing')
        
        
    
    
    def load_retriever_from_faiss(self, index_path : str):
        try:
            
            embeddings = ModelLoader().load_embedding_model()
            
            if not os.path.isdir(index_path):
                raise FileNotFoundError(f"FAISS index directort not found{index_path}")
            
            vector_store = FAISS.load_local(index_path, embeddings,allow_dangerous_deserialization= True)
            
            self.retriever= vector_store.as_retriever(search_type = 'similarity' , search_kwargs= {"k": 5})
            
            self.log.info('FAISS retreiver loaded successfully')
            # self._build_lcel_chain()
            return self.retriever 
        except Exception as e:
            self.log.error('error while loading retriever from faiss')
            raise DocumentportalException("Initializing error in Conversational RAG")
        
    # def invoke(self):
    #     pass
    
    def invoke(self , user_input:str ,chat_history : Optional[List[BaseMessage]] = None)->str:
        
        
        try:
            chat_history = chat_history or []
            payload = {"input" : user_input , "chat_history" : chat_history}
            answer = self.chain.invoke(payload)
            
            if not answer :
                self.log.warning('no answer generated')
                return 'no answer'
            
            self.log.info('answer generated successfully')
            
            return answer
        
        
            
            
        except Exception as e:
            self.log.error("failed to initialize invoke" , error = str(e))
            raise DocumentportalException('error while initializing invoke',sys)
    
    # def _load_llm(self):
    #     pass
    
    def _load_llm(self):
        
        try:
            llm = ModelLoader().load_llm()
            self.log.info('LLM loaded successfully')
            
            return llm
        except Exception as e:
            self.log.error("failed to initialize _load_llm" , error = str(e))
            raise DocumentportalException('error while initializing _load_llm',sys)
    
    @staticmethod
    def format_document(docs):
        return "\n\n".join(d.page_content for d in docs)
    
    def _build_lcel_chain(self):
        try:
            question_rewriter = (
                {"input" : itemgetter("input") , "chat_history" : itemgetter('chat_history')}
                | self.contextualize_prompt
                |self.llm
                |StrOutputParser()
                
            )
            retrieve_docs = question_rewriter | self.retriever | self.format_document
            self.chain = (
            {
                "context" : retrieve_docs ,
                "input"  : itemgetter('input'),
                "chat_history" : itemgetter("chat_history")
                }
                | self.qa_prompt
                |self.llm
                |StrOutputParser()
            )
            self.log.info('LCEL chain created sucessfully')
        except Exception as e:
            self.log.error("failed to  " , error = str(e))
            raise DocumentportalException('error while initializing _load_llm',sys)
            