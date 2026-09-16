"""Frozen SpotifyCares vocabularies used by the agent."""

INTENTS = (
    "Playback reliability",
    "App, device, and platform behavior",
    "Content or catalog availability",
    "Playlist, library, and music organization",
    "Premium, subscription, and plan status",
    "Billing, payment, refund, and card issues",
    "Account access, identity, and security",
    "Family and student eligibility",
    "Downloads and offline listening",
    "Ads and free-tier experience",
)

STATES = (
    "SYMPTOM_REPORTED",
    "CONTEXT_COLLECTED",
    "FIRST_LINE_ACTION_PROPOSED",
    "ACTION_RESULT_REPORTED",
    "REPEATED_FAILURE_OR_BROADER_INCIDENT",
    "PRIVATE_ACCOUNT_CONTEXT_REQUIRED",
    "SPECIALIST_OR_PRODUCT_INVESTIGATION",
    "RESOLVED",
    "MONITORING",
)

ACTIONS = (
    "ASK_PLATFORM_CONTEXT",
    "ASK_SYMPTOM_EVIDENCE",
    "ASK_SCOPE_OR_ENVIRONMENT",
    "ASK_CATALOG_CONTEXT",
    "SESSION_RESET",
    "REINSTALL_OR_CLEAN_INSTALL",
    "BROWSER_REMEDIATION",
    "NETWORK_REMEDIATION",
    "PROVIDE_HELP_RESOURCE",
    "REQUEST_SECURE_ACCOUNT_DETAILS",
    "MOVE_TO_DM_OR_SECURE_CHANNEL",
    "ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE",
    "CONFIRM_AND_MONITOR",
)

REQUIREMENTS = (
    "PLATFORM_CONTEXT",
    "SYMPTOM_EVIDENCE",
    "SCOPE_OR_ENVIRONMENT",
    "CATALOG_CONTEXT",
    "SECURE_ACCOUNT_CONTEXT",
    "PRIOR_ATTEMPTS_AND_TIMING",
)

REQUIREMENT_STATUSES = ("missing", "present", "conflicting", "private", "unknown", "not_required")
ACTION_RESULTS = ("attempted", "failed", "partially_helped", "improved", "resolved", "unknown")
EXPLICITNESS = ("explicit", "inferred", "ambiguous")
RECONSTRUCTION_STATUSES = ("complete", "partial", "uncertain")
EVIDENCE_STRENGTHS = ("strong", "moderate", "weak", "conflicting", "insufficient")


def require(value: str | None, allowed: tuple[str, ...], field: str) -> str:
    if value is None or value not in allowed:
        raise ValueError(f"{field} must use the frozen vocabulary")
    return value
