"""NEWS2 — National Early Warning Score 2 calculator.

NEWS2 is a validated early-warning scoring system that aggregates seven
physiological parameters into a risk score for clinical deterioration.

Parameters scored
-----------------
  Respiration rate  (breaths/min)
  SpO₂              (%) — two scales (standard; Scale 2 for COPD/hypercapnic failure)
  Supplemental O₂   (boolean)
  Systolic BP       (mmHg)
  Heart rate        (bpm)
  Consciousness     (ACVPU: Alert / new Confusion / Voice / Pain / Unresponsive)
  Temperature       (°C)

Risk thresholds
---------------
  0:    Low
  1–4:  Low
  5–6:  Medium — call SpR / senior review
  ≥7:   High  — urgent critical-care review
  Any single parameter = 3: Medium (escalate urgently)

Reference: Royal College of Physicians. NEWS2 (2017). https://www.rcplondon.ac.uk/news2
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class ACVPULevel(str, Enum):
    """ACVPU (Alert, Confusion, Voice, Pain, Unresponsive)."""
    ALERT        = "A"
    CONFUSION    = "C"   # new confusion — score same as V/P/U
    VOICE        = "V"
    PAIN         = "P"
    UNRESPONSIVE = "U"


class NEWS2Risk(str, Enum):
    LOW    = "Low"
    MEDIUM = "Medium"
    HIGH   = "High"


# ── sub-scores ─────────────────────────────────────────────────────────────────

def _score_respiration(rr: int) -> int:
    if rr <= 8:   return 3
    if rr <= 11:  return 1
    if rr <= 20:  return 0
    if rr <= 24:  return 2
    return 3


def _score_spo2_scale1(spo2: float) -> int:
    """Standard SpO₂ scale (non-COPD patients)."""
    if spo2 <= 91:  return 3
    if spo2 <= 93:  return 2
    if spo2 <= 95:  return 1
    return 0


def _score_spo2_scale2(spo2: float, on_oxygen: bool) -> int:
    """Scale 2 — for patients with hypercapnic respiratory failure (COPD target 88–92%)."""
    if spo2 <= 83:  return 3
    if spo2 <= 85:  return 2
    if spo2 <= 87:  return 1
    if spo2 <= 92:  return 0          # target range on air or O₂
    # ≥93% — penalise if on air (too high for their target)
    if on_oxygen:
        if spo2 <= 94:  return 1
        if spo2 <= 96:  return 2
        return 3
    # on air — same as scale 1 above target
    return 0


def _score_oxygen(on_oxygen: bool) -> int:
    return 2 if on_oxygen else 0


def _score_systolic_bp(sbp: int) -> int:
    if sbp <= 90:   return 3
    if sbp <= 100:  return 2
    if sbp <= 110:  return 1
    if sbp <= 219:  return 0
    return 3


def _score_heart_rate(hr: int) -> int:
    if hr <= 40:   return 3
    if hr <= 50:   return 1
    if hr <= 90:   return 0
    if hr <= 110:  return 1
    if hr <= 130:  return 2
    return 3


def _score_consciousness(level: ACVPULevel) -> int:
    return 0 if level == ACVPULevel.ALERT else 3


def _score_temperature(temp: float) -> int:
    if temp <= 35.0:  return 3
    if temp <= 36.0:  return 1
    if temp <= 38.0:  return 0
    if temp <= 39.0:  return 1
    return 2


@dataclass(frozen=True)
class NEWS2Result:
    """Structured result of a NEWS2 assessment."""

    # Raw inputs
    respiratory_rate: int
    spo2: float
    on_oxygen: bool
    systolic_bp: int
    heart_rate: int
    consciousness: ACVPULevel
    temperature: float
    use_spo2_scale2: bool = False

    # Sub-scores (computed at init time via __post_init__)
    rr_score: int        = field(init=False)
    spo2_score: int      = field(init=False)
    o2_score: int        = field(init=False)
    sbp_score: int       = field(init=False)
    hr_score: int        = field(init=False)
    consciousness_score: int = field(init=False)
    temp_score: int      = field(init=False)

    def __post_init__(self) -> None:
        # Use object.__setattr__ because the dataclass is frozen
        object.__setattr__(self, "rr_score",  _score_respiration(self.respiratory_rate))
        spo2_s = (
            _score_spo2_scale2(self.spo2, self.on_oxygen)
            if self.use_spo2_scale2
            else _score_spo2_scale1(self.spo2)
        )
        object.__setattr__(self, "spo2_score", spo2_s)
        object.__setattr__(self, "o2_score",   _score_oxygen(self.on_oxygen))
        object.__setattr__(self, "sbp_score",  _score_systolic_bp(self.systolic_bp))
        object.__setattr__(self, "hr_score",   _score_heart_rate(self.heart_rate))
        object.__setattr__(self, "consciousness_score", _score_consciousness(self.consciousness))
        object.__setattr__(self, "temp_score", _score_temperature(self.temperature))

    @property
    def total(self) -> int:
        return (
            self.rr_score + self.spo2_score + self.o2_score
            + self.sbp_score + self.hr_score
            + self.consciousness_score + self.temp_score
        )

    @property
    def max_single_parameter(self) -> int:
        return max(
            self.rr_score, self.spo2_score, self.o2_score,
            self.sbp_score, self.hr_score,
            self.consciousness_score, self.temp_score,
        )

    @property
    def risk(self) -> NEWS2Risk:
        if self.total >= 7:
            return NEWS2Risk.HIGH
        if self.total >= 5 or self.max_single_parameter >= 3:
            return NEWS2Risk.MEDIUM
        return NEWS2Risk.LOW

    @property
    def interpretation(self) -> str:
        t = self.total
        r = self.risk
        if r == NEWS2Risk.HIGH:
            return (
                f"NEWS2 {t} — HIGH risk. Urgent critical-care review. "
                f"Consider HDU/ICU admission."
            )
        if r == NEWS2Risk.MEDIUM:
            return (
                f"NEWS2 {t} — MEDIUM risk. Urgent SpR/senior clinician review within 1 hour. "
                f"Continuous monitoring."
            )
        return (
            f"NEWS2 {t} — LOW risk. Routine ward monitoring; "
            f"reassess within 4–6 hours or per local protocol."
        )

    def __str__(self) -> str:
        scale_label = "Scale 2 (COPD)" if self.use_spo2_scale2 else "Scale 1"
        return (
            f"NEWS2 Total: {self.total}  [{self.risk.value} risk]\n"
            f"  Respiration rate:  {self.respiratory_rate}/min  → score {self.rr_score}\n"
            f"  SpO₂ ({scale_label}): {self.spo2}%  → score {self.spo2_score}\n"
            f"  Supplemental O₂:   {'Yes' if self.on_oxygen else 'No'}  → score {self.o2_score}\n"
            f"  Systolic BP:       {self.systolic_bp} mmHg  → score {self.sbp_score}\n"
            f"  Heart rate:        {self.heart_rate} bpm  → score {self.hr_score}\n"
            f"  Consciousness:     {self.consciousness.name}  → score {self.consciousness_score}\n"
            f"  Temperature:       {self.temperature}°C  → score {self.temp_score}\n"
            f"  → {self.interpretation}"
        )


def score_news2(
    respiratory_rate: int,
    spo2: float,
    on_oxygen: bool,
    systolic_bp: int,
    heart_rate: int,
    consciousness: str | ACVPULevel,
    temperature: float,
    *,
    use_spo2_scale2: bool = False,
) -> NEWS2Result:
    """Calculate NEWS2 score.

    Parameters
    ----------
    respiratory_rate: Breaths per minute (integer, typical range 8–40)
    spo2:             Peripheral oxygen saturation (%, typical range 70–100)
    on_oxygen:        True if the patient is receiving supplemental oxygen
    systolic_bp:      Systolic blood pressure (mmHg)
    heart_rate:       Beats per minute
    consciousness:    ACVPU level — 'A', 'C', 'V', 'P', or 'U'
    temperature:      Body temperature in Celsius
    use_spo2_scale2:  Use SpO₂ Scale 2 for patients with hypercapnic
                      respiratory failure (e.g. COPD, target SpO₂ 88–92%).

    Returns
    -------
    NEWS2Result with sub-scores, total, risk level, and interpretation.

    Raises
    ------
    ValueError for out-of-range or unrecognised inputs.

    Examples
    --------
    >>> r = score_news2(18, 98.0, False, 120, 72, "A", 36.8)
    >>> r.total
    0
    >>> r.risk.value
    'Low'

    >>> r = score_news2(28, 90.0, True, 88, 115, "V", 35.0)
    >>> r.risk.value
    'High'
    """
    # Validate
    if not (0 < respiratory_rate < 100):
        raise ValueError(f"respiratory_rate must be 1–99, got {respiratory_rate!r}")
    if not (50.0 <= spo2 <= 100.0):
        raise ValueError(f"spo2 must be 50–100%, got {spo2!r}")
    if not (0 < systolic_bp < 300):
        raise ValueError(f"systolic_bp must be 1–299, got {systolic_bp!r}")
    if not (0 < heart_rate < 300):
        raise ValueError(f"heart_rate must be 1–299, got {heart_rate!r}")
    if not (25.0 <= temperature <= 45.0):
        raise ValueError(f"temperature must be 25–45°C, got {temperature!r}")

    if isinstance(consciousness, str):
        try:
            consciousness = ACVPULevel(consciousness.strip().upper())
        except ValueError:
            raise ValueError(
                f"consciousness must be one of 'A','C','V','P','U', got {consciousness!r}"
            ) from None

    return NEWS2Result(
        respiratory_rate=respiratory_rate,
        spo2=spo2,
        on_oxygen=on_oxygen,
        systolic_bp=systolic_bp,
        heart_rate=heart_rate,
        consciousness=consciousness,
        temperature=temperature,
        use_spo2_scale2=use_spo2_scale2,
    )
