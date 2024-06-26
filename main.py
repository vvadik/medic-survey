from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
import random
import string

from starlette.staticfiles import StaticFiles

DATABASE_URL = "sqlite:///./test.db"
Base = declarative_base()

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    current_question_id = Column(Integer)
    state = Column(String)


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    text = Column(String)
    next_question_id = Column(Integer, nullable=True)

    question = relationship("Question", back_populates="answers")


Question.answers = relationship("Answer", order_by=Answer.id, back_populates="question")

Base.metadata.create_all(bind=engine)


class StartTestResponse(BaseModel):
    user_id: str


class NextQuestionResponse(BaseModel):
    question_id: int
    text: str
    answers: list


class AnswerRequest(BaseModel):
    user_id: str
    question_id: int
    answer_id: int


class AnswerResponse(BaseModel):
    question_id: int = None
    text: str = None
    answers: list = None
    result: str = None


class StateResponse(BaseModel):
    user_id: str
    current_question_id: int
    state: str


def generate_user_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))


@app.post("/start_test", response_model=StartTestResponse)
def start_test():
    user_id = generate_user_id()
    db = SessionLocal()
    user = User(id=user_id, current_question_id=1, state="In progress")
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return {"user_id": user_id}


@app.get("/next_question/{user_id}", response_model=NextQuestionResponse)
def next_question(user_id: str):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    question = db.query(Question).filter(Question.id == user.current_question_id).first()
    if not question:
        db.close()
        raise HTTPException(status_code=404, detail="Question not found")

    answers = db.query(Answer).filter(Answer.question_id == question.id).all()
    answer_list = [{"id": answer.id, "text": answer.text} for answer in answers]

    db.close()
    return {"question_id": question.id, "text": question.text, "answers": answer_list}


@app.post("/answer", response_model=AnswerResponse)
def answer_question(answer_request: AnswerRequest):
    db = SessionLocal()
    user = db.query(User).filter(User.id == answer_request.user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    answer = db.query(Answer).filter(
        Answer.id == answer_request.answer_id,
        Answer.question_id == answer_request.question_id
    ).first()

    if not answer:
        db.close()
        raise HTTPException(status_code=404, detail="Answer not found")

    if answer.next_question_id:
        user.current_question_id = answer.next_question_id
        db.commit()
        next_question = db.query(Question).filter(Question.id == answer.next_question_id).first()
        answers = db.query(Answer).filter(Answer.question_id == next_question.id).all()
        answer_list = [{"id": answer.id, "text": answer.text} for answer in answers]
        db.close()
        return {"question_id": next_question.id, "text": next_question.text, "answers": answer_list}
    else:
        user.state = "Completed"
        db.commit()
        db.close()
        return {"result": "You are a creative person!"}


@app.get("/state/{user_id}", response_model=StateResponse)
def get_state(user_id: str):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    db.close()
    return {"user_id": user.id, "current_question_id": user.current_question_id, "state": user.state}


@app.get("/")
def read_root():
    return FileResponse('static/index.html')


# Run the FastAPI application using uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
