# models.py

from typing import List, Literal
from pydantic import BaseModel
from enum import Enum


class ConversationTurn(BaseModel):
    speaker: str
    startTime: str
    endTime: str
    transcript: str
    emotion: str

class AudioAnalysis(BaseModel):
    conversation: List[ConversationTurn]



class TurnCategory(str, Enum):
    pii = "PII Stated"
    product = "Product Issues"
    complaint = "Complaint"
    churn = "Churn Indicators"
    suggestion = "Suggestion"
    none = "None"

class TurnSentiment(str, Enum):
    positive = "Positive"
    negative = "Negative"
    neutral = "Neutral"


class TurnAnalysis(BaseModel):
    category: TurnCategory
    sentiment: TurnSentiment
    translation: str

class CallAnalysis(BaseModel):
    conversation_analysis: List[TurnAnalysis]

class OverallCallAnalysisResult(BaseModel):
    summarization: str
    call_purpose: str
    topics_keywords: List[str]
    action_taken: str
    next_action: str = None
