"""Pydantic schemas package."""
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserLogin, Token, TokenData
)
from app.schemas.book import (
    BookCreate, BookUpdate, BookResponse, BookSummaryResponse
)
from app.schemas.review import (
    ReviewCreate, ReviewUpdate, ReviewResponse, ReviewSummaryResponse
)
from app.schemas.document import (
    DocumentCreate, DocumentResponse, DocumentUpload
)
from app.schemas.qa import QuestionRequest, QuestionResponse

__all__ = [
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin", "Token", "TokenData",
    "BookCreate", "BookUpdate", "BookResponse", "BookSummaryResponse",
    "ReviewCreate", "ReviewUpdate", "ReviewResponse", "ReviewSummaryResponse",
    "DocumentCreate", "DocumentResponse", "DocumentUpload",
    "QuestionRequest", "QuestionResponse"
]
