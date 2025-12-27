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

    def __init__(self,session_id :str , retriever):
        
        try:
            self.log = CustomLogger().get_logger(__name__)
            self.session_id = session_id
            self.retriever = retriever
            self.llm  = self._load_llm()
            self.contextualise_prompt = PROMPT_REGISTRY[PromptType.CONTEXTUALIZE_QUESTION]
            self.qa_prompt = PROMPT_REGISTRY[PromptType.CONTEXT_QA.value]
            # self.history_aware_retriever = create_history_aware_retriever(self.llm , self,retriever,self.contextualise_prompt)
            self.history_aware_retriever = create_history_aware_retriever(
                            self.llm,
                            self.retriever,
                            self.contextualise_prompt
                        )

            self.log.info('created history aware retriever')
            self.qa_chain = create_stuff_documents_chain(self.llm, self.qa_prompt)
#             self.qa_chain = create_stuff_documents_chain(
#     self.llm,
#     self.qa_prompt,
#     document_variable_name="context"
# )

            self.rag_chain = create_retrieval_chain(self.history_aware_retriever , self.qa_chain)
            self.log.info('initialized RAG chain')
            
            self.chain = RunnableWithMessageHistory(
                self.rag_chain,
                self._get_session_history,
                input_messages_key = 'input',
                history_messages_key = 'chat_history',
                output_messages_key = 'answer'
                
            )
            self.log.info('created RunnableWithMessageHistory')
        except Exception as e:
            self.log.error("failed to initialize ConversationalRAG" , error = str(e) , session_id = session_id)
            raise DocumentportalException('error while initializing ConversationalRAG',sys)


    def _load_llm(self):
        
        try:
            llm = ModelLoader().load_llm()
            self.log.info('LLM loaded successfully')
            
            return llm
        except Exception as e:
            self.log.error("failed to initialize _load_llm" , error = str(e))
            raise DocumentportalException('error while initializing _load_llm',sys)
        
    _SESSION_STORE: Dict[str, ChatMessageHistory] = {}

    def _get_session_history(self ,session_id: str) -> ChatMessageHistory:
        
        try:
            if session_id not in self._SESSION_STORE:
                self._SESSION_STORE[session_id] = ChatMessageHistory()
            return self._SESSION_STORE[session_id]
        except Exception as e:
            self.log.error("failed to initialize _create_session_history" , error = str(e))
            raise DocumentportalException('error while initializing _create_session_history',sys)
    
    
    
    def load_retriever_from_faiss(self, index_path:str):
        
        try:
            embeddings = ModelLoader().load_embedding_model()
            if not os.path.isdir(index_path):
                    raise FileNotFoundError('FAISS index directory not found')
            
            vectorstore = FAISS.load_local(index_path , embeddings=embeddings)
            self.log.info("Loaded retriever from FAISS index")
            
            return vectorstore.as_retriever(search_type = 'similarity' , search_kwargs = {'k' : 5})
        except Exception as e:
            
            self.log.error("failed to initialize load_retriever_from_faiss" , error = str(e))
            raise DocumentportalException('error while initializing load_retriever_from_faiss',sys)
        
    
    def invoke(self , user_input:str)->str:
        
        
        try:
            response = self.chain.invoke(
                {"input" : user_input}, 
                config = {'configurable' :{'session_id' : self.session_id}}
            )
            
            answer = response.get('answer' , 'No answer')
            
            if not answer:
                self.log.warning('Empty answer recieved')
            
            self.log.info('chain invoked successfully')
            
            
            return answer
            
            
        except Exception as e:
            self.log.error("failed to initialize invoke" , error = str(e))
            raise DocumentportalException('error while initializing invoke',sys)
        
        