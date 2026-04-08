"""PhysioWave — Contraindications Registry Tests.

Tests the 'Redline' safety gate — the hardcoded logic that cannot be
overridden by any AI model.
"""

from backend.safety.contraindications import (
    get_all_protocols,
    get_all_risk_factors,
    get_blocked_protocols,
    get_conflict_details,
    is_contraindicated,
)


class TestContraindicationsRegistry:
    """Tests for the hardcoded contraindications registry."""

    def test_metal_implants_blocks_ultrasound(self):
        assert is_contraindicated("ultrasound_therapy", {"metal_implants"})

    def test_pacemaker_blocks_ift(self):
        assert is_contraindicated("ift_therapy", {"pacemaker"})

    def test_pacemaker_blocks_electrical_stimulation(self):
        assert is_contraindicated("electrical_stimulation", {"pacemaker"})

    def test_pregnancy_blocks_deep_heat(self):
        assert is_contraindicated("deep_heat_therapy", {"pregnancy"})

    def test_safe_protocol_not_contraindicated(self):
        assert not is_contraindicated("gentle_stretching", {"metal_implants"})

    def test_empty_risks_returns_no_blocked(self):
        blocked = get_blocked_protocols(set())
        assert len(blocked) == 0

    def test_multiple_risks_accumulate(self):
        blocked = get_blocked_protocols({"metal_implants", "pacemaker"})
        assert "ultrasound_therapy" in blocked
        assert "ift_therapy" in blocked
        assert "tens_therapy" in blocked

    def test_conflict_details_returns_triggering_factors(self):
        conflicts = get_conflict_details(
            "ultrasound_therapy",
            {"metal_implants", "pregnancy"},
        )
        assert "metal_implants" in conflicts
        assert "pregnancy" in conflicts

    def test_space_normalization(self):
        assert is_contraindicated("ultrasound therapy", {"metal_implants"})

    def test_all_risk_factors_non_empty(self):
        assert len(get_all_risk_factors()) > 0

    def test_all_protocols_non_empty(self):
        assert len(get_all_protocols()) > 0

    def test_every_risk_factor_has_blocked_protocols(self):
        """No risk factor should have an empty blocked set."""
        for factor in get_all_risk_factors():
            blocked = get_blocked_protocols({factor})
            assert len(blocked) > 0, (
                f'Risk factor "{factor}" has no blocked protocols'
            )

    def test_malignancy_blocks_ultrasound(self):
        assert is_contraindicated("ultrasound_therapy", {"malignancy"})

    def test_open_wounds_blocks_hydrotherapy(self):
        assert is_contraindicated("hydrotherapy", {"open_wounds"})

    def test_sensory_deficit_blocks_heat_therapy(self):
        assert is_contraindicated("heat_therapy", {"sensory_deficit"})
