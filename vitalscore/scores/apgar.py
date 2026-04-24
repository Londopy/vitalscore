"""APGAR score calculator.

The APGAR score evaluates newborn health at 1 and 5 minutes after birth.

  A — Appearance   (skin colour)         0–2
  P — Pulse        (heart rate)           0–2
  G — Grimace      (reflex irritability)  0–2
  A — Activity     (muscle tone)          0–2
  R — Respiration  (breathing effort)     0–2

Total: 0 (no detectable life signs) to 10 (optimal newborn).

Reference: Apgar V. Curr Res Anesth Analg. 1953;32(4):260-7.
"""

from __future__ import annotations
from dataclasses import dataclass


_COMPONENT_RANGE = range(0, 3)  # 0, 1, 2

# ── descriptor maps ───────────────────────────────────────────────────────────
APPEARANCE_DESCRIPTORS: dict[int, str] = {
    0: "Blue/pale all over",
    1: "Blue extremities, pink body (acrocyanosis)",
    2: "Pink all over",
}

PULSE_DESCRIPTORS: dict[int, str] = {
    0: "Absent (no heartbeat)",
    1: "< 100 bpm",
    2: "≥ 100 bpm",
}

GRIMACE_DESCRIPTORS: dict[int, str] = {
    0: "No response to stimulation",
    1: "Grimace on stimulation",
    2: "Cry or cough/sneeze on stimulation",
}

ACTIVITY_DESCRIPTORS: dict[int, str] = {
    0: "None (limp)",
    1: "Some flexion",
    2: "Active motion (flexed limbs)",
}

RESPIRATION_DESCRIPTORS: dict[int, str] = {
    0: "Absent",
    1: "Weak/irregular/gasping",
    2: "Strong cry",
}


@dataclass(frozen=True)
class APGARResult:
    """Structured result of an APGAR assessment."""

    appearance: int
    pulse: int
    grimace: int
    activity: int
    respiration: int

    @property
    def total(self) -> int:
        return self.appearance + self.pulse + self.grimace + self.activity + self.respiration

    @property
    def category(self) -> str:
        t = self.total
        if t >= 7:
            return "Normal"
        if t >= 4:
            return "Moderate concern"
        return "Immediate intervention required"

    @property
    def interpretation(self) -> str:
        t = self.total
        if t >= 7:
            return (
                f"APGAR {t}/10 — Normal. Routine post-delivery care."
            )
        if t >= 4:
            return (
                f"APGAR {t}/10 — Moderate concern. Stimulate, provide supplemental O₂, "
                f"prepare resuscitation equipment."
            )
        return (
            f"APGAR {t}/10 — Immediate intervention required. "
            f"Begin neonatal resuscitation protocol immediately."
        )

    def __str__(self) -> str:
        rows = [
            f"  Appearance:  {self.appearance} — {APPEARANCE_DESCRIPTORS[self.appearance]}",
            f"  Pulse:       {self.pulse} — {PULSE_DESCRIPTORS[self.pulse]}",
            f"  Grimace:     {self.grimace} — {GRIMACE_DESCRIPTORS[self.grimace]}",
            f"  Activity:    {self.activity} — {ACTIVITY_DESCRIPTORS[self.activity]}",
            f"  Respiration: {self.respiration} — {RESPIRATION_DESCRIPTORS[self.respiration]}",
        ]
        return (
            f"APGAR {self.total}/10 — {self.category}\n"
            + "\n".join(rows)
            + f"\n  → {self.interpretation}"
        )


def score_apgar(
    appearance: int,
    pulse: int,
    grimace: int,
    activity: int,
    respiration: int,
) -> APGARResult:
    """Calculate APGAR score.

    Parameters
    ----------
    appearance:  Skin colour score        (0–2)
    pulse:       Heart rate score         (0–2)
    grimace:     Reflex irritability score (0–2)
    activity:    Muscle tone score        (0–2)
    respiration: Breathing effort score   (0–2)

    Returns
    -------
    APGARResult with total, category, and interpretation.

    Raises
    ------
    ValueError if any component is outside 0–2.

    Examples
    --------
    >>> r = score_apgar(2, 2, 2, 2, 2)
    >>> r.total
    10
    >>> r.category
    'Normal'
    >>> r = score_apgar(0, 0, 0, 1, 0)
    >>> r.category
    'Immediate intervention required'
    """
    components = {
        "appearance": appearance,
        "pulse": pulse,
        "grimace": grimace,
        "activity": activity,
        "respiration": respiration,
    }
    for name, value in components.items():
        if value not in _COMPONENT_RANGE:
            raise ValueError(f"{name} must be 0–2, got {value!r}")

    return APGARResult(
        appearance=appearance,
        pulse=pulse,
        grimace=grimace,
        activity=activity,
        respiration=respiration,
    )
