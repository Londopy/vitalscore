"""vitalscore CLI — score a patient from the terminal.

Usage
-----
  vitalscore gcs --eye 4 --verbal 5 --motor 6
  vitalscore avpu --level P
  vitalscore apgar --appearance 2 --pulse 2 --grimace 2 --activity 2 --respiration 2
  vitalscore start --no-walk --rr 28 --pulse --follows-commands
  vitalscore news2 --rr 22 --spo2 94 --no-o2 --sbp 105 --hr 98 --acvpu A --temp 37.2
  vitalscore qsofa --gcs 13 --rr 24 --sbp 95
  vitalscore heart --history 2 --ecg 1 --age 2 --risk 2 --troponin 2
"""

from __future__ import annotations

import argparse
import sys
import textwrap


# ── ANSI colours (disabled on non-TTY) ────────────────────────────────────────

def _colour(code: str, text: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"

RED    = lambda t: _colour("1;31", t)
YELLOW = lambda t: _colour("1;33", t)
GREEN  = lambda t: _colour("1;32", t)
CYAN   = lambda t: _colour("1;36", t)
BOLD   = lambda t: _colour("1", t)


# ═══════════════════════════════════════════════════════════════════════════════
# Sub-command handlers
# ═══════════════════════════════════════════════════════════════════════════════

def _cmd_gcs(args: argparse.Namespace) -> None:
    from vitalscore.scores.gcs import score_gcs
    try:
        result = score_gcs(eye=args.eye, verbal=args.verbal, motor=args.motor)
    except ValueError as exc:
        print(RED(f"Error: {exc}"), file=sys.stderr)
        sys.exit(1)

    colour_fn = GREEN if result.total >= 13 else (YELLOW if result.total >= 9 else RED)
    print(colour_fn(BOLD(f"GCS {result.total}/15  [E{result.eye} V{result.verbal} M{result.motor}]")))
    print(f"  Eye:    {result.eye} — {result.eye_descriptor}")
    print(f"  Verbal: {result.verbal} — {result.verbal_descriptor}")
    print(f"  Motor:  {result.motor} — {result.motor_descriptor}")
    print(f"  Severity: {result.severity}")
    print(f"  → {result.interpretation}")


def _cmd_avpu(args: argparse.Namespace) -> None:
    from vitalscore.scores.avpu import score_avpu
    try:
        result = score_avpu(args.level)
    except ValueError as exc:
        print(RED(f"Error: {exc}"), file=sys.stderr)
        sys.exit(1)

    colour_fn = RED if result.is_critical else GREEN
    print(colour_fn(BOLD(f"AVPU: {result.code} — {result.label}")))
    print(f"  {result.description}")
    print(f"  GCS equivalent: {result.gcs_equivalent}")
    print(f"  Action: {result.recommended_action}")


def _cmd_apgar(args: argparse.Namespace) -> None:
    from vitalscore.scores.apgar import score_apgar
    try:
        result = score_apgar(
            appearance=args.appearance,
            pulse=args.pulse,
            grimace=args.grimace,
            activity=args.activity,
            respiration=args.respiration,
        )
    except ValueError as exc:
        print(RED(f"Error: {exc}"), file=sys.stderr)
        sys.exit(1)

    colour_fn = GREEN if result.total >= 7 else (YELLOW if result.total >= 4 else RED)
    print(colour_fn(BOLD(f"APGAR {result.total}/10 — {result.category}")))
    print(str(result))


def _cmd_start(args: argparse.Namespace) -> None:
    from vitalscore.scores.start import score_start, STARTPriority
    try:
        rr = args.rr if not args.apnoeic else None
        result = score_start(
            can_walk=args.walk,
            respiratory_rate=rr,
            has_radial_pulse=args.pulse if args.pulse is not None else None,
            cap_refill_seconds=args.cap_refill,
            follows_commands=args.follows_commands if args.follows_commands is not None else None,
        )
    except ValueError as exc:
        print(RED(f"Error: {exc}"), file=sys.stderr)
        sys.exit(1)

    colours = {
        STARTPriority.IMMEDIATE: RED,
        STARTPriority.DELAYED:   YELLOW,
        STARTPriority.MINOR:     GREEN,
        STARTPriority.DECEASED:  lambda t: _colour("2;37", t),
    }
    cfn = colours[result.priority]
    print(cfn(BOLD(f"START: {result.priority.value.upper()}  [{result.colour} tag]")))
    print(f"  → {result.rationale}")


def _cmd_news2(args: argparse.Namespace) -> None:
    from vitalscore.scores.news2 import score_news2, NEWS2Risk
    try:
        result = score_news2(
            respiratory_rate=args.rr,
            spo2=args.spo2,
            on_oxygen=args.o2,
            systolic_bp=args.sbp,
            heart_rate=args.hr,
            consciousness=args.acvpu,
            temperature=args.temp,
            use_spo2_scale2=args.scale2,
        )
    except ValueError as exc:
        print(RED(f"Error: {exc}"), file=sys.stderr)
        sys.exit(1)

    colour_fn = (
        RED    if result.risk == NEWS2Risk.HIGH   else
        YELLOW if result.risk == NEWS2Risk.MEDIUM else
        GREEN
    )
    print(colour_fn(BOLD(f"NEWS2 {result.total}/20  [{result.risk.value} risk]")))
    print(str(result))


def _cmd_qsofa(args: argparse.Namespace) -> None:
    from vitalscore.scores.qsofa import score_qsofa
    try:
        result = score_qsofa(
            gcs=args.gcs,
            respiratory_rate=args.rr,
            systolic_bp=args.sbp,
        )
    except ValueError as exc:
        print(RED(f"Error: {exc}"), file=sys.stderr)
        sys.exit(1)

    colour_fn = RED if result.sepsis_alert else GREEN
    print(colour_fn(BOLD(f"qSOFA {result.total}/3  {'— SEPSIS ALERT' if result.sepsis_alert else ''}")))
    print(str(result))


def _cmd_heart(args: argparse.Namespace) -> None:
    from vitalscore.scores.heart import score_heart
    try:
        result = score_heart(
            history=args.history,
            ecg=args.ecg,
            age=args.age,
            risk_factors=args.risk,
            troponin=args.troponin,
        )
    except ValueError as exc:
        print(RED(f"Error: {exc}"), file=sys.stderr)
        sys.exit(1)

    colour_fn = (
        RED    if result.risk_category == "High"     else
        YELLOW if result.risk_category == "Moderate" else
        GREEN
    )
    print(colour_fn(BOLD(f"HEART {result.total}/10 — {result.risk_category} risk")))
    print(str(result))


# ═══════════════════════════════════════════════════════════════════════════════
# Argument parser
# ═══════════════════════════════════════════════════════════════════════════════

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vitalscore",
        description=textwrap.dedent("""\
            vitalscore — Clinical scoring calculators.
            Run 'vitalscore <score> --help' for per-score options.
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Available scores:
              gcs    — Glasgow Coma Scale
              avpu   — Alert/Voice/Pain/Unresponsive
              apgar  — APGAR newborn score
              start  — START mass-casualty triage
              news2  — National Early Warning Score 2
              qsofa  — quick Sequential Organ Failure Assessment
              heart  — HEART chest pain risk score
        """),
    )
    parser.add_argument("--version", action="version", version="vitalscore 0.1.0")
    sub = parser.add_subparsers(dest="command", metavar="<score>")

    # ── GCS ───────────────────────────────────────────────────────────────────
    gcs_p = sub.add_parser("gcs", help="Glasgow Coma Scale (E+V+M, total 3–15)")
    gcs_p.add_argument("--eye",    "-e", type=int, required=True, metavar="1-4",
                        help="Eye opening score (1–4)")
    gcs_p.add_argument("--verbal", "-v", type=int, required=True, metavar="1-5",
                        help="Verbal response score (1–5)")
    gcs_p.add_argument("--motor",  "-m", type=int, required=True, metavar="1-6",
                        help="Motor response score (1–6)")
    gcs_p.set_defaults(func=_cmd_gcs)

    # ── AVPU ──────────────────────────────────────────────────────────────────
    avpu_p = sub.add_parser("avpu", help="AVPU consciousness scale")
    avpu_p.add_argument("--level", "-l", type=str, required=True, metavar="A|V|P|U",
                         help="AVPU level: A (Alert), V (Voice), P (Pain), U (Unresponsive)")
    avpu_p.set_defaults(func=_cmd_avpu)

    # ── APGAR ─────────────────────────────────────────────────────────────────
    apgar_p = sub.add_parser("apgar", help="APGAR newborn score (0–10)")
    for flag, dest, hlp in [
        ("--appearance",  "appearance",  "Skin colour (0–2)"),
        ("--pulse",       "pulse",       "Heart rate (0–2)"),
        ("--grimace",     "grimace",     "Reflex irritability (0–2)"),
        ("--activity",    "activity",    "Muscle tone (0–2)"),
        ("--respiration", "respiration", "Breathing effort (0–2)"),
    ]:
        apgar_p.add_argument(flag, dest=dest, type=int, required=True,
                              metavar="0-2", help=hlp)
    apgar_p.set_defaults(func=_cmd_apgar)

    # ── START ─────────────────────────────────────────────────────────────────
    start_p = sub.add_parser("start", help="START mass-casualty triage")
    walk_g = start_p.add_mutually_exclusive_group(required=True)
    walk_g.add_argument("--walk",    dest="walk", action="store_true",  help="Patient can walk")
    walk_g.add_argument("--no-walk", dest="walk", action="store_false", help="Patient cannot walk")
    start_p.add_argument("--rr",     type=int,   default=None, metavar="breaths/min",
                          help="Respiratory rate (breaths/min); omit or use --apnoeic if no breathing")
    start_p.add_argument("--apnoeic", action="store_true",
                          help="Patient is apnoeic (no respirations)")
    pulse_g = start_p.add_mutually_exclusive_group()
    pulse_g.add_argument("--pulse",    dest="pulse", action="store_true",  default=None,
                          help="Radial pulse present")
    pulse_g.add_argument("--no-pulse", dest="pulse", action="store_false",
                          help="Radial pulse absent")
    start_p.add_argument("--cap-refill", dest="cap_refill", type=float, default=None,
                          metavar="seconds", help="Capillary refill time in seconds")
    cmd_g = start_p.add_mutually_exclusive_group()
    cmd_g.add_argument("--follows-commands",    dest="follows_commands", action="store_true",
                        default=None, help="Patient can follow simple commands")
    cmd_g.add_argument("--no-follows-commands", dest="follows_commands", action="store_false",
                        help="Patient cannot follow simple commands")
    start_p.set_defaults(func=_cmd_start)

    # ── NEWS2 ─────────────────────────────────────────────────────────────────
    news2_p = sub.add_parser("news2", help="National Early Warning Score 2")
    news2_p.add_argument("--rr",    type=int,   required=True, metavar="breaths/min",
                          help="Respiratory rate")
    news2_p.add_argument("--spo2",  type=float, required=True, metavar="%",
                          help="SpO₂ percentage")
    o2_g = news2_p.add_mutually_exclusive_group(required=True)
    o2_g.add_argument("--o2",    dest="o2", action="store_true",  help="Patient on supplemental O₂")
    o2_g.add_argument("--no-o2", dest="o2", action="store_false", help="Patient not on O₂")
    news2_p.add_argument("--sbp",   type=int,   required=True, metavar="mmHg",
                          help="Systolic blood pressure")
    news2_p.add_argument("--hr",    type=int,   required=True, metavar="bpm",
                          help="Heart rate")
    news2_p.add_argument("--acvpu", type=str,   required=True, metavar="A|C|V|P|U",
                          help="ACVPU consciousness level")
    news2_p.add_argument("--temp",  type=float, required=True, metavar="°C",
                          help="Temperature in Celsius")
    news2_p.add_argument("--scale2", action="store_true",
                          help="Use SpO₂ Scale 2 (for COPD / hypercapnic failure)")
    news2_p.set_defaults(func=_cmd_news2)

    # ── qSOFA ─────────────────────────────────────────────────────────────────
    qsofa_p = sub.add_parser("qsofa", help="qSOFA sepsis screening (0–3)")
    qsofa_p.add_argument("--gcs", type=int, required=True, metavar="3-15",
                          help="GCS total (3–15)")
    qsofa_p.add_argument("--rr",  type=int, required=True, metavar="breaths/min",
                          help="Respiratory rate")
    qsofa_p.add_argument("--sbp", type=int, required=True, metavar="mmHg",
                          help="Systolic blood pressure")
    qsofa_p.set_defaults(func=_cmd_qsofa)

    # ── HEART ─────────────────────────────────────────────────────────────────
    heart_p = sub.add_parser("heart", help="HEART chest pain risk score (0–10)")
    heart_p.add_argument("--history",  type=int, required=True, metavar="0-2",
                          help="H: history score (0=slightly suspicious, 1=moderate, 2=highly suspicious)")
    heart_p.add_argument("--ecg",      type=int, required=True, metavar="0-2",
                          help="E: ECG score (0=normal, 1=non-specific, 2=significant ST deviation)")
    heart_p.add_argument("--age",      type=int, required=True, metavar="0-2",
                          help="A: age score (0=<45, 1=45-64, 2=≥65)")
    heart_p.add_argument("--risk",     type=int, required=True, metavar="0-2",
                          help="R: risk factor score (0=none, 1=1-2 factors, 2=≥3 or known disease)")
    heart_p.add_argument("--troponin", type=int, required=True, metavar="0-2",
                          help="T: troponin score (0=≤ULN, 1=1-3×ULN, 2=>3×ULN)")
    heart_p.set_defaults(func=_cmd_heart)

    return parser


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
