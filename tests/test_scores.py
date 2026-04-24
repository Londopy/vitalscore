"""Tests for vitalscore clinical scoring library."""

import pytest
from vitalscore.scores.gcs import score_gcs
from vitalscore.scores.avpu import score_avpu, AVPULevel
from vitalscore.scores.apgar import score_apgar
from vitalscore.scores.start import score_start, STARTPriority
from vitalscore.scores.news2 import score_news2, NEWS2Risk, ACVPULevel
from vitalscore.scores.qsofa import score_qsofa
from vitalscore.scores.heart import score_heart
from vitalscore.models.assessment import CUPS, CUPSCategory, OPQRST, SAMPLE
from vitalscore.batch import TriagePatient, batch_triage


# ═══════════════════════════════════════════════════════════════════════════════
# GCS
# ═══════════════════════════════════════════════════════════════════════════════

class TestGCS:
    def test_perfect_score(self):
        r = score_gcs(4, 5, 6)
        assert r.total == 15
        assert r.severity == "Mild TBI"

    def test_mild_tbi(self):
        r = score_gcs(4, 5, 4)  # total 13
        assert r.total == 13
        assert r.severity == "Mild TBI"

    def test_moderate_tbi(self):
        r = score_gcs(3, 3, 3)  # total 9
        assert r.severity == "Moderate TBI"

    def test_moderate_tbi_boundary(self):
        r = score_gcs(2, 4, 3)  # total 9
        assert r.severity == "Moderate TBI"
        r2 = score_gcs(3, 3, 6)  # total 12
        assert r2.severity == "Moderate TBI"

    def test_severe_tbi(self):
        r = score_gcs(1, 1, 1)
        assert r.total == 3
        assert r.severity == "Severe TBI"

    def test_descriptors(self):
        r = score_gcs(1, 1, 1)
        assert "No eye opening" in r.eye_descriptor
        assert "No verbal" in r.verbal_descriptor
        assert "No motor" in r.motor_descriptor

    def test_invalid_eye(self):
        with pytest.raises(ValueError, match="Eye opening"):
            score_gcs(0, 5, 6)

    def test_invalid_verbal(self):
        with pytest.raises(ValueError, match="Verbal"):
            score_gcs(4, 6, 6)

    def test_invalid_motor(self):
        with pytest.raises(ValueError, match="Motor"):
            score_gcs(4, 5, 7)

    def test_str_contains_total(self):
        assert "15/15" in str(score_gcs(4, 5, 6))


# ═══════════════════════════════════════════════════════════════════════════════
# AVPU
# ═══════════════════════════════════════════════════════════════════════════════

class TestAVPU:
    @pytest.mark.parametrize("level,expected_critical", [
        ("A", False), ("V", False), ("P", True), ("U", True),
    ])
    def test_is_critical(self, level, expected_critical):
        r = score_avpu(level)
        assert r.is_critical == expected_critical

    def test_enum_input(self):
        r = score_avpu(AVPULevel.PAIN)
        assert r.code == "P"

    def test_case_insensitive(self):
        r = score_avpu("a")
        assert r.code == "A"

    def test_invalid_level(self):
        with pytest.raises(ValueError):
            score_avpu("X")

    def test_gcs_equivalent_alert(self):
        r = score_avpu("A")
        assert "15" in r.gcs_equivalent

    def test_gcs_equivalent_unresponsive(self):
        r = score_avpu("U")
        assert "3" in r.gcs_equivalent


# ═══════════════════════════════════════════════════════════════════════════════
# APGAR
# ═══════════════════════════════════════════════════════════════════════════════

class TestAPGAR:
    def test_perfect_score(self):
        r = score_apgar(2, 2, 2, 2, 2)
        assert r.total == 10
        assert r.category == "Normal"

    def test_critical_score(self):
        r = score_apgar(0, 0, 0, 0, 0)
        assert r.total == 0
        assert "Immediate" in r.category

    def test_moderate(self):
        r = score_apgar(1, 1, 1, 1, 1)
        assert r.total == 5
        assert r.category == "Moderate concern"

    def test_boundary_normal_lower(self):
        r = score_apgar(2, 2, 1, 1, 1)  # total 7
        assert r.category == "Normal"

    def test_boundary_moderate_upper(self):
        r = score_apgar(1, 1, 1, 1, 2)  # total 6
        assert r.category == "Moderate concern"

    def test_invalid_component(self):
        with pytest.raises(ValueError):
            score_apgar(3, 2, 2, 2, 2)

    def test_invalid_negative(self):
        with pytest.raises(ValueError):
            score_apgar(2, -1, 2, 2, 2)


# ═══════════════════════════════════════════════════════════════════════════════
# START
# ═══════════════════════════════════════════════════════════════════════════════

class TestSTART:
    def test_walking_is_minor(self):
        r = score_start(can_walk=True, respiratory_rate=18)
        assert r.priority == STARTPriority.MINOR
        assert r.colour == "Green"

    def test_apnoeic_is_deceased(self):
        r = score_start(can_walk=False, respiratory_rate=None)
        assert r.priority == STARTPriority.DECEASED
        assert r.colour == "Black"

    def test_high_rr_is_immediate(self):
        r = score_start(can_walk=False, respiratory_rate=31)
        assert r.priority == STARTPriority.IMMEDIATE
        assert r.colour == "Red"

    def test_no_radial_pulse_is_immediate(self):
        r = score_start(can_walk=False, respiratory_rate=20, has_radial_pulse=False)
        assert r.priority == STARTPriority.IMMEDIATE

    def test_slow_cap_refill_is_immediate(self):
        r = score_start(can_walk=False, respiratory_rate=20, cap_refill_seconds=3.0)
        assert r.priority == STARTPriority.IMMEDIATE

    def test_no_commands_is_immediate(self):
        r = score_start(
            can_walk=False, respiratory_rate=20,
            has_radial_pulse=True, follows_commands=False
        )
        assert r.priority == STARTPriority.IMMEDIATE

    def test_all_ok_is_delayed(self):
        r = score_start(
            can_walk=False, respiratory_rate=20,
            has_radial_pulse=True, follows_commands=True
        )
        assert r.priority == STARTPriority.DELAYED
        assert r.colour == "Yellow"

    def test_rr_boundary_30_is_ok(self):
        r = score_start(can_walk=False, respiratory_rate=30,
                        has_radial_pulse=True, follows_commands=True)
        assert r.priority == STARTPriority.DELAYED

    def test_rr_boundary_31_is_immediate(self):
        r = score_start(can_walk=False, respiratory_rate=31)
        assert r.priority == STARTPriority.IMMEDIATE

    def test_invalid_rr(self):
        with pytest.raises(ValueError):
            score_start(can_walk=False, respiratory_rate=150)

    def test_sort_order(self):
        from vitalscore.scores.start import STARTPriority, _SORT_ORDER
        assert _SORT_ORDER[STARTPriority.IMMEDIATE] < _SORT_ORDER[STARTPriority.DELAYED]
        assert _SORT_ORDER[STARTPriority.DELAYED] < _SORT_ORDER[STARTPriority.MINOR]


# ═══════════════════════════════════════════════════════════════════════════════
# NEWS2
# ═══════════════════════════════════════════════════════════════════════════════

class TestNEWS2:
    def test_all_normal(self):
        r = score_news2(18, 98.0, False, 120, 72, "A", 36.8)
        assert r.total == 0
        assert r.risk == NEWS2Risk.LOW

    def test_high_risk(self):
        # Multiple extreme parameters → total ≥ 7
        r = score_news2(28, 90.0, True, 85, 120, "V", 35.0)
        assert r.risk == NEWS2Risk.HIGH

    def test_single_parameter_3_triggers_medium(self):
        # RR ≤ 8 → score 3, rest normal
        r = score_news2(8, 98.0, False, 120, 72, "A", 36.8)
        assert r.rr_score == 3
        assert r.risk == NEWS2Risk.MEDIUM

    def test_consciousness_v_scores_3(self):
        r = score_news2(18, 98.0, False, 120, 72, "V", 36.8)
        assert r.consciousness_score == 3

    def test_consciousness_a_scores_0(self):
        r = score_news2(18, 98.0, False, 120, 72, "A", 36.8)
        assert r.consciousness_score == 0

    def test_new_confusion_c_scores_3(self):
        r = score_news2(18, 98.0, False, 120, 72, "C", 36.8)
        assert r.consciousness_score == 3

    def test_supplemental_o2_adds_2(self):
        r1 = score_news2(18, 98.0, False, 120, 72, "A", 36.8)
        r2 = score_news2(18, 98.0, True,  120, 72, "A", 36.8)
        assert r2.total == r1.total + 2

    def test_spo2_scale2_flag(self):
        # Scale 2 scoring shouldn't crash
        r = score_news2(18, 91.0, False, 120, 72, "A", 36.8, use_spo2_scale2=True)
        assert isinstance(r.total, int)

    def test_invalid_spo2(self):
        with pytest.raises(ValueError):
            score_news2(18, 110.0, False, 120, 72, "A", 36.8)

    def test_invalid_consciousness(self):
        with pytest.raises(ValueError):
            score_news2(18, 98.0, False, 120, 72, "X", 36.8)

    def test_sbp_above_219_scores_3(self):
        r = score_news2(18, 98.0, False, 220, 72, "A", 36.8)
        assert r.sbp_score == 3


# ═══════════════════════════════════════════════════════════════════════════════
# qSOFA
# ═══════════════════════════════════════════════════════════════════════════════

class TestqSOFA:
    def test_zero_score(self):
        r = score_qsofa(gcs=15, respiratory_rate=16, systolic_bp=120)
        assert r.total == 0
        assert not r.sepsis_alert

    def test_all_three(self):
        r = score_qsofa(gcs=13, respiratory_rate=24, systolic_bp=95)
        assert r.total == 3
        assert r.sepsis_alert

    def test_two_triggers_alert(self):
        r = score_qsofa(gcs=14, respiratory_rate=24, systolic_bp=120)
        assert r.total == 2
        assert r.sepsis_alert

    def test_gcs_15_no_mentation_flag(self):
        r = score_qsofa(gcs=15, respiratory_rate=22, systolic_bp=100)
        assert not r.altered_mentation
        assert r.high_rr
        assert r.low_sbp
        assert r.total == 2

    def test_rr_boundary_22(self):
        r_low  = score_qsofa(15, 21, 120)
        r_high = score_qsofa(15, 22, 120)
        assert not r_low.high_rr
        assert r_high.high_rr

    def test_sbp_boundary_100(self):
        r_low  = score_qsofa(15, 16, 100)
        r_high = score_qsofa(15, 16, 101)
        assert r_low.low_sbp
        assert not r_high.low_sbp

    def test_invalid_gcs(self):
        with pytest.raises(ValueError):
            score_qsofa(gcs=2, respiratory_rate=18, systolic_bp=120)


# ═══════════════════════════════════════════════════════════════════════════════
# HEART
# ═══════════════════════════════════════════════════════════════════════════════

class TestHEART:
    def test_all_zero(self):
        r = score_heart(0, 0, 0, 0, 0)
        assert r.total == 0
        assert r.risk_category == "Low"

    def test_all_two(self):
        r = score_heart(2, 2, 2, 2, 2)
        assert r.total == 10
        assert r.risk_category == "High"

    def test_moderate_boundary(self):
        r = score_heart(1, 1, 1, 1, 0)  # 4
        assert r.risk_category == "Moderate"
        r2 = score_heart(1, 1, 2, 1, 1)  # 6
        assert r2.risk_category == "Moderate"

    def test_mace_probability_low(self):
        r = score_heart(0, 0, 0, 0, 1)  # 1
        assert "1.7%" in r.mace_probability

    def test_mace_probability_high(self):
        r = score_heart(2, 2, 2, 2, 2)
        assert "65%" in r.mace_probability or "50%" in r.mace_probability

    def test_invalid_score(self):
        with pytest.raises(ValueError):
            score_heart(3, 0, 0, 0, 0)

    def test_typed_enum_inputs(self):
        from vitalscore.scores.heart import HistoryScore, ECGScore, AgeScore, RiskFactorScore, TroponinScore
        r = score_heart(
            HistoryScore.HIGHLY_SUSPICIOUS,
            ECGScore.SIGNIFICANT_ST_DEV,
            AgeScore.AGE_65_UP,
            RiskFactorScore.THREE_OR_MORE_OR_KNOWN_DISEASE,
            TroponinScore.ABOVE_THREE,
        )
        assert r.total == 10


# ═══════════════════════════════════════════════════════════════════════════════
# Assessment Models
# ═══════════════════════════════════════════════════════════════════════════════

class TestCUPS:
    def test_critical(self):
        c = CUPS(category=CUPSCategory.CRITICAL, chief_complaint="Cardiac arrest")
        assert c.transport_priority == 1
        assert "Life-threatening" in c.description

    def test_stable(self):
        c = CUPS(category=CUPSCategory.STABLE)
        assert c.transport_priority == 4

    def test_string_category(self):
        c = CUPS(category="Unstable")
        assert c.category == CUPSCategory.UNSTABLE

    def test_case_insensitive_category(self):
        c = CUPS(category="stable")
        assert c.category == CUPSCategory.STABLE

    def test_invalid_category(self):
        with pytest.raises(ValueError):
            CUPS(category="Dying")


class TestOPQRST:
    def test_all_fields(self):
        o = OPQRST(
            onset="Sudden",
            quality="Crushing",
            radiation="Left arm",
            severity=8,
        )
        assert o.severity == 8
        s = o.summary
        assert "Sudden" in s
        assert "8/10" in s

    def test_invalid_severity(self):
        with pytest.raises(ValueError):
            OPQRST(severity=11)

    def test_none_fields_in_summary(self):
        o = OPQRST()
        assert "(not recorded)" in o.summary


class TestSAMPLE:
    def test_basic(self):
        h = SAMPLE(
            signs_symptoms="SOB",
            allergies="Penicillin",
            medications="Aspirin",
        )
        assert h.has_allergies is True

    def test_nkda(self):
        h = SAMPLE(allergies="NKDA")
        assert h.has_allergies is False

    def test_no_allergies_flag(self):
        h = SAMPLE(allergies="none")
        assert h.has_allergies is False

    def test_summary_contains_fields(self):
        h = SAMPLE(signs_symptoms="Chest pain", events="At rest")
        s = h.summary
        assert "Chest pain" in s
        assert "At rest" in s


# ═══════════════════════════════════════════════════════════════════════════════
# Batch Triage
# ═══════════════════════════════════════════════════════════════════════════════

class TestBatchTriage:
    def _make_patients(self):
        return [
            TriagePatient("Minor",    can_walk=True,  respiratory_rate=18),
            TriagePatient("Immediate",can_walk=False, respiratory_rate=35),
            TriagePatient("Deceased", can_walk=False, respiratory_rate=None),
            TriagePatient("Delayed",  can_walk=False, respiratory_rate=20,
                          has_radial_pulse=True, follows_commands=True),
        ]

    def test_sort_order(self):
        pts = self._make_patients()
        result = batch_triage(pts, method="start")
        priorities = [p.start_priority for p in result]
        assert priorities[0] == STARTPriority.IMMEDIATE
        assert priorities[1] == STARTPriority.DELAYED
        assert priorities[2] == STARTPriority.MINOR
        assert priorities[3] == STARTPriority.DECEASED

    def test_results_populated(self):
        pts = self._make_patients()
        result = batch_triage(pts, method="start")
        for p in result:
            assert p.start_result is not None

    def test_missing_field_recorded_as_error(self):
        pts = [TriagePatient("NoWalk")]  # can_walk is None
        result = batch_triage(pts, method="start")
        assert result[0].errors
        assert "can_walk" in result[0].errors[0]

    def test_news2_batch(self):
        pts = [
            TriagePatient(
                "Sick",
                respiratory_rate=28, spo2=90.0, on_oxygen=True,
                systolic_bp=85, heart_rate=120, consciousness="V", temperature=35.0,
            ),
            TriagePatient(
                "Well",
                respiratory_rate=16, spo2=98.0, on_oxygen=False,
                systolic_bp=125, heart_rate=70, consciousness="A", temperature=37.0,
            ),
        ]
        result = batch_triage(pts, method="news2")
        assert result[0].patient_id == "Sick"
        assert result[0].news2_result is not None

    def test_invalid_method(self):
        with pytest.raises(ValueError, match="method"):
            batch_triage([], method="whoops")

    def test_both_method(self):
        p = TriagePatient(
            "Full",
            can_walk=False, respiratory_rate=20,
            has_radial_pulse=True, follows_commands=True,
            spo2=96.0, on_oxygen=False, systolic_bp=118,
            heart_rate=80, consciousness="A", temperature=37.0,
        )
        result = batch_triage([p], method="both")
        assert result[0].start_result is not None
        assert result[0].news2_result is not None
