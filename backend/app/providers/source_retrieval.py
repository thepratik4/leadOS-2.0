import asyncio
from datetime import UTC, datetime

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.logging import logger
from app.validators.ssrf_validator import validate_url_safe_for_retrieval


class RetrievedSourceContent:
    def __init__(
        self,
        final_url: str,
        status_code: int,
        title: str | None,
        text_content: str,
        retrieval_timestamp: datetime,
        headers: dict,
        error_reason: str | None = None,
    ):
        self.final_url = final_url
        self.status_code = status_code
        self.title = title
        self.text_content = text_content
        self.retrieval_timestamp = retrieval_timestamp
        self.headers = headers
        self.error_reason = error_reason

    @property
    def is_successful(self) -> bool:
        return self.status_code == 200 and not self.error_reason and len(self.text_content) > 0


class SourceRetrievalService:
    def __init__(self):
        self.timeout = settings.SOURCE_FETCH_TIMEOUT_SECONDS
        self.max_bytes = settings.MAX_SOURCE_BYTES
        self.user_agent = settings.USER_AGENT
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_FETCHES)

    async def fetch_source_content(self, url: str) -> RetrievedSourceContent:
        """
        Safely retrieves and cleans public website content with SSRF checks,
        streamed byte limits, and redirect revalidation.
        """
        now = datetime.now(UTC)

        # 1. Initial SSRF pre-check
        is_safe, reason = validate_url_safe_for_retrieval(url)
        if not is_safe:
            logger.warning(f"SSRF check rejected URL {url}: {reason}")
            return RetrievedSourceContent(
                final_url=url,
                status_code=400,
                title=None,
                text_content="",
                retrieval_timestamp=now,
                headers={},
                error_reason=f"Security check failed: {reason}",
            )

        async with self.semaphore:
            current_url = url
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }

            try:
                # We manage redirects manually up to 3 hops to validate SSRF at each hop
                max_redirects = 3
                redirect_count = 0

                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(self.timeout, connect=4.0),
                    verify=True,
                    follow_redirects=False,
                ) as client:
                    while redirect_count <= max_redirects:
                        # Re-validate destination URL
                        safe_hop, hop_reason = validate_url_safe_for_retrieval(current_url)
                        if not safe_hop:
                            return RetrievedSourceContent(
                                final_url=current_url,
                                status_code=400,
                                title=None,
                                text_content="",
                                retrieval_timestamp=now,
                                headers={},
                                error_reason=f"Redirect rejected by SSRF guard: {hop_reason}",
                            )

                        async with client.stream("GET", current_url, headers=headers) as response:
                            # Handle redirect
                            if response.is_redirect and "location" in response.headers:
                                redirect_count += 1
                                if redirect_count > max_redirects:
                                    return RetrievedSourceContent(
                                        final_url=current_url,
                                        status_code=response.status_code,
                                        title=None,
                                        text_content="",
                                        retrieval_timestamp=now,
                                        headers={},
                                        error_reason="Exceeded maximum allowed redirects (3).",
                                    )
                                # Resolve relative redirects
                                current_url = str(response.url.join(response.headers["location"]))
                                continue

                            # Terminal response reached
                            if response.status_code != 200:
                                return RetrievedSourceContent(
                                    final_url=str(response.url),
                                    status_code=response.status_code,
                                    title=None,
                                    text_content="",
                                    retrieval_timestamp=now,
                                    headers=dict(response.headers),
                                    error_reason=f"HTTP server responded with status code {response.status_code}",
                                )

                            # Validate content type
                            content_type = response.headers.get("content-type", "").lower()
                            if "html" not in content_type and "text" not in content_type:
                                return RetrievedSourceContent(
                                    final_url=str(response.url),
                                    status_code=response.status_code,
                                    title=None,
                                    text_content="",
                                    retrieval_timestamp=now,
                                    headers=dict(response.headers),
                                    error_reason=f"Non-HTML Content-Type '{content_type}' is not readable as textual evidence.",
                                )

                            # Stream response body bounded to max_bytes so oversized responses do not load fully into memory
                            chunks = []
                            total_bytes = 0
                            async for chunk in response.aiter_bytes():
                                chunks.append(chunk)
                                total_bytes += len(chunk)
                                if total_bytes >= self.max_bytes:
                                    break

                            raw_bytes = b"".join(chunks)[: self.max_bytes]

                        # Parse HTML
                        try:
                            soup = BeautifulSoup(raw_bytes, "html.parser")
                            # Strip scripts, styles, noscript, svg, navigation
                            for tag in soup(
                                ["script", "style", "noscript", "svg", "nav", "footer"]
                            ):
                                tag.decompose()

                            title = (
                                soup.title.string.strip()
                                if soup.title and soup.title.string
                                else None
                            )

                            # Extract paragraphs and headings
                            text_blocks = []
                            for elem in soup.find_all(["h1", "h2", "h3", "p", "li"]):
                                t = elem.get_text(separator=" ", strip=True)
                                if len(t) > 15:
                                    text_blocks.append(t)

                            cleaned_text = "\n".join(text_blocks)
                            if not cleaned_text:
                                cleaned_text = soup.get_text(separator=" ", strip=True)

                            return RetrievedSourceContent(
                                final_url=str(response.url),
                                status_code=200,
                                title=title,
                                text_content=cleaned_text[:50000],  # Bound text content
                                retrieval_timestamp=now,
                                headers=dict(response.headers),
                                error_reason=None,
                            )
                        except Exception as parse_err:
                            return RetrievedSourceContent(
                                final_url=str(response.url),
                                status_code=200,
                                title=None,
                                text_content="",
                                retrieval_timestamp=now,
                                headers=dict(response.headers),
                                error_reason=f"HTML parsing failed: {parse_err!s}",
                            )

            except httpx.TimeoutException:
                return RetrievedSourceContent(
                    final_url=current_url,
                    status_code=504,
                    title=None,
                    text_content="",
                    retrieval_timestamp=now,
                    headers={},
                    error_reason=f"Connection or read timed out after {self.timeout}s.",
                )
            except httpx.RequestError as req_err:
                return RetrievedSourceContent(
                    final_url=current_url,
                    status_code=502,
                    title=None,
                    text_content="",
                    retrieval_timestamp=now,
                    headers={},
                    error_reason=f"Network request error: {req_err!s}",
                )


source_retriever = SourceRetrievalService()
