from dotenv import load_dotenv
import os
import sys
# from langchain_groq import ChatGroq
# from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

from utils.config_loader import load_config
from langchain_community.embeddings import HuggingFaceEmbeddings
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentportalException
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_groq import ChatGroq

from langchain_openai import ChatOpenAI


log = CustomLogger().get_logger(__name__)

# load_dotenv()

# embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# chat = ChatGroq(model = 'openai/gpt-oss-120b')


class ModelLoader:
    def __init__(self):
        load_dotenv()
        self._validate_env_variable_()
        self.config= load_config()
        log.info("configuration loaded successfully" , config_keys  =list(self.config.keys()))
        
    
    
    def _validate_env_variable_(self):
        
        # required_variables = ['GROQ_API_KEY' , 'GOOGLE_API_KEY']
        required_variables = ['OPENAI_API_KEY']

        self.api_keys = {key : os.getenv(key) for key in required_variables}
        missing = [k for k , v in self.api_keys.items() if not v]
        
        if missing:
            log.error("Missing environment variables", missing_vars = missing)
            
            raise DocumentportalException("Missing environment variables", sys)
        
        log.info("Environment variables validated" , available_keys = [k for k in self.api_keys if self.api_keys[k]])
    
    def load_embedding_model(self):
        try:
            log.info("logading embedding model")
            model_name = self.config['embedding_model']['model']
            
            return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")         
        
        except Exception as e:
            log.error("Error loading embedding model" , error = str(e))
            raise DocumentportalException("Failed to load embedding model" , sys)
    
    def load_llm(self):
        
        """
        Load and return the configured LLM model.
        """
        llm_block = self.config["llm"]
        provider_key = os.getenv("LLM_PROVIDER", "openai")

        if provider_key not in llm_block:
            log.error("LLM provider not found in config", provider=provider_key)
            raise ValueError(f"LLM provider '{provider_key}' not found in config")

        llm_config = llm_block[provider_key]
        provider = llm_config.get("provider")
        model_name = llm_config.get("model_name")
        temperature = llm_config.get("temperature", 0.2)
        max_tokens = llm_config.get("max_tokens", 2048)

        log.info("Loading LLM", provider=provider, model=model_name)

        if provider == "openai":
            # return ChatGoogleGenerativeAI(
            #     model=model_name,
            #     google_api_key=self.api_key_mgr.get("GOOGLE_API_KEY"),
            #     temperature=temperature,
            #     max_output_tokens=max_tokens
            # )
            
            return ChatOpenAI(
        model=model_name,
        # google_api_key=self.api_keys.get("OPENAI_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        temperature=temperature,
        max_tokens=max_tokens
    )

        # if provider == "groq":
        #     return ChatGroq(
        #         model=model_name,
        #         # api_key=self.api_key_mgr.get("GROQ_API_KEY"), #type: ignore
        #         api_key=self.api_keys.get("GROQ_API_KEY"),
        #         temperature=temperature,
        #     )

        # elif provider == "openai":
        #     return ChatOpenAI(
        #         model=model_name,
        #         api_key=self.api_key_mgr.get("OPENAI_API_KEY"),
        #         temperature=temperature,
        #         max_tokens=max_tokens
        #     )

        else:
            log.error("Unsupported LLM provider", provider=provider)
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        
        


if __name__ == '__main__':
    loader = ModelLoader()
    
    embeddings = loader.load_embedding_model()
    print(f'embedding model {embeddings}')
    
    
    llm = loader.load_llm()
    print(f'llm {llm}')
    
    
    result = llm.invoke("hello, how are you ?")
    
    print(f'result --> {result}')
    