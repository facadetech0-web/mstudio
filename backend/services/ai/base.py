from abc import ABC, abstractmethod
from typing import Dict, Any, Type, Optional
from pydantic import BaseModel

class AIProvider(ABC):
    """Abstract interface for AI Director providers."""

    @abstractmethod
    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel],
        temperature: Optional[float] = None
    ) -> BaseModel:
        """Generates and validates structured output matching response_model."""
        pass

    @abstractmethod
    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None
    ) -> str:
        """Generates raw text response."""
        pass
