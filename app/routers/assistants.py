from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from typing import List
from app.database import SessionLocal
from app.models.assistant import AIAssistant
from app.schemas.assistant import AssistantCreate, AssistantResponse, AssistantQuery
from app.dependencies import get_current_user
from app.services.ai_service import AIService
from PyPDF2 import PdfReader
import io

router = APIRouter()
ai_service = AIService()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=AssistantResponse)
def create_assistant(assistant: AssistantCreate, db: Session = Depends(get_db),user=Depends(get_current_user)):
    new_assistant = AIAssistant(name=assistant.name, model=assistant.model, language=assistant.language, user_id=user.id)
    db.add(new_assistant)
    db.commit()
    db.refresh(new_assistant)
    return new_assistant

@router.get("/", response_model=List[AssistantResponse])
def get_assistants(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(AIAssistant).filter(AIAssistant.user_id == user.id).all()

@router.get("/{assistant_id}", response_model=AssistantResponse)
def get_assistant(assistant_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    assistant = db.query(AIAssistant).filter(AIAssistant.id == assistant_id, AIAssistant.user_id == user.id).first()
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return assistant

@router.put("/{assistant_id}", response_model=AssistantResponse)
def update_assistant(assistant_id: int, assistant_data: AssistantCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    assistant = db.query(AIAssistant).filter(AIAssistant.id == assistant_id, AIAssistant.user_id == user.id).first()
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")

    assistant.name = assistant_data.name
    assistant.model = assistant_data.model
    assistant.language = assistant_data.language
    db.commit()
    db.refresh(assistant)
    return assistant

@router.delete("/{assistant_id}")
def delete_assistant(assistant_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    assistant = db.query(AIAssistant).filter(AIAssistant.id == assistant_id, AIAssistant.user_id == user.id).first()
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")

    db.delete(assistant)
    db.commit()
    return {"message": "Assistant deleted successfully"}

@router.post("/{assistant_id}/chat")
async def chat_with_assistant(
    assistant_id: int,
    query: AssistantQuery,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """Chat with an AI assistant"""
    assistant = db.query(AIAssistant).filter(
        AIAssistant.id == assistant_id, 
        AIAssistant.user_id == user.id
    ).first()
    
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")

    config = {
        "language": assistant.language,
        "tone": query.tone if hasattr(query, 'tone') and query.tone else "normal",
        "business_type": "selling"
    }

    try:
        response = await ai_service.get_response(
            query.text,
            config,
            assistant_id,
            user.id
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{assistant_id}/upload-knowledge")
async def upload_knowledge(
    assistant_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """Upload knowledge base document for an assistant"""
    assistant = db.query(AIAssistant).filter(
        AIAssistant.id == assistant_id, 
        AIAssistant.user_id == user.id
    ).first()
    
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")

    try:
        # Read the PDF file
        content = await file.read()
        pdf = PdfReader(io.BytesIO(content))
        
        # Extract text from all pages
        text_content = ""
        for page in pdf.pages:
            text_content += page.extract_text()

        # Initialize knowledge base with extracted text
        ai_service.initialize_knowledge_base([text_content])
        return {"message": "Knowledge base updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))