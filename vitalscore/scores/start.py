"""START (Simple Triage And Rapid Treatment) triage calculator.

START is the most widely used mass-casualty-incident (MCI) triage system.
It classifies patients in under 60 seconds using three primary checks:

  1. WALK   — Can the patient walk?
  2. BREATHE — Is the patient breathing? Rate?
  3. PERFUSE — Adequate circulation? (radial pulse / cap refill)
  4. MENTAL  — Can the patient follow simple commands?

Priority categories
-------------------
  IMMEDIATE  (Red)    Life-threatening but salvageable; treat first.
  DELAYED    (Yellow) Serious; can wait for treatment.
  MINOR      (Green)  Minor injury; walking wounded.
  DECEASED   (Black)  No breathing after repositioning; or obviously dead.

Reference: Benson M et al. Ann Emerg Med. 1996;28(6):612-617.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class STARTPriority(str, Enum):
    """START triage priority tag colour."""
    IMMEDIATE = "Immediate"
    DELAYED   = "Delayed"
    MINOR     = "Minor"
    DECEASED  = "Deceased"


# Numeric sort order (lower = higher priority)
_SORT_ORDER: dict[STARTPriority, int] = {
    STARTPriority.IMMEDIATE: 0,
    STARTPriority.DELAYED:   1,
    STARTPriority.MINOR:     2,
    STARTPriority.DECEASED:  3,
}

_COLOURS: dict[STARTPriority, str] = {
    STARTPriority.IMMEDIATE: "Red",
    STARTPriority.DELAYED:   "Yellow",
    STARTPriority.MINOR:     "Green",
    STARTPriority.DECEASED:  "Black",
}

_RATIONALE: dict[STARTPriority, str] = {
    STARTPriority.IMMEDIATE: (
        "Life-threatening injury identified (RR >30, absent radial pulse / cap refill >2s, "
        "or cannot follow commands). Immediate intervention required."
    ),
    STARTPriority.DELAYED: (
        "Breathing present and controlled, perfusion adequate, follows commands. "
        "Serious but can tolerate a short delay in treatment."
    ),
    STARTPriority.MINOR: (
        "Patient is ambulatory (walking). Minor injuries. Treat after Immediate and Delayed."
    ),
    STARTPriority.DECEASED: (
        "No spontaneous respirations after airway repositioning. "
        "No intervention initiated under mass-casualty conditions."
    ),
}


@dataclass(frozen=True)
class STARTResult:
    """Structured result of a START triage assessment."""

    priority: STARTPriority
    can_walk: bool
    respiratory_rate: int | None         # breaths/min; None if not breathing
    has_radial_pulse: bool | None        # None if not assessed
    cap_refill_seconds: float | None     # None if not assessed
    follows_commands: bool | None        # None if not assessed

    @property
    def colour(self) -> str:
        return _COLOURS[self.priority]

    @property
    def sort_order(self) -> int:
        return _SORT_ORDER[self.priority]

    @property
    def rationale(self) -> str:
        return _RATIONALE[self.priority]

    def __str__(self) -> str:
        rr = f"{self.respiratory_rate}/min" if self.respiratory_rate is not None else "not breathing"
        pulse = {None: "not assessed", True: "present", False: "absent"}[self.has_radial_pulse]
        commands = {None: "not assessed", True: "yes", False: "no"}[self.follows_commands]
        return (
            f"START Triage: {self.priority.value.upper()}  [{self.colour} tag]\n"
            f"  Walking:          {'Yes' if self.can_walk else 'No'}\n"
            f"  Respiratory rate: {rr}\n"
            f"  Radial pulse:     {pulse}\n"
            f"  Follows commands: {commands}\n"
            f"  → {self.rationale}"
        )


def score_start(
    can_walk: bool,
    respiratory_rate: int | None,
    *,
    has_radial_pulse: bool | None = None,
    cap_refill_seconds: float | None = None,
    follows_commands: bool | None = None,
    airway_repositioned: bool = False,
) -> STARTResult:
    """Calculate START triage priority.

    Parameters
    ----------
    can_walk:
        True if the patient can walk to the minor-injury area.
    respiratory_rate:
        Breaths per minute after airway positioning. None means apnoeic.
    has_radial_pulse:
        True if radial pulse is palpable. Used when cap_refill_seconds is None.
    cap_refill_seconds:
        Capillary refill time in seconds. If ≤2 → adequate perfusion.
    follows_commands:
        True if patient can follow simple commands (e.g. "squeeze my fingers").
    airway_repositioned:
        True if airway has already been repositioned. If respiratory_rate is
        None and this is False, the function assumes repositioning could not
        restore breathing → Deceased.

    Returns
    -------
    STARTResult with priority, colour, and rationale.

    Raises
    ------
    ValueError for out-of-range respiratory rate.

    Examples
    --------
    >>> score_start(can_walk=True, respiratory_rate=18).priority
    <STARTPriority.MINOR: 'Minor'>

    >>> score_start(can_walk=False, respiratory_rate=None).priority
    <STARTPriority.DECEASED: 'Deceased'>

    >>> score_start(can_walk=False, respiratory_rate=35).priority
    <STARTPriority.IMMEDIATE: 'Immediate'>

    >>> score_start(
    ...     can_walk=False, respiratory_rate=18,
    ...     has_radial_pulse=True, follows_commands=True
    ... ).priority
    <STARTPriority.DELAYED: 'Delayed'>
    """
    # Step 1 — Walking wounded → Minor
    if can_walk:
        return STARTResult(
            priority=STARTPriority.MINOR,
            can_walk=True,
            respiratory_rate=respiratory_rate,
            has_radial_pulse=has_radial_pulse,
            cap_refill_seconds=cap_refill_seconds,
            follows_commands=follows_commands,
        )

    # Step 2 — Respirations
    if respiratory_rate is None:
        # No breathing — apnoeic
        return STARTResult(
            priority=STARTPriority.DECEASED,
            can_walk=False,
            respiratory_rate=None,
            has_radial_pulse=None,
            cap_refill_seconds=None,
            follows_commands=None,
        )

    if not (0 <= respiratory_rate <= 100):
        raise ValueError(f"respiratory_rate must be 0–100 breaths/min, got {respiratory_rate!r}")

    if respiratory_rate > 30:
        return STARTResult(
            priority=STARTPriority.IMMEDIATE,
            can_walk=False,
            respiratory_rate=respiratory_rate,
            has_radial_pulse=has_radial_pulse,
            cap_refill_seconds=cap_refill_seconds,
            follows_commands=follows_commands,
        )

    # Step 3 — Perfusion
    # Use cap refill if provided, otherwise fall back to radial pulse
    perfusion_ok: bool | None = None
    if cap_refill_seconds is not None:
        perfusion_ok = cap_refill_seconds <= 2.0
    elif has_radial_pulse is not None:
        perfusion_ok = has_radial_pulse

    if perfusion_ok is False:
        return STARTResult(
            priority=STARTPriority.IMMEDIATE,
            can_walk=False,
            respiratory_rate=respiratory_rate,
            has_radial_pulse=has_radial_pulse,
            cap_refill_seconds=cap_refill_seconds,
            follows_commands=follows_commands,
        )

    # Step 4 — Mental status
    if follows_commands is False:
        return STARTResult(
            priority=STARTPriority.IMMEDIATE,
            can_walk=False,
            respiratory_rate=respiratory_rate,
            has_radial_pulse=has_radial_pulse,
            cap_refill_seconds=cap_refill_seconds,
            follows_commands=False,
        )

    # All checks passed → Delayed
    return STARTResult(
        priority=STARTPriority.DELAYED,
        can_walk=False,
        respiratory_rate=respiratory_rate,
        has_radial_pulse=has_radial_pulse,
        cap_refill_seconds=cap_refill_seconds,
        follows_commands=follows_commands,
    )
