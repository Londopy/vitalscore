"""
vitalscore — Clinical scoring calculators for Python.

Quick start
-----------
>>> from vitalscore.scores import score_gcs, score_avpu, score_apgar
>>> from vitalscore.scores import score_start, score_news2, score_qsofa, score_heart
>>> from vitalscore.batch import batch_triage
>>> from vitalscore.models import OPQRST, SAMPLE, CUPS
"""

from vitalscore.scores.gcs import GCSResult, score_gcs
from vitalscore.scores.avpu import AVPUResult, score_avpu
from vitalscore.scores.apgar import APGARResult, score_apgar
from vitalscore.scores.start import STARTResult, score_start
from vitalscore.scores.news2 import NEWS2Result, score_news2
from vitalscore.scores.qsofa import qSOFAResult, score_qsofa
from vitalscore.scores.heart import HEARTResult, score_heart
from vitalscore.models.assessment import CUPS, OPQRST, SAMPLE, CUPSCategory
from vitalscore.batch import batch_triage, TriagePatient

__all__ = [
    # scores
    "score_gcs", "GCSResult",
    "score_avpu", "AVPUResult",
    "score_apgar", "APGARResult",
    "score_start", "STARTResult",
    "score_news2", "NEWS2Result",
    "score_qsofa", "qSOFAResult",
    "score_heart", "HEARTResult",
    # models
    "CUPS", "CUPSCategory",
    "OPQRST",
    "SAMPLE",
    # batch
    "batch_triage", "TriagePatient",
]

__version__ = "0.1.0"
