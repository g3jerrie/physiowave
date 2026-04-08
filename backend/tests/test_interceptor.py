"""PhysioWave — Safety Interceptor Tests."""

from backend.safety.interceptor import SafetyInterceptor


class TestSafetyInterceptor:
    """Tests for the AI suggestion safety gate."""

    def setup_method(self):
        self.interceptor = SafetyInterceptor()

    def test_passes_safe_suggestion_no_risks(self):
        result = self.interceptor.validate(
            suggestion="Recommend gentle stretching exercises for 15 minutes.",
            risk_factors=set(),
        )
        assert result.is_safe

    def test_passes_suggestion_no_contraindicated_protocols(self):
        result = self.interceptor.validate(
            suggestion="Recommend gentle stretching exercises.",
            risk_factors={"metal_implants"},
        )
        assert result.is_safe

    def test_blocks_ultrasound_for_metal_implants(self):
        result = self.interceptor.validate(
            suggestion="I recommend ultrasound therapy at 1.5W/cm² for 10 minutes.",
            risk_factors={"metal_implants"},
        )
        assert not result.is_safe
        assert len(result.conflicts) > 0
        assert any(c.protocol == "ultrasound_therapy" for c in result.conflicts)
        assert "HIGH-RISK WARNING" in (result.warning_message or "")

    def test_blocks_electrical_stimulation_for_pacemaker(self):
        result = self.interceptor.validate(
            suggestion="Apply electrical stimulation to the affected quadricep.",
            risk_factors={"pacemaker"},
        )
        assert not result.is_safe

    def test_multiple_contraindications(self):
        result = self.interceptor.validate(
            suggestion="Plan: Start with ultrasound therapy, then electrical stimulation.",
            risk_factors={"pacemaker"},
        )
        assert not result.is_safe
        assert len(result.conflicts) >= 2

    def test_warning_includes_risk_details(self):
        result = self.interceptor.validate(
            suggestion="Consider ift therapy for pain management.",
            risk_factors={"cardiac_monitor"},
        )
        assert not result.is_safe
        assert "cardiac" in (result.warning_message or "").lower()

    def test_empty_suggestion_is_safe(self):
        result = self.interceptor.validate(
            suggestion="",
            risk_factors={"metal_implants"},
        )
        assert result.is_safe
