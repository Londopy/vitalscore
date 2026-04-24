"""qSOFA — quick Sequential Organ Failure Assessment.

qSOFA is a bedside score for rapidly identifying patients with suspected
infection who are at high risk for sepsis-related complications.

Three binary criteria (each = 1 point):
  1. Altered mental status   (GCS < 15)
  2. Respiratory rate        ≥ 22 breaths/min
  3. Systolic BP             ≤ 100 mmHg

Score ≥ 2 prompts urgent evaluation for sepsis and consideration of ICU care.

Reference: Singer M et al. JAMA. 2016;315(8):801-810.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class qSOFAResult:
    """Structured result of a qSOFA assessment."""

    gcs: int             # Full GCS total (3–15)
    respiratory_rate: int   # breaths/min
    systolic_bp: int        # mmHg

    # Computed flags
    altered_mentation: bool = field(init=False)
    high_rr: bool           = field(init=False)
    low_sbp: bool           = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "altered_mentation", self.gcs < 15)
        object.__setattr__(self, "high_rr",           self.respiratory_rate >= 22)
        object.__setattr__(self, "low_sbp",           self.systolic_bp <= 100)

    @property
    def total(self) -> int:
        return int(self.altered_mentation) + int(self.high_rr) + int(self.low_sbp)

    @property
    def sepsis_alert(self) -> bool:
        """True when qSOFA ≥ 2 → suspected sepsis, escalate urgently."""
        return self.total >= 2

    @property
    def interpretation(self) -> str:
        t = self.total
        if t == 0:
            return f"qSOFA {t}/3 — Low risk. Sepsis unlikely on current parameters."
        if t == 1:
            return (
                f"qSOFA {t}/3 — Borderline. One criterion met; "
                f"continue close monitoring and reassess."
            )
        return (
            f"qSOFA {t}/3 — SEPSIS ALERT. ≥2 criteria met. "
            f"Urgent full SOFA assessment, blood cultures, lactate. "
            f"Consider ICU/HDU referral and early sepsis bundle."
        )

    def __str__(self) -> str:
        return (
            f"qSOFA: {self.total}/3  {'⚠ SEPSIS ALERT' if self.sepsis_alert else ''}\n"
            f"  Altered mentation (GCS {self.gcs} < 15): {'✓' if self.altered_mentation else '✗'}\n"
            f"  Respiratory rate  ({self.respiratory_rate}/min ≥ 22): {'✓' if self.high_rr else '✗'}\n"
            f"  Systolic BP       ({self.systolic_bp} mmHg ≤ 100):  {'✓' if self.low_sbp else '✗'}\n"
            f"  → {self.interpretation}"
        )


def score_qsofa(
    gcs: int,
    respiratory_rate: int,
    systolic_bp: int,
) -> qSOFAResult:
    """Calculate qSOFA score.

    Parameters
    ----------
    gcs:              Glasgow Coma Scale total (3–15)
    respiratory_rate: Breaths per minute
    systolic_bp:      Systolic blood pressure in mmHg

    Returns
    -------
    qSOFAResult with individual flags, total, and interpretation.

    Raises
    ------
    ValueError for out-of-range inputs.

    Examples
    --------
    >>> r = score_qsofa(gcs=15, respiratory_rate=16, systolic_bp=118)
    >>> r.total
    0
    >>> r.sepsis_alert
    False

    >>> r = score_qsofa(gcs=13, respiratory_rate=24, systolic_bp=95)
    >>> r.total
    3
    >>> r.sepsis_alert
    True
    """
    if not (3 <= gcs <= 15):
        raise ValueError(f"GCS must be 3–15, got {gcs!r}")
    if not (0 < respiratory_rate < 100):
        raise ValueError(f"respiratory_rate must be 1–99, got {respiratory_rate!r}")
    if not (0 < systolic_bp < 300):
        raise ValueError(f"systolic_bp must be 1–299, got {systolic_bp!r}")

    return qSOFAResult(
        gcs=gcs,
        respiratory_rate=respiratory_rate,
        systolic_bp=systolic_bp,
    )
