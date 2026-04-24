"""AVPU (Alert, Voice, Pain, Unresponsive) consciousness scale.

A rapid four-level assessment of a patient's level of consciousness.

Reference: Kelly CA et al. J Accid Emerg Med. 2004.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class AVPULevel(str, Enum):
    """AVPU level of consciousness."""
    ALERT = "A"
    VOICE = "V"
    PAIN = "P"
    UNRESPONSIVE = "U"


_GCS_EQUIVALENT: dict[AVPULevel, str] = {
    AVPULevel.ALERT:        "GCS 15 (estimated)",
    AVPULevel.VOICE:        "GCS ~12–13 (estimated)",
    AVPULevel.PAIN:         "GCS ~8 (estimated)",
    AVPULevel.UNRESPONSIVE: "GCS 3 (estimated)",
}

_DESCRIPTIONS: dict[AVPULevel, str] = {
    AVPULevel.ALERT:        "Patient is fully awake, alert, and oriented",
    AVPULevel.VOICE:        "Patient responds to voice but is not fully alert",
    AVPULevel.PAIN:         "Patient responds only to painful stimuli",
    AVPULevel.UNRESPONSIVE: "Patient does not respond to any stimuli",
}

_ACTIONS: dict[AVPULevel, str] = {
    AVPULevel.ALERT:        "Routine assessment; monitor for deterioration",
    AVPULevel.VOICE:        "Urgent evaluation; protect airway, consider supplemental O₂",
    AVPULevel.PAIN:         "Immediate intervention; manage airway, IV access, call for help",
    AVPULevel.UNRESPONSIVE: "Resuscitation-level response; CPR if pulseless, immediate ALS",
}


@dataclass(frozen=True)
class AVPUResult:
    """Structured result of an AVPU assessment."""

    level: AVPULevel

    @property
    def code(self) -> str:
        return self.level.value

    @property
    def label(self) -> str:
        return self.level.name.title()

    @property
    def description(self) -> str:
        return _DESCRIPTIONS[self.level]

    @property
    def recommended_action(self) -> str:
        return _ACTIONS[self.level]

    @property
    def gcs_equivalent(self) -> str:
        return _GCS_EQUIVALENT[self.level]

    @property
    def is_critical(self) -> bool:
        """True if the level indicates a critical / life-threatening state."""
        return self.level in (AVPULevel.PAIN, AVPULevel.UNRESPONSIVE)

    def __str__(self) -> str:
        return (
            f"AVPU: {self.code} — {self.label}\n"
            f"  {self.description}\n"
            f"  GCS equivalent: {self.gcs_equivalent}\n"
            f"  Action: {self.recommended_action}"
        )


def score_avpu(level: str | AVPULevel) -> AVPUResult:
    """Score AVPU level of consciousness.

    Parameters
    ----------
    level: One of 'A', 'V', 'P', 'U'  (case-insensitive) or an AVPULevel enum.

    Returns
    -------
    AVPUResult with description, GCS equivalent, and recommended action.

    Raises
    ------
    ValueError if level is not a recognised AVPU code.

    Examples
    --------
    >>> r = score_avpu("A")
    >>> r.is_critical
    False
    >>> r = score_avpu("P")
    >>> r.is_critical
    True
    """
    if isinstance(level, AVPULevel):
        return AVPUResult(level=level)

    normalised = str(level).strip().upper()
    try:
        avpu_level = AVPULevel(normalised)
    except ValueError:
        raise ValueError(
            f"AVPU level must be one of 'A', 'V', 'P', 'U', got {level!r}"
        ) from None

    return AVPUResult(level=avpu_level)
