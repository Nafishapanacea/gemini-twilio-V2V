from pydantic import BaseModel


class QuestionAnswer(BaseModel):
    question: str
    answer: str


class InterviewResult(BaseModel):
    call_sid: str
    completed: bool
    responses: list[QuestionAnswer]