"""Clinical scoring sub-package."""

from vitalscore.scores.gcs import GCSResult, score_gcs
from vitalscore.scores.avpu import AVPUResult, score_avpu
from vitalscore.scores.apgar import APGARResult, score_apgar
from vitalscore.scores.start import STARTResult, score_start
from vitalscore.scores.news2 import NEWS2Result, score_news2
from vitalscore.scores.qsofa import qSOFAResult, score_qsofa
from vitalscore.scores.heart import HEARTResult, score_heart

__all__ = [
    "score_gcs", "GCSResult",
    "score_avpu", "AVPUResult",
    "score_apgar", "APGARResult",
    "score_start", "STARTResult",
    "score_news2", "NEWS2Result",
    "score_qsofa", "qSOFAResult",
    "score_heart", "HEARTResult",
]
