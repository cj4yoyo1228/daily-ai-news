from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RawArticle(BaseModel):
    title: str
    url: str
    source: str
    published_at: datetime
    content_snippet: str
    similar_sources: list[str] = []


class EvaluationResult(BaseModel):
    reasoning: str
    impact_score: int
    specificity_score: int
    novelty_score: int
    total_score: int
    is_qualified: bool
    executive_summary: Optional[str] = None


class ScoredArticle(BaseModel):
    article: RawArticle
    evaluation: EvaluationResult
