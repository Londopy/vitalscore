# vitalscore

**Clinical scoring calculators for Python.**

[![PyPI version](https://img.shields.io/pypi/v/vitalscore.svg)](https://pypi.org/project/vitalscore/)
[![Python 3.10+](https://img.shields.io/pypi/pyversions/vitalscore.svg)](https://pypi.org/project/vitalscore/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

`vitalscore` provides typed, validated implementations of the clinical scoring tools used in emergency medicine, critical care, and pre-hospital settings — all exposed as clean Python dataclasses with interpretation strings built in.

---

## Scores included

| Score | Function | Description |
|---|---|---|
| GCS | `score_gcs` | Glasgow Coma Scale (3–15) |
| AVPU | `score_avpu` | Consciousness level: Alert / Voice / Pain / Unresponsive |
| APGAR | `score_apgar` | Newborn assessment (0–10) |
| START | `score_start` | Mass-casualty triage: Immediate / Delayed / Minor / Deceased |
| NEWS2 | `score_news2` | National Early Warning Score 2 (0–20) |
| qSOFA | `score_qsofa` | Sepsis screening (0–3) |
| HEART | `score_heart` | Chest pain risk stratification (0–10) |

### Assessment models

| Model | Description |
|---|---|
| `CUPS` | Critical / Unstable / Potentially unstable / Stable |
| `OPQRST` | Symptom characterisation mnemonic |
| `SAMPLE` | Patient history mnemonic |

---

## Installation

```bash
pip install vitalscore
```

Requires Python 3.10+. No external dependencies.

---

## Quick start

```python
from vitalscore import score_gcs, score_avpu, score_start, score_news2, score_qsofa, score_heart
from vitalscore import OPQRST, SAMPLE, CUPS, CUPSCategory
from vitalscore import batch_triage, TriagePatient
```

### GCS — Glasgow Coma Scale

```python
result = score_gcs(eye=2, verbal=1, motor=3)

result.total        # 6
result.severity     # "Severe TBI"
result.interpretation
# "Severe TBI (GCS 6) — critical, consider intubation and ICU"

print(result)
# GCS 6/15  [E2 V1 M3]
#   Eye:    2 — Eye opening to pain
#   Verbal: 1 — No verbal response
#   Motor:  3 — Flexion to pain (decorticate)
#   → Severe TBI (GCS 6) — critical, consider intubation and ICU
```

### AVPU — Consciousness scale

```python
result = score_avpu("P")      # also accepts AVPULevel enum

result.is_critical    # True
result.gcs_equivalent # "GCS ~8 (estimated)"
result.recommended_action
# "Immediate intervention; manage airway, IV access, call for help"
```

### APGAR — Newborn score

```python
result = score_apgar(appearance=2, pulse=2, grimace=1, activity=1, respiration=2)

result.total     # 8
result.category  # "Normal"
```

### START — Mass-casualty triage

```python
# Walking wounded → Minor (Green)
score_start(can_walk=True, respiratory_rate=18).priority
# <STARTPriority.MINOR: 'Minor'>

# Apnoeic → Deceased (Black)
score_start(can_walk=False, respiratory_rate=None).priority
# <STARTPriority.DECEASED: 'Deceased'>

# RR > 30 → Immediate (Red)
score_start(can_walk=False, respiratory_rate=35).priority
# <STARTPriority.IMMEDIATE: 'Immediate'>

# All OK → Delayed (Yellow)
score_start(
    can_walk=False, respiratory_rate=20,
    has_radial_pulse=True, follows_commands=True
).priority
# <STARTPriority.DELAYED: 'Delayed'>
```

### NEWS2 — National Early Warning Score 2

```python
result = score_news2(
    respiratory_rate=22,
    spo2=94.0,
    on_oxygen=False,
    systolic_bp=105,
    heart_rate=98,
    consciousness="A",   # ACVPU: A / C / V / P / U
    temperature=37.2,
)

result.total        # 5
result.risk.value   # "Medium"
result.interpretation
# "NEWS2 5 — MEDIUM risk. Urgent SpR/senior clinician review within 1 hour."

# For COPD patients (SpO₂ target 88–92%), use Scale 2:
result = score_news2(..., use_spo2_scale2=True)
```

### qSOFA — Sepsis screening

```python
result = score_qsofa(gcs=13, respiratory_rate=24, systolic_bp=95)

result.total         # 3
result.sepsis_alert  # True
result.interpretation
# "qSOFA 3/3 — SEPSIS ALERT. Urgent full SOFA assessment, blood cultures, lactate."
```

### HEART — Chest pain risk

```python
from vitalscore.scores.heart import HistoryScore, ECGScore, AgeScore, RiskFactorScore, TroponinScore

result = score_heart(
    history=HistoryScore.HIGHLY_SUSPICIOUS,
    ecg=ECGScore.SIGNIFICANT_ST_DEV,
    age=AgeScore.AGE_65_UP,
    risk_factors=RiskFactorScore.THREE_OR_MORE_OR_KNOWN_DISEASE,
    troponin=TroponinScore.ABOVE_THREE,
)
# or pass plain integers 0–2 for each field

result.total            # 10
result.risk_category    # "High"
result.mace_probability # "~50–65%"
```

---

## Assessment models

### CUPS — Transport priority

```python
from vitalscore import CUPS, CUPSCategory

c = CUPS(category=CUPSCategory.CRITICAL, chief_complaint="Unresponsive, no pulse")
c.transport_priority   # 1
c.description          # "Life-threatening condition. Immediate intervention required..."

# String input also accepted:
CUPS(category="Unstable")
```

### OPQRST — Symptom characterisation

```python
from vitalscore import OPQRST

pain = OPQRST(
    onset="Sudden, during exertion",
    quality="Crushing pressure",
    radiation="Radiates to left arm and jaw",
    severity=9,          # 0–10 NRS
    time="30 minutes",
    associated="Diaphoresis, nausea",
)
print(pain.summary)
```

### SAMPLE — Patient history

```python
from vitalscore import SAMPLE

history = SAMPLE(
    signs_symptoms="Crushing chest pain, diaphoresis",
    allergies="Penicillin (anaphylaxis)",
    medications="Aspirin 81 mg, Metformin 500 mg BD",
    pertinent_history="HTN, T2DM, previous MI 2019",
    last_oral_intake="6 hours ago",
    events="Onset at rest, watching TV",
)

history.has_allergies   # True
print(history)
```

---

## Batch triage

Score a list of patients and receive them sorted from most to least critical.

```python
from vitalscore import batch_triage, TriagePatient
from vitalscore.batch import format_triage_report

patients = [
    TriagePatient("P1", can_walk=True,  respiratory_rate=18),
    TriagePatient("P2", can_walk=False, respiratory_rate=35),
    TriagePatient("P3", can_walk=False, respiratory_rate=None),   # apnoeic
    TriagePatient("P4", can_walk=False, respiratory_rate=20,
                  has_radial_pulse=True, follows_commands=True),
]

sorted_pts = batch_triage(patients, method="start")
# → [P2 (Immediate), P4 (Delayed), P1 (Minor), P3 (Deceased)]

print(format_triage_report(sorted_pts))
```

For NEWS2 batch scoring, populate the NEWS2 fields (`spo2`, `on_oxygen`,
`systolic_bp`, `heart_rate`, `consciousness`, `temperature`) and pass `method="news2"`.
Use `method="both"` to run both algorithms simultaneously.

---

## CLI

Every score is accessible from the terminal:

```bash
# GCS
vitalscore gcs --eye 2 --verbal 1 --motor 3

# AVPU
vitalscore avpu --level P

# APGAR
vitalscore apgar --appearance 2 --pulse 2 --grimace 1 --activity 1 --respiration 2

# START triage
vitalscore start --no-walk --rr 35
vitalscore start --no-walk --rr 20 --pulse --follows-commands

# NEWS2
vitalscore news2 --rr 22 --spo2 94 --no-o2 --sbp 105 --hr 98 --acvpu A --temp 37.2
vitalscore news2 --rr 10 --spo2 89 --o2 --sbp 90 --hr 115 --acvpu V --temp 35.0 --scale2

# qSOFA
vitalscore qsofa --gcs 13 --rr 24 --sbp 95

# HEART
vitalscore heart --history 2 --ecg 1 --age 2 --risk 2 --troponin 1
```

Output is ANSI-coloured when run in a terminal (red for critical, yellow for urgent, green for low risk).

---

## Input validation

All `score_*` functions raise a `ValueError` with a clear message if any input is out of range:

```python
score_gcs(eye=0, verbal=5, motor=6)
# ValueError: Eye opening must be 1–4, got 0

score_news2(respiratory_rate=18, spo2=110.0, ...)
# ValueError: spo2 must be 50–100%, got 110.0
```

---

## Project layout

```
vitalscore/
├── vitalscore/
│   ├── scores/        # gcs.py  avpu.py  apgar.py  start.py
│   │                  # news2.py  qsofa.py  heart.py
│   ├── models/        # assessment.py  (CUPS, OPQRST, SAMPLE)
│   ├── batch.py       # batch_triage, TriagePatient, format_triage_report
│   └── cli.py         # vitalscore CLI entry point
└── tests/
    └── test_scores.py # 80 unit tests
```

---

## Contributing

Pull requests are welcome. Please run the test suite before submitting:

```bash
pip install -e ".[dev]"
pytest
```

---

## Disclaimer

`vitalscore` is a software tool intended to **support** clinical decision-making, not replace it. Always defer to qualified medical professionals and local clinical guidelines. The authors accept no liability for patient outcomes.

---

## License

MIT © 2026
