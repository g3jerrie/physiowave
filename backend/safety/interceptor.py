"""PhysioWave — Safety Interceptor.

HIPAA Compliance Note: This interceptor is the final safety gate between
the AI model output and the patient-facing UI. It MUST be called for
every AI suggestion. No bypass mechanism exists by design.
"""

from dataclasses import dataclass, field

from backend.core.logger import logger
from backend.safety.contraindications import (
    get_all_protocols,
    get_conflict_details,
    is_contraindicated,
)


@dataclass
class ProtocolConflict:
    """A therapy protocol that conflicts with patient risk factors."""
    protocol: str
    triggering_factors: set[str]


@dataclass
class SafetyResult:
    """Result of a safety validation check."""
    is_safe: bool
    suggestion: str
    conflicts: list[ProtocolConflict] = field(default_factory=list)
    warning_message: str | None = None


class SafetyInterceptor:
    """Validates AI suggestions against the patient's risk profile.

    HIPAA Compliance Note: This interceptor CANNOT be bypassed.
    Every AI suggestion must pass through validate() before
    being returned to the user.
    """

    def validate(
        self,
        suggestion: str,
        risk_factors: set[str],
    ) -> SafetyResult:
        """Validate an AI suggestion against patient risk factors.

        Returns SafetyResult with is_safe=True if no conflicts,
        or is_safe=False with conflict details and warning message.
        """
        if not risk_factors:
            return SafetyResult(is_safe=True, suggestion=suggestion)

        # Extract mentioned protocols from the suggestion text
        mentioned = self._extract_protocols(suggestion)
        if not mentioned:
            return SafetyResult(is_safe=True, suggestion=suggestion)

        # Cross-reference each protocol against risk factors
        conflicts: list[ProtocolConflict] = []
        for protocol in mentioned:
            if is_contraindicated(protocol, risk_factors):
                details = get_conflict_details(protocol, risk_factors)
                conflicts.append(
                    ProtocolConflict(
                        protocol=protocol,
                        triggering_factors=set(details.keys()),
                    )
                )

        if not conflicts:
            return SafetyResult(is_safe=True, suggestion=suggestion)

        warning = self._build_warning(conflicts)
        logger.warning(
            f"Safety BLOCKED: {len(conflicts)} contraindication(s) detected"
        )

        return SafetyResult(
            is_safe=False,
            suggestion=suggestion,
            conflicts=conflicts,
            warning_message=warning,
        )

    def _extract_protocols(self, suggestion: str) -> set[str]:
        """Extract therapy protocol names mentioned in suggestion text."""
        normalized = suggestion.lower()
        found: set[str] = set()

        for protocol in get_all_protocols():
            readable = protocol.replace("_", " ")
            if readable in normalized or protocol in normalized:
                found.add(protocol)

        return found

    def _build_warning(self, conflicts: list[ProtocolConflict]) -> str:
        """Build user-facing warning message."""
        lines = [
            "⚠️ HIGH-RISK WARNING: Contraindications Detected",
            "",
            "The following suggested protocols conflict with the patient's "
            "medical history:",
            "",
        ]

        for conflict in conflicts:
            readable = conflict.protocol.replace("_", " ").upper()
            factors = ", ".join(
                f.replace("_", " ") for f in conflict.triggering_factors
            )
            lines.append(f"  • {readable} — blocked due to: {factors}")

        lines.extend([
            "",
            "These protocols have been automatically blocked. "
            "Please consult the patient's full history before proceeding.",
        ])

        return "\n".join(lines)


# Singleton
safety_interceptor = SafetyInterceptor()
