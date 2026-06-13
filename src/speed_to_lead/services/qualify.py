"""Lead qualification.

`RuleQualifier` is the zero-dependency default (and a strong baseline). The
fine-tuned LoRA classifier in `speed_to_lead.ml` implements the same
`Qualifier` protocol and is dropped in when its adapter is present — so the
graph never knows or cares which one is running.
"""

from __future__ import annotations

import re
from typing import Protocol, runtime_checkable

from ..models import EnrichmentResult, FitTier, Lead, QualificationResult
from ..normalize import is_business_domain

# intent label -> trigger keywords (longest/most-specific win)
_INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "purchase_intent": ("buy", "purchase", "order", "sign up", "get started", "ready to"),
    "pricing": ("price", "pricing", "quote", "cost", "how much", "budget", "plan"),
    "demo_request": ("demo", "trial", "walkthrough", "see it", "book a call", "meeting"),
    "support": ("help", "issue", "problem", "bug", "support", "not working"),
    "partnership": ("partner", "partnership", "collaborat", "integrat", "reseller"),
    "job_inquiry": ("job", "resume", "cv", "hiring", "position", "career", "internship"),
}

# crude but effective spam signals
_SPAM_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bseo\s+services?\b",
        r"\bguest\s+post\b",
        r"\bbacklinks?\b",
        r"\bcrypto|forex|casino\b",
        r"\bincrease your (traffic|sales|ranking)\b",
        r"https?://\S+\b.*https?://\S+",  # multiple links
    )
)

_HIGH_INTENT = frozenset({"purchase_intent", "pricing", "demo_request"})


@runtime_checkable
class Qualifier(Protocol):
    """Anything that turns a lead + enrichment into a qualification."""

    name: str

    def qualify(self, lead: Lead, enrichment: EnrichmentResult) -> QualificationResult: ...


def detect_intent(message: str | None) -> str:
    if not message:
        return "general_inquiry"
    text = message.lower()
    for intent, keywords in _INTENT_KEYWORDS.items():
        if any(k in text for k in keywords):
            return intent
    return "general_inquiry"


def looks_like_spam(message: str | None) -> bool:
    if not message:
        return False
    return any(p.search(message) for p in _SPAM_PATTERNS)


class RuleQualifier:
    """Transparent, deterministic baseline qualifier.

    Scores ICP fit from explainable signals and classifies buyer intent from
    the message. Every decision ships with `reasons` so a human can audit it.
    """

    name = "rules"

    def qualify(self, lead: Lead, enrichment: EnrichmentResult) -> QualificationResult:
        intent = detect_intent(lead.message)
        reasons: list[str] = []

        if intent == "job_inquiry" or looks_like_spam(lead.message):
            return QualificationResult(
                tier=FitTier.SPAM,
                score=0.05,
                confidence=0.9,
                intent="spam" if looks_like_spam(lead.message) else intent,
                reasons=["matched spam/non-buyer pattern"],
                model=self.name,
            )

        score = 0.3  # neutral prior
        business = bool(lead.domain and is_business_domain(lead.domain))
        if business:
            score += 0.25
            reasons.append("business email domain")
        else:
            reasons.append("free email domain")

        if lead.company:
            score += 0.1
            reasons.append("company provided")
        if enrichment.employee_range or enrichment.industry:
            score += 0.1
            reasons.append("enrichment matched company")

        if intent in _HIGH_INTENT:
            score += 0.25
            reasons.append(f"high-intent message: {intent}")
        elif intent != "general_inquiry":
            score += 0.05
            reasons.append(f"intent: {intent}")

        score = min(score, 1.0)
        tier = FitTier.HOT if score >= 0.7 else FitTier.WARM if score >= 0.45 else FitTier.COLD
        # Confidence: strong when signals agree (business+high-intent or neither).
        confidence = 0.6 + 0.3 * (1 if business and intent in _HIGH_INTENT else 0)

        return QualificationResult(
            tier=tier,
            score=round(score, 3),
            confidence=round(confidence, 3),
            intent=intent,
            reasons=reasons,
            model=self.name,
        )


def get_qualifier() -> Qualifier:
    """Return the LoRA classifier if its adapter exists, else the rule baseline."""
    try:
        from ..ml.classifier import load_classifier

        clf = load_classifier()
        if clf is not None:
            return clf
    except Exception:  # ML extra not installed / no adapter — fine, use rules.
        pass
    return RuleQualifier()
