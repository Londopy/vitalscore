"""Glasgow Coma Scale (GCS) calculator.

GCS assesses level of consciousness across three components:
  Eye Opening (E)   — 1 to 4
  Verbal Response (V) — 1 to 5
  Motor Response (M)  — 1 to 6

Total range: 3 (deep coma / death) to 15 (fully alert).

Reference: Teasdale G, Jennett B. Lancet. 1974;2(7872):81-84.
"""

from __future__ import annotations
from dataclasses import dataclass


# ── validation ranges ──────────────────────────────────────────────────────────
_EYE_RANGE = range(1, 5)     # 1-4
_VERBAL_RANGE = range(1, 6)  # 1-5
_MOTOR_RANGE = range(1, 7)   # 1-6

# ── descriptor maps ───────────────────────────────────────────────────────────
EYE_DESCRIPTORS: dict[int, str] = {
    1: "No eye opening",
    2: "Eye opening to pain",
    3: "Eye opening to voice",
    4: "Eyes open spontaneously",
}

VERBAL_DESCRIPTORS: dict[int, str] = {
    1: "No verbal response",
    2: "Incomprehensible sounds",
    3: "Inappropriate words",
    4: "Confused",
    5: "Oriented",
}

MOTOR_DESCRIPTORS: dict[int, str] = {
    1: "No motor response",
    2: "Extension to pain (decerebrate)",
    3: "Flexion to pain (decorticate)",
    4: "Withdrawal from pain",
    5: "Localises pain",
    6: "Obeys commands",
}


@dataclass(frozen=True)
class GCSResult:
    """Structured result of a GCS assessment."""

    eye: int
    verbal: int
    motor: int

    @property
    def total(self) -> int:
        return self.eye + self.verbal + self.motor

    @property
    def eye_descriptor(self) -> str:
        return EYE_DESCRIPTORS[self.eye]

    @property
    def verbal_descriptor(self) -> str:
        return VERBAL_DESCRIPTORS[self.verbal]

    @property
    def motor_descriptor(self) -> str:
        return MOTOR_DESCRIPTORS[self.motor]

    @property
    def severity(self) -> str:
        """Clinically accepted TBI severity band."""
        t = self.total
        if t >= 13:
            return "Mild TBI"
        if t >= 9:
            return "Moderate TBI"
        return "Severe TBI"

    @property
    def interpretation(self) -> str:
        t = self.total
        if t == 15:
            return "Normal — fully alert and oriented"
        if t >= 13:
            return f"Mild TBI (GCS {t}) — minor impairment, monitor closely"
        if t >= 9:
            return f"Moderate TBI (GCS {t}) — significant impairment, urgent evaluation required"
        return f"Severe TBI (GCS {t}) — critical, consider intubation and ICU"

    def __str__(self) -> str:
        return (
            f"GCS {self.total}/15  [E{self.eye} V{self.verbal} M{self.motor}]\n"
            f"  Eye:    {self.eye} — {self.eye_descriptor}\n"
            f"  Verbal: {self.verbal} — {self.verbal_descriptor}\n"
            f"  Motor:  {self.motor} — {self.motor_descriptor}\n"
            f"  → {self.interpretation}"
        )


def score_gcs(eye: int, verbal: int, motor: int) -> GCSResult:
    """Calculate GCS score.

    Parameters
    ----------
    eye:    Eye opening score      (1–4)
    verbal: Verbal response score  (1–5)
    motor:  Motor response score   (1–6)

    Returns
    -------
    GCSResult dataclass with total, severity, and interpretation.

    Raises
    ------
    ValueError if any component is outside its valid range.

    Examples
    --------
    >>> r = score_gcs(eye=4, verbal=5, motor=6)
    >>> r.total
    15
    >>> r.severity
    'Mild TBI'
    >>> r = score_gcs(eye=2, verbal=1, motor=3)
    >>> r.severity
    'Severe TBI'
    """
    if eye not in _EYE_RANGE:
        raise ValueError(f"Eye opening must be 1–4, got {eye!r}")
    if verbal not in _VERBAL_RANGE:
        raise ValueError(f"Verbal response must be 1–5, got {verbal!r}")
    if motor not in _MOTOR_RANGE:
        raise ValueError(f"Motor response must be 1–6, got {motor!r}")

    return GCSResult(eye=eye, verbal=verbal, motor=motor)
