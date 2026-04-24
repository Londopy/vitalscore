"""Batch triage — score a list of patients and return sorted priority order.

Supports START and NEWS2 batch scoring.  Each patient is wrapped in a
TriagePatient dataclass and results are sorted from most to least critical.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from vitalscore.scores.start import STARTPriority, STARTResult, score_start
from vitalscore.scores.news2 import NEWS2Result, score_news2, ACVPULevel


# ═══════════════════════════════════════════════════════════════════════════════
# Generic patient wrapper
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TriagePatient:
    """Container for a single patient's triage inputs and computed result.

    Attributes
    ----------
    patient_id:     A unique identifier (name, number, tag).
    start_result:   Populated after batch_triage() runs START scoring.
    news2_result:   Populated after batch_triage() runs NEWS2 scoring.
    metadata:       Any extra key-value pairs (age, location, incident note, …).
    """

    patient_id:   str
    # START inputs
    can_walk:               bool | None = None
    respiratory_rate:       int | None  = None
    has_radial_pulse:       bool | None = None
    cap_refill_seconds:     float | None = None
    follows_commands:       bool | None = None
    # NEWS2 inputs
    spo2:           float | None = None
    on_oxygen:      bool  | None = None
    systolic_bp:    int   | None = None
    heart_rate:     int   | None = None
    consciousness:  str   | None = None
    temperature:    float | None = None
    use_spo2_scale2: bool = False
    # computed
    start_result:   STARTResult | None = field(default=None, repr=False)
    news2_result:   NEWS2Result | None = field(default=None, repr=False)
    errors:         list[str]   = field(default_factory=list, repr=False)
    metadata:       dict[str, Any] = field(default_factory=dict, repr=False)

    # ── convenience properties ─────────────────────────────────────────────────

    @property
    def start_priority(self) -> STARTPriority | None:
        return self.start_result.priority if self.start_result else None

    @property
    def start_sort_key(self) -> int:
        """Lower = higher priority (Immediate=0, Delayed=1, Minor=2, Deceased=3, None=99)."""
        if self.start_result is None:
            return 99
        return self.start_result.sort_order

    @property
    def news2_sort_key(self) -> int:
        """Lower = higher risk.  High=0, Medium=1, Low=2, None=99."""
        if self.news2_result is None:
            return 99
        mapping = {"High": 0, "Medium": 1, "Low": 2}
        return mapping.get(self.news2_result.risk.value, 99)


# ═══════════════════════════════════════════════════════════════════════════════
# Batch runners
# ═══════════════════════════════════════════════════════════════════════════════

def batch_triage(
    patients: list[TriagePatient],
    *,
    method: str = "start",
) -> list[TriagePatient]:
    """Score a list of patients and return them sorted by priority (most critical first).

    Parameters
    ----------
    patients: List of TriagePatient objects with relevant fields populated.
    method:   'start' (default), 'news2', or 'both'.

    Returns
    -------
    The same list of TriagePatient objects with result fields populated,
    sorted from highest to lowest priority.

    Raises
    ------
    ValueError if method is not recognised.

    Examples
    --------
    >>> from vitalscore.batch import TriagePatient, batch_triage
    >>> pts = [
    ...     TriagePatient("P1", can_walk=True, respiratory_rate=18),
    ...     TriagePatient("P2", can_walk=False, respiratory_rate=35),
    ...     TriagePatient("P3", can_walk=False, respiratory_rate=14,
    ...                   has_radial_pulse=True, follows_commands=True),
    ... ]
    >>> sorted_pts = batch_triage(pts, method="start")
    >>> [p.patient_id for p in sorted_pts]
    ['P2', 'P3', 'P1']
    >>> sorted_pts[0].start_priority.value
    'Immediate'
    """
    valid_methods = {"start", "news2", "both"}
    if method not in valid_methods:
        raise ValueError(f"method must be one of {valid_methods}, got {method!r}")

    for patient in patients:
        if method in ("start", "both"):
            _run_start(patient)
        if method in ("news2", "both"):
            _run_news2(patient)

    if method == "news2":
        return sorted(patients, key=lambda p: (p.news2_sort_key, p.patient_id))
    # Default sort is START priority, with NEWS2 as tiebreaker
    return sorted(patients, key=lambda p: (p.start_sort_key, p.news2_sort_key, p.patient_id))


def _run_start(patient: TriagePatient) -> None:
    """Attempt START scoring; record error on the patient if inputs are missing/invalid."""
    if patient.can_walk is None:
        patient.errors.append("START: 'can_walk' is required")
        return
    try:
        patient.start_result = score_start(
            can_walk=patient.can_walk,
            respiratory_rate=patient.respiratory_rate,
            has_radial_pulse=patient.has_radial_pulse,
            cap_refill_seconds=patient.cap_refill_seconds,
            follows_commands=patient.follows_commands,
        )
    except Exception as exc:
        patient.errors.append(f"START error: {exc}")


def _run_news2(patient: TriagePatient) -> None:
    """Attempt NEWS2 scoring; record error on the patient if inputs are missing/invalid."""
    required = {
        "respiratory_rate": patient.respiratory_rate,
        "spo2":             patient.spo2,
        "on_oxygen":        patient.on_oxygen,
        "systolic_bp":      patient.systolic_bp,
        "heart_rate":       patient.heart_rate,
        "consciousness":    patient.consciousness,
        "temperature":      patient.temperature,
    }
    missing = [k for k, v in required.items() if v is None]
    if missing:
        patient.errors.append(f"NEWS2: missing fields: {', '.join(missing)}")
        return
    try:
        patient.news2_result = score_news2(
            respiratory_rate=patient.respiratory_rate,  # type: ignore[arg-type]
            spo2=patient.spo2,                          # type: ignore[arg-type]
            on_oxygen=patient.on_oxygen,                # type: ignore[arg-type]
            systolic_bp=patient.systolic_bp,            # type: ignore[arg-type]
            heart_rate=patient.heart_rate,              # type: ignore[arg-type]
            consciousness=patient.consciousness,        # type: ignore[arg-type]
            temperature=patient.temperature,            # type: ignore[arg-type]
            use_spo2_scale2=patient.use_spo2_scale2,
        )
    except Exception as exc:
        patient.errors.append(f"NEWS2 error: {exc}")


# ═══════════════════════════════════════════════════════════════════════════════
# Pretty-print utility
# ═══════════════════════════════════════════════════════════════════════════════

def format_triage_report(patients: list[TriagePatient]) -> str:
    """Return a plain-text sorted triage report for a list of scored patients."""
    lines: list[str] = [
        "=" * 60,
        f"  TRIAGE REPORT  —  {len(patients)} patient(s)",
        "=" * 60,
    ]
    for rank, p in enumerate(patients, start=1):
        lines.append(f"\n#{rank}  Patient: {p.patient_id}")
        if p.start_result:
            lines.append(
                f"  START: {p.start_result.priority.value.upper()} [{p.start_result.colour}]"
            )
        if p.news2_result:
            lines.append(
                f"  NEWS2: {p.news2_result.total}/20  [{p.news2_result.risk.value} risk]"
            )
        if p.errors:
            for err in p.errors:
                lines.append(f"  ⚠  {err}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)
