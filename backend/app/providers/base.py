from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class RawSearchCandidate(BaseModel):
    title: str
    url: str
    snippet: str
    source_name: str = "Web Search"
    domain: str | None = None
    extracted_metadata: dict[str, Any] = {}


class ProviderHealthStatus(BaseModel):
    provider_name: str
    is_available: bool
    requires_key: bool
    is_key_configured: bool
    message: str


class BaseSearchProvider(ABC):
    @abstractmethod
    async def search(
        self,
        query: str,
        industry: str | None = None,
        geography: str | None = None,
        employee_range: str | None = None,
        buying_signal: str | None = None,
        limit: int = 10,
    ) -> list[RawSearchCandidate]:
        """Executes search and returns normalized candidates."""

    @abstractmethod
    def get_health(self) -> ProviderHealthStatus:
        """Returns the operational status and requirements of the provider."""
