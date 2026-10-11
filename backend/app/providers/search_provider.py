import asyncio

import httpx
from ddgs import DDGS

from app.core.config import settings
from app.core.logging import logger
from app.providers.base import BaseSearchProvider, ProviderHealthStatus, RawSearchCandidate
from app.validators.url_normalizer import normalize_domain


class DuckDuckGoSearchProvider(BaseSearchProvider):
    def __init__(self):
        self.name = "DuckDuckGo (DDGS)"

    def get_health(self) -> ProviderHealthStatus:
        return ProviderHealthStatus(
            provider_name=self.name,
            is_available=True,
            requires_key=False,
            is_key_configured=True,
            message="Active real-time web discovery provider via DuckDuckGo.",
        )

    async def search(
        self,
        query: str,
        industry: str | None = None,
        geography: str | None = None,
        employee_range: str | None = None,
        buying_signal: str | None = None,
        limit: int = 10,
    ) -> list[RawSearchCandidate]:
        # Formulate a structured search query incorporating user filters
        query_parts = [query]
        if industry:
            query_parts.append(f'"{industry}"')
        if geography:
            query_parts.append(f'"{geography}"')
        if employee_range:
            query_parts.append(f'"{employee_range} employees"')
        if buying_signal:
            query_parts.append(buying_signal)

        # Append company discovery intent terms
        query_parts.append("company official website OR about OR careers")
        search_query = " ".join(query_parts)

        candidates: list[RawSearchCandidate] = []

        def _run_search():
            dd = DDGS(timeout=10)
            # Retrieve slightly more results to account for filtering and normalization
            results = list(dd.text(search_query, max_results=min(limit * 2, 30)))
            return results

        try:
            raw_results = await asyncio.to_thread(_run_search)
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e!s}")
            raise RuntimeError(f"Live web search provider failed: {e!s}")

        seen_domains = set()
        for r in raw_results:
            url = r.get("href") or ""
            title = r.get("title") or ""
            snippet = r.get("body") or ""

            if not url or not title:
                continue

            domain = normalize_domain(url)
            # Skip aggregator domains that aren't individual companies
            blacklisted_aggregators = {
                "linkedin.com",
                "wikipedia.org",
                "bloomberg.com",
                "forbes.com",
                "crunchbase.com",
                "twitter.com",
                "x.com",
                "facebook.com",
                "youtube.com",
                "glassdoor.com",
                "g2.com",
                "capterra.com",
                "reddit.com",
                "medium.com",
                "github.com",
            }
            if not domain or domain in blacklisted_aggregators or domain in seen_domains:
                continue

            seen_domains.add(domain)
            candidates.append(
                RawSearchCandidate(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source_name="DuckDuckGo Search",
                    domain=domain,
                    extracted_metadata={
                        "raw_query": search_query,
                    },
                )
            )

            if len(candidates) >= limit:
                break

        return candidates


class BraveSearchProvider(BaseSearchProvider):
    def __init__(self):
        self.api_key = settings.BRAVE_SEARCH_API_KEY
        self.name = "Brave Search API"

    def get_health(self) -> ProviderHealthStatus:
        is_configured = bool(self.api_key and self.api_key.strip())
        return ProviderHealthStatus(
            provider_name=self.name,
            is_available=is_configured,
            requires_key=True,
            is_key_configured=is_configured,
            message="Configured"
            if is_configured
            else "Brave Search API key not configured in BRAVE_SEARCH_API_KEY.",
        )

    async def search(
        self,
        query: str,
        industry: str | None = None,
        geography: str | None = None,
        employee_range: str | None = None,
        buying_signal: str | None = None,
        limit: int = 10,
    ) -> list[RawSearchCandidate]:
        if not self.api_key:
            raise ValueError(
                "Brave Search provider requires BRAVE_SEARCH_API_KEY to be set in backend configuration."
            )

        query_parts = [query]
        if industry:
            query_parts.append(industry)
        if geography:
            query_parts.append(geography)
        if buying_signal:
            query_parts.append(buying_signal)

        full_query = " ".join(query_parts)

        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {
                "X-Subscription-Token": self.api_key,
                "Accept": "application/json",
            }
            resp = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": full_query, "count": limit},
                headers=headers,
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Brave Search API error {resp.status_code}: {resp.text}")

            data = resp.json()
            web_results = data.get("web", {}).get("results", [])
            candidates: list[RawSearchCandidate] = []
            for r in web_results:
                url = r.get("url")
                candidates.append(
                    RawSearchCandidate(
                        title=r.get("title", ""),
                        url=url,
                        snippet=r.get("description", ""),
                        source_name="Brave Search",
                        domain=normalize_domain(url),
                    )
                )
            return candidates


def get_search_provider(name: str | None = None) -> BaseSearchProvider:
    provider_name = (name or settings.SEARCH_PROVIDER).lower()
    if provider_name == "brave":
        return BraveSearchProvider()
    return DuckDuckGoSearchProvider()
