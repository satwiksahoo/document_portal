import os
import fitz
import uuid
import sys
from datetime import datetime
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentportalException

class DocumentHandler:
    def __init__(self , data_dir = None , session_id = None):
        
        try:
        
            self.log = CustomLogger().get_logger(__name__)
            self.data_dir = os.getenv("DATA_STORAGE_PATH" ,os.path.join(os.getcwd() , 'data' , 'document_analysis'))
            
            # self.session_id = session_id or f'session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}'
            self.session_id = session_id or f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            
            self.session_path = os.path.join(self.data_dir,self.session_id)
            
            os.makedirs(self.session_path , exist_ok=True)
            
            self.log.info("PDF handler initialized" , session_id = self.session_id , session_path = self.session_path)
        except Exception as e:
            raise DocumentportalException("error initializing document error" , e) from e
        
        
    def save_pdf(self, uploaded_file) -> str:
        try:
            filename = os.path.basename(uploaded_file.name)
            if not filename.lower().endswith(".pdf"):
                raise ValueError("Invalid file type. Only PDFs are allowed.")
            save_path = os.path.join(self.session_path, filename)
            # with open(save_path, "wb") as f:
            #     if hasattr(uploaded_file, "read"):
            #         f.write(uploaded_file.read())
            #     else:
            #         f.write(uploaded_file.getbuffer())
            
            with open(save_path, "wb") as f:
                if hasattr(uploaded_file, "read"):
                    f.write(uploaded_file.read())

                elif hasattr(uploaded_file, "getbuffer"):
                    f.write(uploaded_file.getbuffer())

                elif hasattr(uploaded_file, "get_buffer"):
                    f.write(uploaded_file.get_buffer())

                elif hasattr(uploaded_file, "file_path"):
                    with open(uploaded_file.file_path, "rb") as src:
                        f.write(src.read())

                else:
                    raise TypeError(f"Unsupported file type: {type(uploaded_file)}")

            self.log.info("PDF saved successfully", file=filename, save_path=save_path, session_id=self.session_id)
            return save_path
        except Exception as e:
            # self.log.error("Failed to save PDF", error=str(e), session_id=self.session_id)
            self.log.exception("Failed to save PDF", session_id=self.session_id)

            raise DocumentportalException(f"Failed to save PDF: {str(e)}", e) from e

    def read_pdf(self, pdf_path: str) -> str:
        try:
            text_chunks = []
            with fitz.open(pdf_path) as doc:
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    text_chunks.append(f"\n--- Page {page_num + 1} ---\n{page.get_text()}")  # type: ignore
            text = "\n".join(text_chunks)
            self.log.info("PDF read successfully", pdf_path=pdf_path, session_id=self.session_id, pages=len(text_chunks))
            return text
        except Exception as e:
            self.log.error("Failed to read PDF", error=str(e), pdf_path=pdf_path, session_id=self.session_id)
            raise DocumentportalException(f"Could not process PDF: {pdf_path}", e) from e
        
    # def save_pdf(self):
        
    #     try:
    #         pass
    #     except Exception as e:
    #         raise DocumentportalException("error initializing document error" , e) from e
        
            
    
    # def read_pdf(self):
    #     try:
    #         pass
    #     except Exception as e:
    #         raise DocumentportalException("error initializing document error" , e) from e
        
        

if __name__ == '__main__':
    from pathlib import Path
    from io import BytesIO
    
    pdf_path = '/Users/satwiksahoo/Desktop/CodeBasics/LLMops/Document_portal/data/document_analysis/data_llama.pdf'
    
    class DummyFile:
        def __init__(self , file_path):
            self.name = Path(file_path).name
            self.file_path = file_path
        
        def get_buffer(self):
            return open(self.file_path , 'rb').read()
        
    dummyfile = DummyFile(pdf_path) 
    
    handler = DocumentHandler()
    


    
    try:
        
        saved_path = handler.save_pdf(dummyfile)
        content = handler.read_pdf(saved_path)
        
        print(content[:500])
        
    except Exception as e:
        print(e)
        
    
    
    
    