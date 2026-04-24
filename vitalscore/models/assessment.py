"""Clinical assessment data models.

CUPS   — patient priority classification (Critical / Unstable / Potentially unstable / Stable)
OPQRST — pain/symptom history mnemonic
SAMPLE — complete patient history mnemonic
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ═══════════════════════════════════════════════════════════════════════════════
# CUPS
# ═══════════════════════════════════════════════════════════════════════════════

class CUPSCategory(str, Enum):
    """CUPS patient priority category.

    Used primarily in pre-hospital and EMS settings to rapidly
    categorise patients for transport and resource allocation.
    """
    CRITICAL            = "Critical"
    UNSTABLE            = "Unstable"
    POTENTIALLY_UNSTABLE = "Potentially unstable"
    STABLE              = "Stable"


_CUPS_DESCRIPTIONS: dict[CUPSCategory, str] = {
    CUPSCategory.CRITICAL: (
        "Life-threatening condition. Immediate intervention required. "
        "Highest transport priority — lights and siren."
    ),
    CUPSCategory.UNSTABLE: (
        "Potentially life-threatening. Condition may deteriorate rapidly. "
        "Expedited transport with ALS monitoring."
    ),
    CUPSCategory.POTENTIALLY_UNSTABLE: (
        "Currently stable, but signs or history suggest possible deterioration. "
        "Monitor closely during transport. ALS standby advised."
    ),
    CUPSCategory.STABLE: (
        "No immediate life threat. Routine transport with BLS monitoring. "
        "Reassess regularly."
    ),
}

_CUPS_TRANSPORT_PRIORITY: dict[CUPSCategory, int] = {
    CUPSCategory.CRITICAL:            1,
    CUPSCategory.UNSTABLE:            2,
    CUPSCategory.POTENTIALLY_UNSTABLE: 3,
    CUPSCategory.STABLE:              4,
}


@dataclass
class CUPS:
    """CUPS classification data model.

    Parameters
    ----------
    category:
        CUPSCategory enum value or a string matching one of:
        'Critical', 'Unstable', 'Potentially unstable', 'Stable'.
    chief_complaint:
        Brief description of why the patient is being assessed.
    notes:
        Any additional clinical notes.

    Examples
    --------
    >>> c = CUPS(category="Critical", chief_complaint="Unresponsive, no pulse")
    >>> c.transport_priority
    1
    >>> c.description
    'Life-threatening condition...'
    """

    category: CUPSCategory
    chief_complaint: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.category, str):
            # Accept either the full label or a normalised variant
            normalised = self.category.strip().lower()
            for cat in CUPSCategory:
                if cat.value.lower() == normalised:
                    object.__setattr__(self, "category", cat)
                    return
            valid = [c.value for c in CUPSCategory]
            raise ValueError(f"CUPSCategory must be one of {valid}, got {self.category!r}")

    @property
    def description(self) -> str:
        return _CUPS_DESCRIPTIONS[self.category]

    @property
    def transport_priority(self) -> int:
        """1 (highest) to 4 (lowest)."""
        return _CUPS_TRANSPORT_PRIORITY[self.category]

    def __str__(self) -> str:
        parts = [
            f"CUPS: {self.category.value}  (transport priority {self.transport_priority})",
            f"  {self.description}",
        ]
        if self.chief_complaint:
            parts.append(f"  Chief complaint: {self.chief_complaint}")
        if self.notes:
            parts.append(f"  Notes: {self.notes}")
        return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# OPQRST
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class OPQRST:
    """OPQRST pain/symptom characterisation model.

    All fields are optional strings so the model can be populated
    incrementally during a patient assessment.

    Fields
    ------
    onset:         When did the symptom start? Was it sudden or gradual?
    provocation:   What makes it better or worse? (Position, activity, food, …)
    palliation:    What relieves the symptom? (Rest, medication, position, …)
    quality:       How does the patient describe it? (Sharp, dull, pressure, burning, …)
    radiation:     Does it radiate or move anywhere?
    severity:      Severity on a 0–10 scale (stored as int; None = not assessed)
    time:          How long has it been present? Any previous episodes?
    associated:    Associated symptoms (SOB, nausea, diaphoresis, …)

    Examples
    --------
    >>> p = OPQRST(
    ...     onset="Sudden, during exertion",
    ...     quality="Crushing pressure",
    ...     radiation="Radiates to left arm",
    ...     severity=8,
    ... )
    >>> print(p.summary)
    """

    onset:       str | None = None
    provocation: str | None = None
    palliation:  str | None = None
    quality:     str | None = None
    radiation:   str | None = None
    severity:    int | None = None     # 0–10 NRS
    time:        str | None = None
    associated:  str | None = None

    def __post_init__(self) -> None:
        if self.severity is not None and not (0 <= self.severity <= 10):
            raise ValueError(f"severity must be 0–10, got {self.severity!r}")

    @property
    def summary(self) -> str:
        rows: list[str] = ["OPQRST Symptom Assessment"]
        fields: dict[str, Any] = {
            "O — Onset":       self.onset,
            "P — Provocation": self.provocation,
            "P — Palliation":  self.palliation,
            "Q — Quality":     self.quality,
            "R — Radiation":   self.radiation,
            "S — Severity":    f"{self.severity}/10" if self.severity is not None else None,
            "T — Time":        self.time,
            "A — Associated":  self.associated,
        }
        for label, value in fields.items():
            marker = value if value is not None else "(not recorded)"
            rows.append(f"  {label}: {marker}")
        return "\n".join(rows)

    def __str__(self) -> str:
        return self.summary


# ═══════════════════════════════════════════════════════════════════════════════
# SAMPLE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SAMPLE:
    """SAMPLE patient history data model.

    SAMPLE is a mnemonic for collecting a complete patient history
    in emergency and pre-hospital settings.

    Fields
    ------
    signs_symptoms:     Primary complaint(s) and any objective findings.
    allergies:          Known drug or environmental allergies (with reaction type).
    medications:        Current medications including OTC, supplements, inhalers.
    pertinent_history:  Relevant past medical/surgical history, previous similar events.
    last_oral_intake:   Time of last food/drink (critical pre-sedation / surgical).
    events:             What was the patient doing when symptoms began? Precipitating events.
    additional:         Any other relevant information.

    Examples
    --------
    >>> h = SAMPLE(
    ...     signs_symptoms="Chest pain, diaphoresis",
    ...     allergies="Penicillin (anaphylaxis)",
    ...     medications="Aspirin 81 mg daily, Metformin 500 mg BD",
    ...     pertinent_history="HTN, T2DM, previous MI 2019",
    ...     last_oral_intake="6 hours ago",
    ...     events="Onset at rest, watching TV",
    ... )
    >>> print(h)
    """

    signs_symptoms:     str | None = None
    allergies:          str | None = None
    medications:        str | None = None
    pertinent_history:  str | None = None
    last_oral_intake:   str | None = None
    events:             str | None = None
    additional:         str | None = None

    @property
    def has_allergies(self) -> bool:
        """True if allergies field is populated with something other than 'NKDA' / 'none'."""
        if not self.allergies:
            return False
        return self.allergies.strip().upper() not in {"NKDA", "NKA", "NONE", "NIL", "NO"}

    @property
    def summary(self) -> str:
        rows: list[str] = ["SAMPLE Patient History"]
        fields: dict[str, Any] = {
            "S — Signs/Symptoms":     self.signs_symptoms,
            "A — Allergies":          self.allergies,
            "M — Medications":        self.medications,
            "P — Pertinent history":  self.pertinent_history,
            "L — Last oral intake":   self.last_oral_intake,
            "E — Events":             self.events,
        }
        if self.additional:
            fields["Additional"] = self.additional

        for label, value in fields.items():
            marker = value if value is not None else "(not recorded)"
            rows.append(f"  {label}: {marker}")
        return "\n".join(rows)

    def __str__(self) -> str:
        return self.summary
