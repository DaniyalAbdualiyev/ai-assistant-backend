from fastapi import UploadFile
import PyPDF2
import docx
import io

async def process_pdf(file: UploadFile) -> str:
    try:
        # Read the uploaded file into memory
        contents = await file.read()
        pdf_file = io.BytesIO(contents)
        
        # Create PDF reader object
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract text from all pages
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")

async def process_docx(file: UploadFile) -> str:
    try:
        # Read the uploaded file into memory
        contents = await file.read()
        doc_file = io.BytesIO(contents)
        
        # Create document object
        doc = docx.Document(doc_file)
        
        # Extract text from all paragraphs
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        
        return text.strip()
    except Exception as e:
        raise Exception(f"Error processing DOCX: {str(e)}")

async def process_txt(file: UploadFile) -> str:
    try:
        # Read the uploaded file into memory
        contents = await file.read()
        return contents.decode('utf-8').strip()
    except Exception as e:
        raise Exception(f"Error processing TXT: {str(e)}")

async def process_file(file: UploadFile) -> str:
    try:
        if file.filename.endswith('.pdf'):
            return await process_pdf(file)
        elif file.filename.endswith('.docx'):
            return await process_docx(file)
        elif file.filename.endswith('.txt'):
            return await process_txt(file)
        else:
            raise ValueError("Unsupported file type. Please upload PDF, DOCX, or TXT files.")
    except Exception as e:
        raise Exception(f"Error processing file: {str(e)}") 