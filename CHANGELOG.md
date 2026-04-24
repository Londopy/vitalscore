# Changelog

All notable changes to **vitalscore** will be documented here.

This project adheres to [Semantic Versioning](https://semver.org/) and
the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

---

## [Unreleased]

> Changes staged for the next release.

---

## [0.1.0] — 2026-04-23

### Added

- **GCS** (`score_gcs`) — Glasgow Coma Scale with Eye / Verbal / Motor sub-scores,
  severity bands (Mild / Moderate / Severe TBI), and per-component descriptors.
- **AVPU** (`score_avpu`) — Alert / Voice / Pain / Unresponsive consciousness scale
  with GCS equivalents, `is_critical` flag, and recommended clinical actions.
- **APGAR** (`score_apgar`) — Newborn APGAR score with Appearance / Pulse / Grimace /
  Activity / Respiration components and intervention guidance.
- **START triage** (`score_start`) — Simple Triage And Rapid Treatment algorithm
  producing Immediate / Delayed / Minor / Deceased priority tags; supports both
  radial-pulse and capillary-refill perfusion inputs.
- **NEWS2** (`score_news2`) — National Early Warning Score 2 across all seven
  physiological parameters; SpO₂ Scale 1 (standard) and Scale 2 (COPD /
  hypercapnic failure); Low / Medium / High risk classification.
- **qSOFA** (`score_qsofa`) — quick Sequential Organ Failure Assessment with
  `sepsis_alert` boolean (score ≥ 2).
- **HEART score** (`score_heart`) — Chest pain risk stratification with typed enums
  for all five domains and MACE probability strings.
- **CUPS** data model — Critical / Unstable / Potentially unstable / Stable
  classification with transport-priority ordering.
- **OPQRST** data model — Onset / Provocation / Palliation / Quality / Radiation /
  Severity / Time / Associated symptom characterisation.
- **SAMPLE** data model — Signs & Symptoms / Allergies / Medications / Pertinent
  history / Last oral intake / Events patient history model.
- **Batch triage** (`batch_triage`) — accepts a list of `TriagePatient` objects,
  runs START and/or NEWS2 scoring, and returns patients sorted from most to
  least critical. Missing-field errors are recorded per-patient rather than
  raising globally.
- **CLI tool** (`vitalscore <score> [flags]`) — score any patient directly from
  the terminal with ANSI-coloured output; all seven scores are supported.
- **80 unit tests** covering boundary conditions, invalid inputs, enum coercion,
  case-insensitive parsing, and full batch-sorting behaviour.

[Unreleased]: https://github.com/Londopy/vitalscore/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Londopy/vitalscore/releases/tag/v0.1.0
