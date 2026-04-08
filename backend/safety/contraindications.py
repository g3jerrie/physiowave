"""PhysioWave — Contraindications Registry (The "Redline" Safety Gate).

HIPAA Compliance Note: This is a hardcoded logic gate. No AI model can
override these contraindications. Every AI suggestion MUST be validated
against this registry before reaching the patient-facing UI.

Sources:
- Physiotherapy_Combi_5in1_Machine_User_Manual.pdf (Section 3)
- Textbook of Electrotherapy (clinical guidelines)
- Therapeutic Exercise: Foundations and Techniques
"""

# ─── Master Registry ──────────────────────────────────────────────────
# Map: risk_factor → set of blocked therapy protocols

REGISTRY: dict[str, set[str]] = {
    # Implants & Devices
    "metal_implants": {
        "ultrasound_therapy", "shortwave_diathermy",
        "microwave_diathermy", "deep_heat_therapy",
    },
    "pacemaker": {
        "ultrasound_therapy", "electrical_stimulation", "ift_therapy",
        "tens_therapy", "shortwave_diathermy", "microwave_diathermy",
        "deep_heat_therapy",
    },
    "cardiac_monitor": {
        "ift_therapy", "tens_therapy", "electrical_stimulation",
        "shortwave_diathermy",
    },
    "cochlear_implant": {
        "shortwave_diathermy", "microwave_diathermy",
    },

    # Cardiovascular
    "dvt_history": {
        "deep_tissue_massage", "compression_therapy", "vigorous_exercise",
    },
    "active_hemorrhage": {
        "ultrasound_therapy", "deep_tissue_massage",
        "electrical_stimulation", "hydrotherapy",
    },
    "thrombophlebitis": {
        "deep_tissue_massage", "compression_therapy", "heat_therapy",
    },

    # Neurological
    "epilepsy": {
        "transcranial_stimulation", "high_frequency_tens",
        "electrical_stimulation",
    },
    "sensory_deficit": {
        "heat_therapy", "cryotherapy", "electrical_stimulation",
    },

    # Reproductive / Special
    "pregnancy": {
        "deep_heat_therapy", "electrical_stimulation",
        "high_intensity_laser", "shortwave_diathermy",
        "microwave_diathermy", "ultrasound_therapy",
    },

    # Musculoskeletal
    "osteoporosis": {
        "high_velocity_manipulation", "vigorous_massage",
        "high_impact_exercise",
    },
    "acute_fracture": {
        "vigorous_massage", "manipulation",
        "weight_bearing_exercise", "ultrasound_therapy",
    },

    # Dermatological / Tissue
    "open_wounds": {
        "ultrasound_therapy", "hydrotherapy", "electrical_stimulation",
    },
    "active_infection": {
        "hydrotherapy", "heat_therapy", "deep_tissue_massage",
    },
    "malignancy": {
        "ultrasound_therapy", "deep_heat_therapy",
        "shortwave_diathermy", "vigorous_massage",
    },
    "skin_disease_active": {
        "hydrotherapy", "electrical_stimulation", "ultrasound_therapy",
    },
}


def get_blocked_protocols(risk_factors: set[str]) -> set[str]:
    """Return all therapy protocols blocked by the given risk factors."""
    blocked = set()
    for factor in risk_factors:
        protocols = REGISTRY.get(factor)
        if protocols:
            blocked.update(protocols)
    return blocked


def is_contraindicated(protocol: str, risk_factors: set[str]) -> bool:
    """Check if a specific protocol is contraindicated."""
    normalized = protocol.lower().replace(" ", "_")
    return normalized in get_blocked_protocols(risk_factors)


def get_conflict_details(
    protocol: str, risk_factors: set[str]
) -> dict[str, set[str]]:
    """Return which risk factors block a specific protocol."""
    normalized = protocol.lower().replace(" ", "_")
    conflicts: dict[str, set[str]] = {}
    for factor in risk_factors:
        protocols = REGISTRY.get(factor)
        if protocols and normalized in protocols:
            conflicts.setdefault(factor, set()).add(normalized)
    return conflicts


def get_all_risk_factors() -> set[str]:
    """Return all known risk factor identifiers."""
    return set(REGISTRY.keys())


def get_all_protocols() -> set[str]:
    """Return all known therapy protocols that can be blocked."""
    protocols = set()
    for blocked_set in REGISTRY.values():
        protocols.update(blocked_set)
    return protocols
