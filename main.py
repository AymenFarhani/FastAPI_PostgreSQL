from http.client import HTTPException
from typing import List
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.sql.annotation import Annotated

import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session

fastapi_app = FastAPI()
models.Base.metadata.create_all(bind=engine)

class BaseChoice(BaseModel):
    choice_text: str
    is_correct: bool

class QuestionBase(BaseModel):
    question_text: str
    choices: List[BaseChoice]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency =Annotated[Session, Depends(get_db)]

@fastapi_app.post("/questions")
async def create_question(question: QuestionBase, db: Session = Depends(get_db)):
    new_question = models.Questions(question_text=question.question_text)
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    for choice in question.choices:
        db_choice = models.Choices(choice_text=choice.choice_text, is_correct=choice.is_correct, question_id=new_question.id)
        db.add(db_choice)
    db.commit()

@fastapi_app.get("/questions/{question_id}")
async def get_question(question_id: int, db: Session = Depends(get_db)):
    question = db.query(models.Questions).filter(models.Questions.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@fastapi_app.get("/choices/{question_id}")
async def get_choices(question_id:int, db: Session = Depends(get_db)):
    choices = db.query(models.Choices).filter(models.Choices.question_id == question_id).all()
    if not choices:
        raise HTTPException(status_code=404, detail="No choices found")
    return choices