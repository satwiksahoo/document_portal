import uuid 
from pathlib import Path
import sys
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentportalException
from utils.model_loader import ModelLoader
from datetime import datetime
class SingleDocIngestor:

    def __init__(self,data_dir : str = 'data/single_doc_chat',faiss_dir:str = 'faiss_index'):
        try:
            self.log = CustomLogger().get_logger(__name__)
            self.data_dir= Path(data_dir)
            self.data_dir.mkdir(parents=True , exist_ok=True)
            
            self.faiss_dir = Path(faiss_dir)
            self.faiss_dir.mkdir(parents=True , exist_ok=True)
            
            self.model_loader = ModelLoader()
            self.log.info('SingleDocIngestor initialized' , temp_path = str(self.data_dir), faiss_path = str(self.faiss_dir))
        except Exception as e:
            self.log.error("failed to initialize singleDocIngestor" , error = str(e))
            raise DocumentportalException('error while initializing singleDocIngestor',sys)
        
    
        
    def ingest_files(self,uploaded_files):
        try:
            documents = []
            
            for uploaded_file in uploaded_files:
                unique_filename = f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
                temp_path = self.data_dir / unique_filename
                
                with open(temp_path , 'wb') as f_out:
                    f_out.write(uploaded_file.read())
                self.log.info('PDF saved for ingestion')
                loader = PyPDFLoader(str(temp_path))
                docs = loader.load()
                documents.extend(docs)
                self.log.info('PDF FILE LOADED')
                
                return self._create_retrieval(documents)
                
        except Exception as e:
            self.log.error("failed while ingesting file" , error = str(e))
            raise DocumentportalException('error while ingesting file',sys)
        
    
    
    def _create_retrieval(self,documents):
        try:
            splitter = RecursiveCharacterTextSplitter(chunk_size = 1000 , chunk_overlap = 300)
            chunks = splitter.split_documents(documents)
            self.log.info('document chunks created')
                # 🔍 DEBUG START (ADD THIS)
            print("\n========== DEBUG: CHUNK INSPECTION ==========")
            print("TOTAL CHUNKS:", len(chunks))

            for i, chunk in enumerate(chunks[:3]):
                print(f"\n--- CHUNK {i} PREVIEW ---")
                print(repr(chunk.page_content[:500]))
            print("========== END DEBUG ==========\n")
            # 🔍 DEBUG END

            embeddings = self.model_loader.load_embedding_model()
            vector_store = FAISS.from_documents(documents=chunks , embedding=embeddings)
            vector_store.save_local(str(self.faiss_dir))
            
            self.log.info('FAISS index created and saved')
            
            retriever = vector_store.as_retriever(search_type = 'similarity' , search_kwargs = {'k' : 5} )
            
            self.log.info('Retriever created successfully ')
            
            return retriever
            
        except Exception as e:
            self.log.error("failed while creating retrieval" , error = str(e))
            raise DocumentportalException('error while creating retrieval',sys)
        
    
    def save_uploaded_file(self, actual_file): 
        
        
        try:
            self.delete_existing_file()
            self.log.info('existing file deleted sucessfully')
            
            # ref_path = self.base_dir/reference_file.name
            # actual_path = self.base_dir/actual_file.name
            
            # ref_path = self.session_path / reference_file.name
            actual_path = self.session_path / actual_file.name
            
            if not actual_file.name.endswith('.pdf'):
                raise ValueError('Only PDF files are allowed')
            
            
            # with open(ref_path, 'wb') as f:
            #     f.write(reference_file.getbuffer())
            
            with open(actual_path, 'wb') as f:
                f.write(actual_file.getbuffer())
                
            
            self.log.info('File saved' , actual = str(actual_path))
            
            return actual_path
            
        except Exception as e:
            self.log.error(e)
            raise DocumentportalException('error while uploading file' , sys)
                
    