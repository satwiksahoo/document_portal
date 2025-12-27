import sys
from pathlib import Path
import fitz
import uuid
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentportalException
# from utils.file_io import generate_session_id, save_uploaded_files
from datetime import datetime
import shutil
from typing import Iterable, List, Optional, Dict, Any
class DocumentComparator:
    
    def __init__(self , base_dir:str = 'data/document_compare' ,session_id: Optional[str] = None):
        
        self.log = CustomLogger().get_logger(__name__)
        self.base_dir = Path(base_dir)
        # self.base_dir.mkdir(parents=True , exist_ok=True)
        self.session_id = session_id or f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        self.session_path = self.base_dir / self.session_id
        self.session_path.mkdir(parents=True, exist_ok=True)
        self.log.info("DocumentComparator initialized", session_path=str(self.session_path))
        
    
    # def delete_existing_file(self):

    #     try:
    #         if self.base_dir.exists() and self.base_dir.is_dir():
    #             for file in self.base_dir.iterdir():
    #                 if file.is_file():
    #                     file.unlink()
    #                     self.log.info('File deleted', path = str(file))
                
    #             self.log.info('Directory cleaned' , directory = str(self.base_dir))
    #     except Exception as e:
    #         self.log.error(e)
    #         raise DocumentportalException('error while deleting file' , sys)
        
    
    def delete_existing_file(self):
        try:
            if self.session_path.exists():
                for file in self.session_path.iterdir():
                    if file.is_file():
                        file.unlink()
                        self.log.info("File deleted", path=str(file))
        except Exception as e:
            self.log.error(str(e))
            raise DocumentportalException("error while deleting file", e)

    
    def save_uploaded_file(self, reference_file , actual_file): 
        
        
        try:
            self.delete_existing_file()
            self.log.info('existing file deleted sucessfully')
            
            # ref_path = self.base_dir/reference_file.name
            # actual_path = self.base_dir/actual_file.name
            
            ref_path = self.session_path / reference_file.name
            actual_path = self.session_path / actual_file.name
            
            if not reference_file.name.endswith('.pdf') or not actual_file.name.endswith('.pdf'):
                raise ValueError('Only PDF files are allowed')
            
            
            with open(ref_path, 'wb') as f:
                f.write(reference_file.getbuffer())
            
            with open(actual_path, 'wb') as f:
                f.write(actual_file.getbuffer())
                
            
            self.log.info('File saved' , reference = str(ref_path) , actual = str(actual_path))
            
            return ref_path , actual_path
            
        except Exception as e:
            self.log.error(e)
            raise DocumentportalException('error while uploading file' , sys)
                
    
    
    
    
    def read_pdf(self , pdf_path : str):
        
        try:
            with fitz.open(pdf_path) as doc:
                if doc.is_encrypted:
                    raise ValueError('PDF is encrypted and cannot be read')
                all_text = []
                
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    if text.strip():
                        all_text.append(f'\n --- page {page_num + 1} --- \n{text}')
                
                self.log.info('PDF read successfully' , file= str(pdf_path) , pages = len(all_text))
                
                return '\n'.join(all_text)
        except Exception as e:
            self.log.error(e)
            raise DocumentportalException('error while reading the file ' , sys)
        
    
    def combine_documents(self)->str:
        try:
            
            content_dict = {}
            
            doc_parts = []
            
            for filename in sorted(self.session_path.iterdir()):
                
                if filename.is_file() and filename.suffix == '.pdf':
                    content_dict[filename.name] = self.read_pdf(filename)
                    
            
            
            for filename, content in content_dict.items():
                doc_parts.append(f'Document: {filename}\n{content}')
                
                
            combined_text = '\n\n'.join(doc_parts)
            
            self.log.info('Documents combined' ,count = len(doc_parts))
            
            return combined_text
            
            
            
        except Exception as e:
            self.log.error('error while combining document' , sys)
    
    
    
    def clean_old_sessions(self, keep_latest: int = 3):
        try:
            sessions = sorted([f for f in self.base_dir.iterdir() if f.is_dir()], reverse=True)
            for folder in sessions[keep_latest:]:
                shutil.rmtree(folder, ignore_errors=True)
                self.log.info("Old session folder deleted", path=str(folder))
        except Exception as e:
            self.log.error("Error cleaning old sessions", error=str(e))
            raise DocumentportalException("Error cleaning old sessions", e) from e
        