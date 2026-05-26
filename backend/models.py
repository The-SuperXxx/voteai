"""数据模型定义"""
from pydantic import BaseModel
from typing import Optional


class AskRequest(BaseModel):
    question: str


class ModelAnswer(BaseModel):
    model: str
    answer: str
    avg_score: float


class VoteEntry(BaseModel):
    voter: str
    scores: dict[str, int]  # {"DeepSeek-R1": 8, "Qwen3-8B": 9, ...}


class AskResponse(BaseModel):
    id: str
    question: str
    best_answer: str
    best_model: str
    score: float
    votes: list[VoteEntry]
    all_answers: list[ModelAnswer]
