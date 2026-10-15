# QSimulation
About quantum simulation research happening at Accelequant

## Quantinuum-AQ: QITE vs Quantum Krylov (branch `prajjwal-dev`)

**Started:** 2026-10-08  
**Status:** active

## Scope

Study notes on Quantum Imaginary-Time Evolution (QITE) and a benchmark plan against Quantum
Krylov for molecular ground-state energies on Quantinuum hardware.

## Files

- `study-notes/qite-complete-guide.tex` / `.pdf` -- **main QITE document**: merge of the two notes below, written for first-time learners
- `study-notes/quantum-imaginary-time-evolution.tex` / `.pdf` -- earlier derivation log (kept; has a 2026-10-12 correction entry)
- `study-notes/` holds every .tex, .pdf and .pptx. Provided: `QITE_Learning_Notes.*`, `QITE_Teaching_Slides.*`, `Krylov_SKQD_Study_Notes.*`, the two papers -- user-provided notes and slides (untouched)
- `study-notes/quantinuum-krylov-review-and-strategy.tex` / `.pdf` -- **main Krylov document**: critique of the SKQD report, the four 'state-of-the-art paradigms' brief checked claim by claim, toy numerics, alternatives and the four-arm publication strategy (2026-10-15)
- `study-notes/qite-slides.pptx` -- 15-slide deck (built by `code/make_ppt.py`)
- `code/qite_h2.py` -- 2-qubit H2 QITE / ITE / Krylov emulation; writes `figures/` and `code/results.json`
- `code/krylov_toy_checks_h2.py` -- all toy checks A-G of the Krylov document (overlap conditioning, shot noise + thresholding, sampled basis vs classical control, report arithmetic, statistical PE vs Krylov on the same data, IQPE depth, HQC envelope); writes `code/krylov_toy_checks_h2_results.json`, `figures/krylov-conditioning-h2.png`, `figures/spe-vs-krylov-h2.png`
- `code/qkrylov_quantinuum.py` -- circuit-level prototype of the four benchmark arms (SKQD sampling, coherent Krylov with Hadamard tests, QITE, statistical phase estimation) written against pytket: circuits compiled to the H-series native gate set {PhasedX, Rz, ZZPhase}, costed with Quantinuum's HQC formula; runs on a local statevector backend with sampled shots (`--backend statevector`; fixed Trotter step, Oliveira noise-aware Krylov threshold, QCELS fit, per-circuit HQC ledger), and carries a qnexus submission path for the H2 emulators/hardware (`--backend qnexus --device H2-1LE|H2-Emulator|H2-1E|H2-1`, untested here); writes `code/qkrylov_<instance>_results.json` and `figures/qkrylov-<instance>-budget.png` (both `h2-2q` and `h2-4q` results are committed; the 4-qubit Hadamard-test circuits reach 600-1500 ZZPhase gates, which is the budget story of Section 12 of the Krylov document)
- `notes/` -- the three research notes (2026-10-15) behind the Krylov document: Quantinuum platform facts, checked literature citations, state of the art and novelty check
- `figures/` -- plots used by the notes and slides
