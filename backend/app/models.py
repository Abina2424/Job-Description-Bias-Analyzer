from pydantic import BaseModel
from typing import List, Optional, Literal


class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    requires_clarification: Optional[bool] = False


class BiasAnalysis(BaseModel):
    job_description: str
    biased_terms: List[str]
    bias_type: Literal["masculine", "feminine", "neutral"]
    bias_explanation: str
    inclusive_alternative: str
