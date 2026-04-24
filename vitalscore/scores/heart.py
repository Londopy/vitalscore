"""HEART score — risk stratification for acute chest pain.

HEART estimates the probability of a major adverse cardiac event (MACE)
within 6 weeks in patients presenting with chest pain.

Five domains (each scored 0, 1, or 2):
  H — History          suspicious narrative for ACS
  E — ECG              LBBB, ST changes, non-specific changes
  A — Age              < 45 / 45–65 / > 65
  R — Risk factors     HTN, hypercholesterolaemia, DM, obesity, smoking,
                       family history, atherosclerotic disease
  T — Troponin         ≤ normal limit / 1–3× ULN / > 3× ULN

Risk stratification
-------------------
  0–3:  Low  (~1.7% MACE) — safe for early discharge with outpatient follow-up
  4–6:  Moderate (~12% MACE) — observe, serial troponins, cardiology input
  7–10: High (~65% MACE) — early invasive strategy, urgent cardiology review

Reference: Six AJ et al. Neth Heart J. 2008;16(6):191-196.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum


class HistoryScore(IntEnum):
    """H — History of chest pain."""
    SLIGHTLY_SUSPICIOUS  = 0   # mostly non-cardiac features
    MODERATELY_SUSPICIOUS = 1  # mix of cardiac and non-cardiac features
    HIGHLY_SUSPICIOUS    = 2   # predominantly ACS features


class ECGScore(IntEnum):
    """E — ECG findings."""
    NORMAL             = 0
    NON_SPECIFIC_CHANGE = 1  # LBBB, repolarisation disturbance, pacemaker rhythm
    SIGNIFICANT_ST_DEV  = 2  # significant ST deviation not due to LBBB/LVH/repol


class AgeScore(IntEnum):
    """A — Age."""
    UNDER_45  = 0
    AGE_45_64 = 1
    AGE_65_UP = 2


class RiskFactorScore(IntEnum):
    """R — Known risk factors or atherosclerotic disease.

    Risk factors counted: HTN, hypercholesterolaemia, DM, obesity (BMI >30),
    current/recent smoking, positive family history.
    """
    NO_RISK_FACTORS  = 0   # no known risk factors
    ONE_TWO_FACTORS  = 1   # 1–2 risk factors
    THREE_OR_MORE_OR_KNOWN_DISEASE = 2  # ≥3 risk factors OR known atherosclerotic disease


class TroponinScore(IntEnum):
    """T — Troponin (relative to institution's upper limit of normal, ULN)."""
    NORMAL         = 0   # ≤ ULN
    ONE_TO_THREE   = 1   # > 1× and ≤ 3× ULN
    ABOVE_THREE    = 2   # > 3× ULN


@dataclass(frozen=True)
class HEARTResult:
    """Structured result of a HEART score assessment."""

    history:     HistoryScore
    ecg:         ECGScore
    age:         AgeScore
    risk_factors: RiskFactorScore
    troponin:    TroponinScore

    @property
    def total(self) -> int:
        return int(self.history) + int(self.ecg) + int(self.age) + int(self.risk_factors) + int(self.troponin)

    @property
    def risk_category(self) -> str:
        t = self.total
        if t <= 3:
            return "Low"
        if t <= 6:
            return "Moderate"
        return "High"

    @property
    def mace_probability(self) -> str:
        t = self.total
        if t <= 3:
            return "~1.7%"
        if t <= 6:
            return "~12–17%"
        return "~50–65%"

    @property
    def interpretation(self) -> str:
        t = self.total
        cat = self.risk_category
        prob = self.mace_probability
        if cat == "Low":
            return (
                f"HEART {t}/10 — LOW risk ({prob} MACE). "
                f"Consider early discharge with outpatient follow-up. "
                f"No further troponins likely needed."
            )
        if cat == "Moderate":
            return (
                f"HEART {t}/10 — MODERATE risk ({prob} MACE). "
                f"Observe, serial troponins at 3h/6h. "
                f"Cardiology review before disposition."
            )
        return (
            f"HEART {t}/10 — HIGH risk ({prob} MACE). "
            f"Early invasive strategy. Urgent cardiology review. "
            f"Likely admission for angiography."
        )

    def __str__(self) -> str:
        return (
            f"HEART Score: {self.total}/10  [{self.risk_category} risk]\n"
            f"  H — History:      {int(self.history)}/2  ({self.history.name.replace('_', ' ').title()})\n"
            f"  E — ECG:          {int(self.ecg)}/2  ({self.ecg.name.replace('_', ' ').title()})\n"
            f"  A — Age:          {int(self.age)}/2  ({self.age.name.replace('_', ' ').title()})\n"
            f"  R — Risk factors: {int(self.risk_factors)}/2  ({self.risk_factors.name.replace('_', ' ').title()})\n"
            f"  T — Troponin:     {int(self.troponin)}/2  ({self.troponin.name.replace('_', ' ').title()})\n"
            f"  MACE probability: {self.mace_probability}\n"
            f"  → {self.interpretation}"
        )


def score_heart(
    history: int | HistoryScore,
    ecg: int | ECGScore,
    age: int | AgeScore,
    risk_factors: int | RiskFactorScore,
    troponin: int | TroponinScore,
) -> HEARTResult:
    """Calculate HEART score.

    Each parameter accepts either an integer (0–2) or the typed enum.

    Parameters
    ----------
    history:      History score      (0 = slightly suspicious, 1 = moderate, 2 = highly suspicious)
    ecg:          ECG score          (0 = normal, 1 = non-specific, 2 = significant ST deviation)
    age:          Age score          (0 = <45, 1 = 45–64, 2 = ≥65)
    risk_factors: Risk factor score  (0 = none, 1 = 1–2 factors, 2 = ≥3 or known disease)
    troponin:     Troponin score     (0 = ≤ULN, 1 = 1–3×ULN, 2 = >3×ULN)

    Returns
    -------
    HEARTResult with total, risk category, and interpretation.

    Raises
    ------
    ValueError if any component is outside 0–2.

    Examples
    --------
    >>> r = score_heart(history=2, ecg=2, age=2, risk_factors=2, troponin=2)
    >>> r.total
    10
    >>> r.risk_category
    'High'

    >>> r = score_heart(history=0, ecg=0, age=0, risk_factors=0, troponin=0)
    >>> r.risk_category
    'Low'
    """
    def _coerce(name: str, value: int | object, cls: type) -> object:
        if isinstance(value, cls):
            return value
        try:
            return cls(int(value))
        except ValueError:
            valid = [e.value for e in cls]
            raise ValueError(f"{name} must be one of {valid}, got {value!r}") from None

    return HEARTResult(
        history=_coerce("history", history, HistoryScore),
        ecg=_coerce("ecg", ecg, ECGScore),
        age=_coerce("age", age, AgeScore),
        risk_factors=_coerce("risk_factors", risk_factors, RiskFactorScore),
        troponin=_coerce("troponin", troponin, TroponinScore),
    )
