import json

import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger


class ExtractedClaimCandidate(BaseModel):
    claim_type: str  # e.g., "offering", "hiring", "headquarters", "tech_stack", "employee_count"
    claim_value: str
    source_name: str
    approximate_quote: str | None = None


class ClaimExtractorService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY

    async def extract_candidate_claims(
        self,
        company_name: str,
        domain: str,
        source_url: str,
        source_text: str,
    ) -> list[ExtractedClaimCandidate]:
        """
        Extracts candidate claims from retrieved source text.
        If GEMINI_API_KEY is configured, uses Gemini to assist in structured claim extraction.
        Otherwise, uses deterministic heuristic/regex extraction from the text.
        IMPORTANT: All returned candidates must be verified by the Evidence Validator!
        """
        if not source_text or len(source_text.strip()) < 20:
            return []

        # If Gemini is configured, use it for assisted parsing
        if self.api_key and self.api_key.strip():
            try:
                claims = await self._extract_with_gemini(company_name, domain, source_text[:4000])
                if claims:
                    return claims
            except Exception as e:
                logger.warning(
                    f"Gemini claim extraction failed or timed out: {e}. Falling back to deterministic extractor."
                )

        # Deterministic heuristic extraction
        return self._extract_deterministically(company_name, source_text)

    async def _extract_with_gemini(
        self,
        company_name: str,
        domain: str,
        excerpt: str,
    ) -> list[ExtractedClaimCandidate]:
        prompt = f"""You are a factual claim extractor for LeadOS.
Analyze ONLY the provided raw text from {company_name} ({domain}).
Extract up to 4 factual business claims that explicitly appear in the text regarding:
- Company offering/product
- Hiring or team expansion
- Headquarters or office locations
- Technology or integrations

Rules:
1. ONLY extract statements explicitly mentioned in the text.
2. DO NOT invent facts, metrics, or revenue figures.
3. Provide the exact or near-exact quote from the text.

Respond with ONLY valid JSON array adhering to this schema:
[
  {{
    "claim_type": "offering" | "hiring" | "headquarters" | "tech_stack",
    "claim_value": "Short summary of the factual claim",
    "source_name": "Official Website",
    "approximate_quote": "Snippet from text supporting this claim"
  }}
]

Raw Text:
{excerpt}
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                url,
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "responseMimeType": "application/json",
                    },
                },
            )
            if resp.status_code != 200:
                logger.warning(f"Gemini API returned status {resp.status_code}")
                return []

            data = resp.json()
            raw_text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            parsed = json.loads(raw_text)
            candidates = []
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and "claim_type" in item and "claim_value" in item:
                        candidates.append(
                            ExtractedClaimCandidate(
                                claim_type=str(item.get("claim_type", "offering")),
                                claim_value=str(item.get("claim_value", "")),
                                source_name=str(item.get("source_name", "Official Website")),
                                approximate_quote=item.get("approximate_quote"),
                            )
                        )
            return candidates

    def _extract_deterministically(
        self, company_name: str, source_text: str
    ) -> list[ExtractedClaimCandidate]:
        """Deterministic heuristic extraction from parsed text."""
        candidates: list[ExtractedClaimCandidate] = []
        lines = [line.strip() for line in source_text.split("\n") if len(line.strip()) > 30]

        # 1. Offering / Description heuristic
        for line in lines[:5]:
            if any(
                term in line.lower()
                for term in [
                    "platform",
                    "solution",
                    "software",
                    "api",
                    "service",
                    "helps",
                    "provides",
                    "empowers",
                ]
            ):
                candidates.append(
                    ExtractedClaimCandidate(
                        claim_type="offering",
                        claim_value=line[:160],
                        source_name="Official Website",
                        approximate_quote=line[:200],
                    )
                )
                break

        # 2. Hiring / Careers heuristic
        hiring_patterns = [
            "we're hiring",
            "open positions",
            "careers",
            "join our team",
            "engineering roles",
            "hiring in",
        ]
        for line in lines:
            if any(p in line.lower() for p in hiring_patterns):
                candidates.append(
                    ExtractedClaimCandidate(
                        claim_type="hiring",
                        claim_value=f"Active hiring notice: {line[:140]}",
                        source_name="Careers / About",
                        approximate_quote=line[:200],
                    )
                )
                break

        # 3. Location heuristic
        location_patterns = [
            "headquartered in",
            "based in",
            "offices in",
            "san francisco",
            "new york",
            "london",
            "austin",
            "toronto",
            "berlin",
        ]
        for line in lines:
            if any(p in line.lower() for p in location_patterns):
                candidates.append(
                    ExtractedClaimCandidate(
                        claim_type="headquarters",
                        claim_value=line[:120],
                        source_name="About / Contact",
                        approximate_quote=line[:180],
                    )
                )
                break

        # 4. Tech / integrations
        tech_patterns = [
            "integrates with",
            "built on",
            "powered by",
            "rest api",
            "sdk",
            "python",
            "react",
            "aws",
            "cloud",
        ]
        for line in lines:
            if any(p in line.lower() for p in tech_patterns):
                candidates.append(
                    ExtractedClaimCandidate(
                        claim_type="tech_stack",
                        claim_value=line[:140],
                        source_name="Product / Tech Spec",
                        approximate_quote=line[:180],
                    )
                )
                break

        return candidates


claim_extractor = ClaimExtractorService()
