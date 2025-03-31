from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.models.assistant import AIAssistant
from app.schemas.assistant import AssistantCreate, AssistantResponse
from app.dependencies import get_current_user, get_db

router = APIRouter()

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