import re

from app.schemas.evidence import VerificationStatus


def normalize_text_for_matching(text: str) -> str:
    """Removes excess whitespace and lowercases text for matching."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.lower().strip())


def extract_key_numbers(claim: str) -> list[str]:
    """Finds numbers, dollar amounts, and percentages in a claim."""
    return re.findall(r"\$?\d+(?:,\d+)*(?:\.\d+)?%?", claim)


def extract_salient_tokens(claim: str) -> list[str]:
    """Extracts informative keywords from claim, skipping trivial stop words."""
    stop_words = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "and",
        "or",
        "in",
        "on",
        "at",
        "to",
        "for",
        "with",
        "by",
        "of",
        "from",
        "that",
        "this",
        "it",
        "as",
        "be",
        "has",
        "have",
        "had",
        "its",
        "their",
        "our",
        "we",
        "company",
        "provides",
    }
    tokens = re.findall(r"\b[a-z0-9\-\$]{3,}\b", claim.lower())
    return [t for t in tokens if t not in stop_words]


def is_word_match(token: str, text: str) -> bool:
    """Checks if a token or numeric term appears as an isolated word/token in text,
    preventing partial substring matches (e.g. 'cat' in 'education' or '50' in '500')."""
    if not token or not text:
        return False
    pattern = rf"(?<!\w){re.escape(token.lower())}(?!\w)"
    return bool(re.search(pattern, text.lower()))


def validate_claim_against_source(
    claim_value: str,
    claim_type: str,
    source_text: str | None,
) -> tuple[VerificationStatus, str | None, str]:
    """
    Validates a claim against retrieved source text.
    Returns: (verification_status, best_supporting_excerpt, validation_notes)
    """
    if not source_text or len(source_text.strip()) < 10:
        return (
            "unknown",
            None,
            "Source text could not be retrieved, was empty, or failed network security checks.",
        )

    norm_claim = normalize_text_for_matching(claim_value)
    norm_source = normalize_text_for_matching(source_text)

    # 1. Direct exact or full phrase match with word boundaries
    direct_match = re.search(rf"(?<!\w){re.escape(norm_claim)}(?!\w)", norm_source)
    if direct_match:
        start = max(0, direct_match.start() - 60)
        end = min(len(source_text), direct_match.end() + 60)
        excerpt = source_text[start:end].strip()
        return (
            "verified",
            excerpt,
            f"Direct factual match found in source text for {claim_type} claim.",
        )

    # 2. Check key numbers and metrics
    numbers = extract_key_numbers(claim_value)
    salient_tokens = extract_salient_tokens(claim_value)

    if not salient_tokens:
        return (
            "unverified",
            None,
            "Claim does not contain sufficient salient keywords for verification.",
        )

    # Count how many salient tokens appear in source using word-boundary matching
    matched_tokens = [t for t in salient_tokens if is_word_match(t, norm_source)]
    token_ratio = len(matched_tokens) / len(salient_tokens) if salient_tokens else 0.0

    # If numbers were part of the claim (e.g. "$15M", "50-100", "2024"), they MUST be present
    if numbers:
        matched_numbers = [n for n in numbers if is_word_match(n, norm_source)]
        if not matched_numbers:
            return (
                "unverified",
                None,
                f"Numeric claim elements {numbers} were not found in source text.",
            )

    # 3. Locate best paragraph / window containing the highest density of matched tokens
    paragraphs = [p.strip() for p in source_text.split("\n") if len(p.strip()) > 20]
    best_para = ""
    best_score = 0

    for p in paragraphs:
        p_lower = p.lower()
        score = sum(1 for t in matched_tokens if is_word_match(t, p_lower))
        if numbers:
            score += sum(2 for n in numbers if is_word_match(n, p_lower))
        if score > best_score:
            best_score = score
            best_para = p

    # Determine status
    if token_ratio >= 0.75 and (
        not numbers or any(is_word_match(n, best_para) for n in numbers)
    ):
        excerpt = best_para[:350]
        return (
            "verified",
            excerpt,
            f"Verified: {len(matched_tokens)}/{len(salient_tokens)} salient terms and required metrics substantiated in source excerpt.",
        )
    elif token_ratio >= 0.4:
        excerpt = best_para[:350] if best_para else None
        return (
            "partially_verified",
            excerpt,
            f"Partially verified: {len(matched_tokens)}/{len(salient_tokens)} salient terms detected, but full context is incomplete.",
        )
    else:
        return (
            "unverified",
            None,
            f"Unverified: Only {len(matched_tokens)}/{len(salient_tokens)} terms matched in source. Evidence insufficient.",
        )
