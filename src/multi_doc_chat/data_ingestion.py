import uuid 
from pathlib import Path
import sys
from langchain_community.document_loaders import PyPDFLoader , Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentportalException
from utils.model_loader import ModelLoader
from datetime import datetime,timezone

class DocumentIngestor:
    SUPPORTED_FILE_EXTENSION = {'.pdf' , '.docx' , '.txt' , '.md'}
    
    def __init__(self, temp_dir : str  = 'data/multi_doc_chat', faiss_dir : str = 'faiss_index' , session_id : str | None = None):
        try:
            self.log = CustomLogger().get_logger(__name__)
            
            self.temp_dir = Path(temp_dir)
            self.faiss_dir = Path(faiss_dir)
            
            self.temp_dir.mkdir(parents=True , exist_ok=True)
            self.faiss_dir.mkdir(parents=True , exist_ok=True)
            
            
            
            self.session_id = session_id or f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            self.session_temp_dir  = self.temp_dir  / self.session_id
            self.session_faiss_dir = self.faiss_dir / self.session_id
            
            self.session_temp_dir.mkdir(parents=True , exist_ok=True)
            self.session_faiss_dir.mkdir(parents=True , exist_ok=True)
            
            
            self.model_loader = ModelLoader()
            
            self.log.info('initialization completed successfully')
        
        
        except Exception as e:
            self.log.error('Failed to initialize DocumentIngestor' , error = str(e))
            raise DocumentportalException("Initialize error in DocumentIngestor" ,sys)
    
    
    def ingest_file(self,uploaded_files):
        
        try:
            documents = []
            
            for uploaded_file in uploaded_files:
                ext = Path(uploaded_file.name).suffix.lower()
                if ext not in self.SUPPORTED_FILE_EXTENSION:
                    self.log.warning('unsupported file skipped')
                    continue
                
                unique_filename = f'{uuid.uuid4().hex[:8]}{ext}'
                
                temp_path = self.session_temp_dir / unique_filename
                
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.read())
                
                self.log.info('file saved for ingestion')
                
                
                if ext == '.pdf':
                    loader = PyPDFLoader(str(temp_path))
                
                
                elif ext == '.docx':
                    loader = Docx2txtLoader(str(temp_path))
                    
                elif ext == '.txt':
                    loader = TextLoader(str(temp_path))
                
                else:
                    self.log.warning("unsupported file found")
                    continue
                
                docs = loader.load()
                documents.extend(docs)
                
            if not documents:
                    raise DocumentportalException("No Valid document loaded", sys)
                
            self.log.info('all documents loaded')
            return self._create_retriever(documents)
            
                
        
        except Exception as e:
            self.log.error('Failed to ingest file' , error = str(e))
            raise DocumentportalException("ingestion error in DocumentIngestor" ,e)
    
    
    def _create_retriever(self, documents):
        try:
            splitter = RecursiveCharacterTextSplitter(chunk_size = 1000 , chunk_overlap = 300)
            chunks = splitter.split_documents(documents)
            
            self.log.info('chunking of documents completed')
            
            embeddings = self.model_loader.load_embedding_model()
            
            vector_store = FAISS.from_documents(documents=chunks,embedding=embeddings)
            
            vector_store.save_local(str(self.session_faiss_dir))
            
            self.log.info('FAISS index saved to disk ')
            
            retriever = vector_store.as_retriever(search_type = 'similarity', search_kwargs = {"k" : 5})
            
            self.log.info('FAISS retreiver created and ready to use')
            
            return retriever
        
        except Exception as e:
            self.log.error('Failed to create retriever ' , error = str(e))
            raise DocumentportalException("retriever error in DocumentIngestor" ,sys)
    
    