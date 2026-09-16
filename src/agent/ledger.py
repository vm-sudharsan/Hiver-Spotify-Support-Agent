"""Action-history extraction and protection against repeating failed advice."""
from __future__ import annotations

from dataclasses import dataclass
import re
from collections.abc import Iterable, Sequence

from .models import AttemptedAction, Message
from .taxonomy import ACTIONS, ACTION_RESULTS, EXPLICITNESS


_ACTION_PATTERNS: tuple[tuple[str, str], ...] = (
    ("ASK_PLATFORM_CONTEXT", r"device|operating system|\bios\b|android|ios|app version|spotify version"),
    ("ASK_SYMPTOM_EVIDENCE", r"error message|screenshot|what happens|exact symptom"),
    ("ASK_SCOPE_OR_ENVIRONMENT", r"another device|different device|another browser|incognito|other artist|wifi|wi-fi|3g|4g|cellular"),
    ("ASK_CATALOG_CONTEXT", r"song link|song uri|track link|country is your account|catalog"),
    ("SESSION_RESET", r"log ?out|log ?in|restart|re-?start"),
    ("REINSTALL_OR_CLEAN_INSTALL", r"reinstall|clean install|uninstall"),
    ("BROWSER_REMEDIATION", r"clear (?:the )?cache|clear cookies|supported browser|another browser|incognito"),
    ("NETWORK_REMEDIATION", r"restart (?:the )?connection|try another network|wifi|wi-fi|cellular|mobile data"),
    ("PROVIDE_HELP_RESOURCE", r"https?://|help page|help link|support article"),
    ("REQUEST_SECURE_ACCOUNT_DETAILS", r"username|email address|account details|account email"),
    ("MOVE_TO_DM_OR_SECURE_CHANNEL", r"\bdm\b|direct message|private message|secure channel"),
    ("ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE", r"developer|technical team|tech team|investigat|passed .* feedback"),
    ("CONFIRM_AND_MONITOR", r"glad to hear|if it happens again|keep an eye|monitor|let us know if"),
)

_FAILURE = re.compile(r"\b(no luck|still (?:not|no|doesn|does not|won)|didn['’]?t help|did not help|nothing changed|neither worked|doesn['’]?t work|does not work|won['’]?t work|problem persists)\b", re.I)
_RESOLVED = re.compile(r"\b(fixed|resolved|working now|works now|it works|solved)\b", re.I)
_IMPROVED = re.compile(r"\b(better|improved|seems to have worked|working so far|partially)\b", re.I)


@dataclass(frozen=True)
class ActionFilterResult:
    eligible_actions: tuple[str, ...]
    rejected_actions: dict[str, str]
    repeated_failed_action_rate: float


def extract_attempted_actions(messages: Sequence[Message]) -> tuple[AttemptedAction, ...]:
    """Extract ordered action evidence from the supplied visible context only."""
    raw: list[tuple[str, str, int, str]] = []
    for index, message in enumerate(messages):
        for action, pattern in _ACTION_PATTERNS:
            if re.search(pattern, message.text, re.I):
                explicitness = "explicit" if message.role == "support" or re.search(r"\b(i|we) (tried|did|used)", message.text, re.I) else "inferred"
                raw.append((action, message.message_id, index, explicitness))
    ledger: list[AttemptedAction] = []
    for order, (action, source_id, index, explicitness) in enumerate(raw, 1):
        result_text = messages[index].text if messages[index].role == "customer" else ""
        if messages[index].role == "support":
            for following in messages[index + 1:]:
                if following.role == "support":
                    break
                if following.role == "customer":
                    result_text = following.text
                    break
        result = _result(result_text)
        ledger.append(
            AttemptedAction(
                action=action,
                order=order,
                source_message_id=source_id,
                explicitness=explicitness,
                result=result,
                result_evidence=result_text,
            )
        )
    return tuple(ledger)


def failed_actions(ledger: Iterable[AttemptedAction]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item.action for item in ledger if item.result == "failed"))


def filter_actions(
    candidates: Iterable[str],
    ledger: Iterable[AttemptedAction],
    *,
    allow_retry: bool = False,
) -> ActionFilterResult:
    """Remove directly repeated failed actions unless a caller has new evidence."""
    candidate_list = tuple(candidates)
    invalid = [action for action in candidate_list if action not in ACTIONS]
    if invalid:
        raise ValueError(f"candidate actions must use the frozen vocabulary: {invalid}")
    failed = set(failed_actions(ledger))
    rejected = {
        action: "customer-reported failure; retry requires new evidence"
        for action in candidate_list
        if action in failed and not allow_retry
    }
    eligible = tuple(action for action in candidate_list if action not in rejected)
    rate = sum(action in failed for action in candidate_list) / len(candidate_list) if candidate_list else 0.0
    return ActionFilterResult(eligible, rejected, round(rate, 4))


def _result(text: str) -> str:
    if not text:
        return "unknown"
    if _FAILURE.search(text):
        return "failed"
    if _RESOLVED.search(text):
        return "resolved"
    if _IMPROVED.search(text):
        return "improved"
    return "attempted"
