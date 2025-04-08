import PyPDF2
import docx
import logging
from typing import Optional
import io

logger = logging.getLogger(__name__)

class FileProcessor:
    async def process_file(self, file_content: bytes, filename: str) -> str:
        """
        Process uploaded file and extract text content
        """
        try:
            if filename.endswith('.pdf'):
                return self._process_pdf(file_content)
            elif filename.endswith('.docx'):
                return self._process_docx(file_content)
            elif filename.endswith('.txt'):
                return self._process_txt(file_content)
            else:
                raise ValueError(f"Unsupported file type: {filename}")
        except Exception as e:
            logger.error(f"Error processing file {filename}: {str(e)}")
            raise

    def _process_pdf(self, content: bytes) -> str:
        """
        Extract text from PDF file
        """
        try:
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise

    def _process_docx(self, content: bytes) -> str:
        """
        Extract text from DOCX file
        """
        try:
            docx_file = io.BytesIO(content)
            doc = docx.Document(docx_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error processing DOCX: {str(e)}")
            raise

    def _process_txt(self, content: bytes) -> str:
        """
        Process plain text file
        """
        try:
            return content.decode('utf-8').strip()
        except Exception as e:
            logger.error(f"Error processing TXT: {str(e)}")
            raise

    def chunk_text(self, text: str, chunk_size: int = 1000) -> list:
        """
        Split text into chunks for processing
        """
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0

        for word in words:
            if current_size + len(word) + 1 > chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += len(word) + 1

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks 