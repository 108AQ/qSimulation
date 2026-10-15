<!-- Research note compiled 2026-10-15 with web access for study-notes/quantinuum-krylov-review-and-strategy.tex; sources are URLs/arXiv IDs; confidence tags as stated inside. -->

# Quantinuum platform fact-check (verified 2026-10-15)

Method: every statement below was checked against a fetched page (WebFetch) or a locally
extracted PDF (pdftotext on the official data sheets / PCNs, copies in `pdfs/` next to this file).
Where a page could not be fetched, this is stated and the closest source is given.
Confidence: **high** = read directly from a primary source; **medium** = primary source but
partial/indirect, or consistent secondary sources; **low** = single secondary source or inferred.

---

## 1. System Model H2 (H2-1, H2-2) and H1-1

### 1a. Official H2 Product Data Sheet — Version 4.00, September 17, 2025  (high)
Source: https://docs.quantinuum.com/systems/_static/assets/data_sheets/Quantinuum%20H2%20Product%20Data%20Sheet.pdf
(the older path `/systems/data_sheets/...` now returns 404). Text extracted with pdftotext.

Features (verbatim bullets):
- "N ≥ 56 qubit trapped-ion based quantum computers"
- "All-to-all connectivity"
- "Quantum charge-coupled device (QCCD) architecture with 4 gate zones in a trap consisting of two connected linear sections"
- "Mid-circuit measurement conditioned circuit branching"  (= classical feed-forward / conditional logic)
- "Qubit reuse after mid-circuit measurement"
- "Native gate set: single-qubit rotations, two-qubit ZZ gates, parameterized-angle ZZ gates, general SU(4) entangler"
- "TKET supported in the stack provides circuit optimization to all submitted circuits."

Table 1 (Typical / Max):
| Parameter | Typical | Max |
|---|---|---|
| Qubits | 56 | |
| Connectivity | All-to-all | |
| Parallel two-qubit operations | 4 | |
| 1-qubit gate infidelity | 3 × 10⁻⁵ | 2 × 10⁻⁴ |
| 2-qubit gate infidelity | 1 × 10⁻³ | 2 × 10⁻³ |
| SPAM error | 1 × 10⁻³ | 5 × 10⁻³ |
| Memory error per qubit at average depth-1 circuit | 2 × 10⁻⁴ | 2 × 10⁻³ |
| Mid-circuit measurement cross-talk error | 5 × 10⁻⁶ | 2 × 10⁻⁴ |

Qubits are ¹⁷¹Yb⁺ hyperfine states; "typical infidelities ... are an average over all operational zones".
The sheet says machine-specific data are in the "Performance Validation document and Quantinuum
Hardware Specifications repository" (https://github.com/Quantinuum/quantinuum-hardware-specifications —
README confirms it holds "the data referenced in the Quantinuum H1 and H2 Product Data Sheets";
the per-machine JSON was not read here).  The data sheet does NOT distinguish H2-1 from H2-2.

### 1b. Quantinuum H2 product web page  (high, marketing figures, undated page, © 2026)
Source: https://www.quantinuum.com/hardware/h2
"56 fully-connected qubits"; single-qubit gate fidelity ">99.99%"; two-qubit gate fidelity ">99.9%";
Quantum Volume "33,554,432 (2^25)"; "All-to-all-connectivity"; mid-circuit measurement, conditional
logic and qubit reuse listed as features; "racetrack architecture".

### 1c. H2-1 vs H2-2 and emulator sizes (Azure provider page, ms.date 2025-01-28, updated 2026-05-15)  (high)
Source: https://learn.microsoft.com/azure/quantum/provider-quantinuum
- `quantinuum.qpu.h2-1` 56 qubits; `quantinuum.qpu.h2-2` 56 qubits.
- `quantinuum.sim.h2-1e` / `h2-2e`: "56/32 qubits — Uses a realistic physical model and noise model of H2-1[/H2-2]. 56 qubit simulation is only available as a stabilizer simulation".
- Syntax checkers `h2-1sc`, `h2-2sc` free of cost.
- Capabilities table: "Mid-Circuit Measurement and Reset (MCMR)", "Arbitrary Angle ZZ Gates",
  "General SU(4) Entangling Gate", "Emulator Noise Parameters", "TKET Optimizations in Quantinuum Stack"
  (`tket-opt-level`, default 2; `no-opt`). Note: "All mid-circuit measurements should be followed by a
  reset if the qubit is to be used again".
- Internal inconsistency on that page: prose says H2 "currently has 1 machine, the H2-1" while the
  target table lists both H2-1 and H2-2.

Systems Reference table (https://docs.quantinuum.com/systems/support/system_reference.html): System
Model H2 — 56 qubits — "Available" — release 2023-05-09 — Racetrack.  (high)

### 1d. Per-device 2025 numbers (secondary, medium-low)
A 2026 arXiv paper that ran on H2-2 (arXiv:2608.04290) quotes Quantinuum's H2-2 hardware-specification
dataset dated 2025-08-28: two-qubit gate error 8.3(5) × 10⁻⁴, SPAM 6.7(9) × 10⁻⁴ (|0⟩) and
1.2(1) × 10⁻³ (|1⟩). Seen only in a search snippet; not read from the paper. Treat as indicative.

### 1e. H1-1  (high)
- H1 Product Data Sheet Version 8.0.1, June 09, 2025
  (https://docs.quantinuum.com/systems/_static/assets/data_sheets/Quantinuum%20H1%20Product%20Data%20Sheet.pdf):
  20 qubits, all-to-all, 5 parallel 2q operations; 1q infidelity 2 × 10⁻⁵ typ / 2 × 10⁻⁴ max;
  2q 1 × 10⁻³ / 3 × 10⁻³; SPAM 2 × 10⁻³ / 5 × 10⁻³; memory 2 × 10⁻⁴ / 1 × 10⁻³;
  MCM cross-talk 4 × 10⁻⁵ / 2 × 10⁻⁴; native gates incl. arbitrary-angle ZZ and general SU(4).
- **H1-1 is retired.** Product Change Notification 2025-07-15 "System Model H1 Retirement"
  (https://docs.quantinuum.com/systems/pcns/H1%20Product%20Change%20Notification%202025_07_15%20System%20Model%20H1%20Retirement.pdf):
  Date of Change October 15th 2025; sunsets H1-1, its emulators and syntax checkers (tied to Helios launch).
  Systems Reference: System Model H1 — 20 qubits — "Sunset (International)" — release 2020-10-30 —
  sunset 2025-10-15. The Japan on-premise H1-family machine "Reimei" (RIKEN) "continues operation".
  The Azure provider page (updated May 2026) lists no H1 targets.

---

## 2. Helios

### 2a. Launch  (high)
Product Change Notification "Helios Release", Issue Date November 5th, 2025, Date of Change
November 5th, 2025 (https://docs.quantinuum.com/systems/_static/assets/pcns/Helios%20Product%20Change%20Notification%202025_11_05%20Quantinuum%20Helios-1%20Release.pdf; extracted locally):
- "the Helios quantum computer will become commercially available through Nexus to current customers with access to system model H2"
- "Helios is the first release of our third-generation quantum computer ... qubits implemented through atomic hyperfine states of 137Ba+ ... Helios-1, which has 98 physical qubits (ions) ... eight interaction zones"
- Features: "98 qubit", "All-to-all connectivity", "8 gate zones for parallel single qubit operations and 4 parallel gate zones for two qubit operations", "Qubit reuse after mid-circuit measurement", "Native gate set: single-qubit rotations, two-qubit ZZ gates, arbitrary-angle ZZ gates", "Real-time conditional logic execution", "Capable of performing real-time error correction".
- Targets: "Helios-1" (physical hardware), "Helios-1SC" (syntax checker), "Helios-1E" (Helios emulation);
  Nexus-hosted endpoints "(billed in CPU time)": "Helios-1E-lite" (emulation on CPU), "Selene", "Selene – plus".
- "Subscriptions provide access to both H2 and Helios QPUs ... up to the contractual monthly allocation of HQCs. For circuits that require ≤ 56 qubits, Quantinuum strongly encourages users to submit these jobs to the System Model H2 family".
- "Quantinuum will continue to utilize the HQC as a unit of cost for a submitted program but exact cost will only be returned after a circuit has been completed ... users will be able to specify a max cost".
Systems Reference: Quantinuum Helios — 98 qubits — "Available" — release 2025-11-05 — Tuning Fork.
Secondary (press reprints of the release, 5 Nov 2025): 99.921% 2q, 99.9975% 1q fidelity;
"94 logical qubits (error detected)" and "48 logical error-corrected qubits" (medium).

### 2b. Helios Product Data Sheet — Version 1.2, June 09, 2026  (high)
Source: https://docs.quantinuum.com/systems/_static/assets/data_sheets/Quantinuum%20Helios%20Product%20Data%20Sheet.pdf
Features: "N ≥ 98 137Ba+ qubit"; "All-to-all connectivity"; "eight gate zones in a trap consisting of a
single circular storage ring and two linear gating sections"; "Eight gate zones for SPAM [and] 1-qubit
operations and four gate zones for 2-qubit operations"; "Ultra-low crosstalk with mid-circuit measurement
conditioned circuit branching"; "Qubit reuse after mid-circuit measurement"; "Native gate set: 1-qubit
rotations, 2-qubit ZZ gates, parameterized-angle ZZ gates" (no SU(4) entangler listed, unlike H2);
"Long T2 coherence times (~seconds)"; "Real-time integer and floating point arithmetic"; "Real-time
boolean logic"; "Real-time arbitrary control flow"; "Capable of performing real-time error correction".

| Parameter | Typical | Max |
|---|---|---|
| Qubits | 98 | |
| Connectivity | All-to-all | |
| Two qubit quantum logic zones | 4 | |
| 1-qubit gate infidelity | 0.3 × 10⁻⁴ | 2 × 10⁻⁴ |
| 2-qubit gate infidelity | 8 × 10⁻⁴ | 20 × 10⁻⁴ |
| SPAM error | 5 × 10⁻⁴ | 20 × 10⁻⁴ |
| Memory error per qubit at average depth-1 circuit | 6 × 10⁻⁴ | 10 × 10⁻⁴ |
| Mid-circuit measurement cross-talk error | 0.5 × 10⁻⁴ | 7 × 10⁻⁴ |

### 2c. Helios characterisation paper  (high)
"Helios: A 98-qubit trapped-ion quantum computer", Ransford et al. (186 authors), arXiv:2511.05465,
submitted 7 Nov 2025, https://arxiv.org/abs/2511.05465 : ¹³⁷Ba⁺ hyperfine qubits; average infidelities
"2.5(1)×10⁻⁵ for single-qubit gates", "7.9(2)×10⁻⁴ for two-qubit gates", "4.8(6)×10⁻⁴ for state
preparation and measurement".

### 2d. Native gate set as exposed to users (Guppy names)  (high)
Helios Operation page https://docs.quantinuum.com/systems/user_guide/hardware_user_guide/helios.html :
`phased_x` (R_xy(θ,φ)), `rz` (R_z, "performed virtually"), `zz_max` (ZZ), `zz_phase` (R_ZZ(θ)),
`measure`, `reset`; minimum angles R_zz 1×10⁻⁴, R_xy 3×10⁻⁴ (smaller "automatically rounded to zero");
"The junction enables all-to-all connectivity with N operations compared to N² for swaps";
"Each job submitted to hardware is limited to 10,000 shots and 500,000 Hardware Quantum Credits (HQCs)
hard limit"; "Users must specify a `max_cost` parameter". pytket circuits are accepted (tket realigns
non-native ops after submission). Parameterised-ZZ page:
https://docs.quantinuum.com/systems/trainings/helios/getting_started/parameterized_angle_2_qubit_gates.html
(`guppylang.std.qsystem.zz_phase()`, R_zz(θ)=e^{−iθ/2 Z⊗Z}, R_zz(π/2)=ZZ).

### 2e. Emulators  (high)
- `Helios-1E`: hardware-hosted, "operating on a GPU backend", statevector up to 32 qubits (recommend ≤28),
  stabilizer up to 56; usage tracked in HQCs ("Hardware Quantum Credits (HQCs) processed in an hour");
  default noise parameters (table "from 2025-11-18"): p1 = 2.5e-05, p2 = 0.0008, p_meas = 1e-06,
  p_init = 0.0005, p_prep_leak_ratio 0.75, seepage 0.3333, quadratic dephasing 0.058, linear 0.0079.
  https://docs.quantinuum.com/systems/user_guide/emulator_user_guide/emulators/helios_emulators.html
- `Helios-1E-lite`: CPU, "billed in CPU time" (PCN). `Selene`: open-source local emulator framework
  (also hosted in Nexus); simulators Statevector (QuEST), Stabilizer, MPS (added May 2026), Coinflip,
  ClassicalReplay; error models NoError, Depolarizing, QSystem ("preconfigured noise model for accurate
  Helios emulation"), HeliosCustom. https://docs.quantinuum.com/nexus/nexus_api/backend_configs.html ;
  https://docs.quantinuum.com/systems/trainings/helios/getting_started/quantinuum_emulator.html
- May 2026 systems release notes (https://docs.quantinuum.com/product-updates/posts/systems_4_2026/,
  dated May 4, 2026): Selene MPS simulator + open-source error models; Leakage Error Toolkit (heralded
  leakage measurement on Helios, leakage detection gadget H2+Helios, leakage repump H2); Helios runtime
  single-qubit gate optimisation on by default (~50% fewer Rxy in random mirror benchmarking, ~25% in
  phase estimation).

### 2f. How Helios is costed  (high) — still HQC, but dynamic
Workflow page https://docs.quantinuum.com/systems/user_guide/hardware_user_guide/workflow.html :
"Jobs submitted to Helios are costed differently to System Model H2 jobs. ... overall HQC cost is dynamic
to job execution. The HQC cost for a job consists of 2 parts: a HQC cost dependent on the branches of the
user's program that are executed [and] an additional +5 HQC cost for a new job". Estimate by "specifying
`metrics` as the emulation mode with the target as the Helios emulator (`Helios-1E`)".
Helios costing page https://docs.quantinuum.com/systems/trainings/helios/getting_started/costing.html :
HQC = 5 + (C/5000) × (Max(N₁q) + 10·Max(N₂q) + 5·Max(N_M)), where 1-qubit gates = `phased_x`
(Rz excluded), 2-qubit = `zz_phase`, measurement-type = `measure`, `leaked_measure`,
`measure_and_reset` and ion initialisations; Max = maximum per-shot counts over a 10-shot emulation;
each branch of a dynamic program costed separately; "Users are required to specify a maximum cost with
each job submission" (hard cap, deducted from allocation; DEPLETED state if exceeded).
Worked example on the page: 10/20/30 shots → 6.098 / 7.196 / 8.294 HQC.

---

## 3. HQC formula, where documented, emulator charging, allocations

### 3a. Formula  (high) — matches the user's belief exactly
HQC = 5 + C · (N₁q + 10·N₂q + 5·N_m) / 5000
- Quantinuum docs (Hardware User Guide → Workflow → "Tracking Usage with Hardware Quantum Credits"):
  https://docs.quantinuum.com/systems/user_guide/hardware_user_guide/workflow.html — N₁q = number of
  1-qubit gates, N₂q = native 2-qubit gates, N_m = "state preparation and measurement operations,
  including the initial implicit preparation and any intermediate or final measurements and resets",
  C = shot count. For H2 conditional programs "the charged HQCs include all the gates and measurements
  across all conditional branches" (whether executed or not). "The syntax checkers are free to use while
  the emulators and quantum computers require HQCs."
- Nexus "Quantum System User Terms And Conditions" v8.0, October 2026:
  https://nexus.quantinuum.com/auth/terms_and_conditions/quantum_system — same formula; HQCs "are a
  representation of the size of a quantum computational job ... neither units of time nor money".
- Azure Quantum provider page (updated 2026-05-15) and pricing page (updated 2026-04-23):
  https://learn.microsoft.com/azure/quantum/provider-quantinuum ; https://learn.microsoft.com/azure/quantum/pricing
  — same formula; "Native gate is equivalent to CNOT up to several single-qubit gates".
- Glossary: https://www.quantinuum.com/glossary-item/hardware-quantum-credits-hqcs (points to the docs page).

### 3b. Emulator charging relative to hardware  (high)
- Hardware-hosted (Quantinuum-hosted) emulators `H1-1E`, `H2-1E`, `H2-2E` (and `Helios-1E`) "consume HQCs
  upon usage" with the same formula; Azure books them as "eHQCs" with a separate quota ("System Model H2
  Emulator usage is offered free-of-charge with a hardware subscription").
- Nexus-hosted emulators — `H1-Emulator`, `H2-Emulator` (noisy, 26 qubits), `H1-1LE`/`H2-1LE`
  (noiseless), `Helios-1E-lite`, `Selene` — are "costed in time" / counted against the Nexus Simulation
  quota, "without submitting to a Fair Queue or consuming HQCs".
  Sources: https://docs.quantinuum.com/systems/user_guide/emulator_user_guide/introduction.html (table:
  H1-1E / H2-1E / H2-2E tier "Hardware", currency "HQC"; H1-Emulator / H2-Emulator tier "Nexus",
  currency "Seconds"; statevector 32 / stabilizer 56 qubits for H2-xE; 26 for H2-Emulator);
  https://docs.quantinuum.com/systems/trainings/h2/getting_started/emulators.html ;
  https://docs.quantinuum.com/nexus/trainings/notebooks/basics/auth_quotas.html ("Your simulation,
  compilation and Nexus Lab quota will renew each month ... if you have access to Quantinuum Systems
  you'll need to have a HQC quota").
- Cost estimation API: `qnexus.circuits.cost(circuit_ref, n_shots, backend_config, syntax_checker=None,
  project=None) -> float | None` — "Estimate the cost (in HQC) of running Circuit programs for n_shots
  number of shots on a Quantinuum H2 system. NB: This will execute a costing job on a dedicated cost
  estimation device." https://docs.quantinuum.com/nexus/nexus_api/circuits.html

### 3c. Published allocations / prices  (medium)
- Azure pricing (updated 2026-04-23): Standard Plan USD 125,000/month = 10k HQCs (H2) + 100k eHQCs;
  Premium Plan USD 175,000/month = 17k HQCs + 170k eHQCs; Pay-as-you-go per HQC (contact sales).
- arXiv:2601.09943 "Three Months in the Life of Cloud Quantum Computing" (15 Jan 2026,
  https://arxiv.org/abs/2601.09943): one group's subscription "$185K per month, that included 17,000 HQC"
  and "170,000 HQC for the emulators"; their (self-declared arbitrary) split gives ≈ $9.79/HQC;
  "Quantinuum has just recently added support for a pay-as-you-go plan".
- Academic: no public Quantinuum-wide academic HQC allocation found. Closest: H1 retirement PCN mentions
  "Academic pay-as-you-go plans" (Azure) being updated to H2 targets; EPFL internal competitive call for
  Quantinuum access (deadline 17 Aug 2026, no HQC figure):
  https://www.epfl.ch/research/domains/quantum-center/funding/call-for-research-proposals-access-to-quantinuum-quantum-computers/ ;
  UK NQCC SparQ Access offers "Quantinuum H2-1 and H2-2 plus their emulators" to UK academics in
  3-month allocations (https://www.nqcc.ac.uk/sparq-access/). Could not verify any numeric academic
  allocation.

---

## 4. Native gate names in pytket; compilation; pytket-quantinuum status

### 4a. Gate set and passes  (high)
pytket-quantinuum docs https://docs.quantinuum.com/tket/extensions/pytket-quantinuum/ (changelog top entry
0.59.2, August 2026) and the GitHub source of that page
(https://raw.githubusercontent.com/Quantinuum/pytket-quantinuum/main/docs/index.md):
- Native gate set "{Rz, PhasedX, ZZMax, ZZPhase}" (AutoRebase target); native two-qubit gate options
  "`ZZMax`, `ZZPhase` and `TK2`"; "Currently, the default two-qubit gate for all devices is `ZZPhase`";
  AutoSquash targets {PhasedX, Rz}. (`TK2` = the general SU(4) entangler, opt-in; on the hardware stack
  it is `Rxxyyzz`, selected with `nativetq: Rxxyyzz` per the Azure page.)
- `QuantinuumBackend.default_compilation_pass(optimisation_level)` — levels 0–3, default 2:
  - 0: DecomposeBoxes, scratch_reg_resize_pass, AutoRebase, FlattenRelabelRegistersPass
  - 1: DecomposeBoxes, scratch_reg_resize_pass, SynthesiseTket, NormaliseTK2, DecomposeTK2, AutoRebase,
    ZZPhaseToRz, RemoveRedundancies, AutoSquash, FlattenRelabelRegistersPass, RemoveRedundancies
  - 2: DecomposeBoxes, scratch_reg_resize_pass, FullPeepholeOptimise, NormaliseTK2, DecomposeTK2,
    AutoRebase, RemoveRedundancies, AutoSquash, FlattenRelabelRegistersPass, RemoveRedundancies
  - 3: DecomposeBoxes, scratch_reg_resize_pass, RemoveBarriers, GreedyPauliSimp (timeout, default 5 min),
    NormaliseTK2, DecomposeTK2, AutoRebase, RemoveRedundancies, AutoSquash, FlattenRelabelRegistersPass,
    RemoveRedundancies
- `rebase_pass()` converts all gates to supported OpTypes ignoring architecture constraints.
- In the Quantinuum cloud stack, submitted circuits are additionally run through TKET at `tket-opt-level`
  (default 2) unless `no-opt` is set (Azure page; Nexus `QuantinuumConfig.no_opt`, default True in qnexus,
  i.e. Nexus-compiled circuits are not re-optimised server-side by default).

### 4b. Deprecation of pytket-quantinuum submission → qnexus  (high)
- Product update 28 Aug 2025 https://docs.quantinuum.com/product-updates/posts/nexus_8_2025_pytket_quantinuum/ :
  "Quantinuum is deprecating the job submission API in pytket-quantinuum ... slated to be removed by
  November 30th, 2025"; "Recommendation is to use Nexus for job submission"; pytket-quantinuum "will still
  exist as a client-side tool for local compilation and local emulation (suffixed with 'LE')"; "Cloud
  emulators (suffixed with E) only accessible with Nexus from November 30th, 2025"; jobs retained 40 days.
- pytket-quantinuum docs: "As of version 0.56.0 it no longer allows submission to Quantinuum devices:
  please use the `qnexus` package for that." Changelog 0.56.1 (December 2025): "Remove all methods
  providing remote access to Quantinuum devices. (Please use `qnexus` instead.)"; 0.59.0 (April 2026)
  requires pytket 2.16, pytket-pecos 0.3.3 (local LE emulator), pytket-qir 1.0.0; 0.59.2 (August 2026).
  https://docs.quantinuum.com/tket/extensions/pytket-quantinuum/changelog.html
- Current recommended path: `qnexus` (Nexus) for compile/execute on hardware and cloud emulators;
  pytket-quantinuum only for offline compilation (`QuantinuumAPIOffline`) and local `...LE` emulation.
  For Helios the native path is Guppy → HUGR → `qnx.hugr.upload` (pytket circuits also accepted).

---

## 5. Current qnexus Python API (verified against docs pages, © 2025; no version number displayed)

Pages: https://docs.quantinuum.com/nexus/trainings/notebooks/basics/getting_started.html ;
https://docs.quantinuum.com/nexus/trainings/notebooks/basics/jobs_results.html (raw source
.../_sources/trainings/notebooks/basics/jobs_results.ipynb.txt) ;
https://docs.quantinuum.com/nexus/trainings/notebooks/basics/auth_quotas.html ;
https://docs.quantinuum.com/nexus/nexus_api/execute.html ; https://docs.quantinuum.com/nexus/nexus_api/backend_configs.html ;
https://docs.quantinuum.com/systems/trainings/h2/getting_started/emulators.html

### 5a. Minimal pytket workflow (code copied from the Jobs & Results notebook, login lines from Auth page)  (high)
```python
from datetime import datetime
from pytket import Circuit
import qnexus as qnx

qnx.login()                   # browser-based; alternatives: qnx.login_with_credentials(), qnx.logout()

my_job_name_prefix = datetime.now()
my_project_ref = qnx.projects.get_or_create(name="My Project")
# optional: qnx.context.set_active_project(my_project_ref)

my_circuit_ref = qnx.circuits.upload(
    name=f"My Circuit from {datetime.now()}",
    circuit=Circuit(2).H(0).CX(0, 1).measure_all(),
    project=my_project_ref,
)

compile_job_ref = qnx.start_compile_job(
    programs=[my_circuit_ref],
    name=f"{my_job_name_prefix}_compile_async",
    optimisation_level=1,
    backend_config=qnx.QuantinuumConfig(device_name="H2-1LE"),
    project=my_project_ref,
    skip_intermediate_circuits=False,  # Store compiled circuits
)
qnx.jobs.wait_for(compile_job_ref)
compiled_circuits = [item.get_output() for item in qnx.jobs.results(compile_job_ref)]

execute_job_ref = qnx.start_execute_job(
    programs=compiled_circuits,
    name=f"{my_job_name_prefix}_execute_async",
    n_shots=[100] * len(compiled_circuits),
    backend_config=qnx.QuantinuumConfig(device_name="H2-1LE"),
    project=my_project_ref,
)
qnx.jobs.wait_for(execute_job_ref)
execute_job_result_refs = qnx.jobs.results(execute_job_ref)
result = execute_job_result_refs[0].download_result()   # pytket BackendResult
result.get_counts()
```
Notes: the current docs use the keyword `programs=` (older pages used `circuits=`). API reference
signature: `qnexus.start_execute_job(programs, n_shots, backend_config, name, description='',
properties=None, project=None, valid_check=True, language=Language.AUTO, credential_name=None,
wasm_module=None, gpu_decoder_config=None, user_group=None, target_region=None ('us'|'sg'),
max_cost=[], n_qubits=[]) -> ExecuteJobRef`; blocking variant `qnexus.execute(..., timeout=300.0)`
returns `list[QsysResult | BackendResult | QIRResult]`. `qnx.jobs.status(ref)` for polling.
For Helios/HUGR programs the result object is a `QsysResult` and counts come from
`result.collated_counts()` (Getting Started page).

### 5b. `QuantinuumConfig` fields (API reference)  (high)
`device_name: str` (required); `simulator: str = 'state-vector'` (or `'stabilizer'`, noisy emulators
only); `noisy_simulation: bool = True` ("Whether to use a noisy simulation with an error model");
`error_params: UserErrorParams | None` (override p1, p2, p_meas, p_init, ... — not for LE targets);
`user_group`; `attempt_batching=False`, `batch_id`, `max_batch_cost`; `compiler_options`;
`no_opt=True`; `allow_implicit_swaps=True`; `allow_2q_gate_rebase=False`; `target_2qb_gate`;
`leakage_detection=False`; `simplify_initial=False`; `postprocess=False`; `machine_debug=False`;
`max_cost` (deprecated; pass per job).
Noiseless run example from the H2 emulators page:
`qnexus.QuantinuumConfig(device_name="H1-Emulator", noisy_simulation=False)`;
stabilizer: `qnexus.QuantinuumConfig(device_name=machine, simulator="stabilizer")`.

### 5c. Device names  (high)
- Hardware: `H2-1`, `H2-2`, `Helios-1` (H1-1 sunset 2025-10-15).
- Syntax checkers (free): `H2-1SC`, `H2-2SC`, `Helios-1SC`.
- Hardware-hosted noisy emulators (HQC-costed): `H2-1E`, `H2-2E`, `Helios-1E` (`H1-1E` sunset).
- Nexus-hosted noisy emulators (time-costed): `H2-Emulator` (26 qubits), `H1-Emulator`; `Helios-1E-lite` (CPU).
- Nexus-hosted noiseless (`LE`): `H2-1LE`, `H1-1LE` ("only provide noiseless state-vector emulation";
  `noisy_simulation`/`error_params` not applicable) — "provided for all Nexus users", counted in the
  Simulation quota. (pytket-quantinuum's *local* emulator also uses the `LE` suffix, via pytket-pecos.)
- Helios config: `qnx.models.HeliosConfig(system_name='Helios-1' | 'Helios-1E' | 'Helios-1SC',
  max_cost=..., emulator_config=qnx.models.HeliosEmulatorConfig(simulator=..., error_model=...,
  runtime=...), attempt_batching, batch_id, max_batch_cost, options)`; `qnx.models.SeleneConfig(...)`.
  Programs: `hugr = guppy_program.compile(); hugr_ref = qnx.hugr.upload(hugr_package=hugr, name=...)`.

---

## 6. Error mitigation / error detection in Quantinuum software

### 6a. PMSV  (high)
Paper: K. Yamamoto, D. Z. Manrique, I. T. Khan, H. Sawada, D. Muñoz Ramo, "Quantum hardware calculations
of periodic systems with partition-measurement symmetry verification: simplified models of hydrogen chain
and iron crystals", **Phys. Rev. Research 4, 033110 (2022)**, arXiv:2109.08401 (v4 24 May 2022),
https://arxiv.org/abs/2109.08401 (page links DOI 10.1103/PhysRevResearch.4.033110). (The citation
"Phys. Rev. Research 4, 033110 (2022)" in the brief is therefore correct; the title in the brief was not
given — it is NOT the Heisenberg-spin-chain paper.)
InQuanto exposes it: `inquanto.protocols.PMSV` (built from a list of stabilizers, e.g. from
`symmetry_operators_z2_in_sector()`), passed as `protocol.build(..., noise_mitigation=pmsv)`; also
`inquanto.protocols.SPAM` and Qermit `MitRes`/`MitEx` integration via `PauliAveraging.run_mitres()/run_mitex()`.
Docs: https://docs.quantinuum.com/inquanto/manual/errmit.html (example H₂: raw −1.0697 → PMSV −1.1251 vs
state-vector −1.1368, ~5% shots discarded); example script
https://docs.quantinuum.com/inquanto/_downloads/c7f5edf6e6adeb6a5d440542a06a3100/expval_pmsv.py

### 6b. Iceberg code  (high)
C. N. Self, M. Benedetti, D. Amaro, "Protecting expressive circuits with a quantum error detection code",
**Nature Physics 20, 219–224 (2024)**, DOI 10.1038/s41567-023-02282-2; arXiv:2211.06703 (v1 12 Nov 2022,
v2 26 Jul 2024 "Published version"), https://arxiv.org/abs/2211.06703. [[k+2, k, 2]] code detecting any
single-qubit error; experiments "On the 12-qubit Quantinuum **H1-2** hardware" (arXiv abstract): 8 logical
qubits, circuits of up to 256 layers, saturating logical quantum volume 2⁸; more syndrome measurements
help. (nature.com itself could not be fetched — journal reference taken from the arXiv page.)
Related Quantinuum error-detection chemistry: Yamamoto, Duffield, Kikuchi, Muñoz Ramo, "Demonstrating
Bayesian quantum phase estimation with quantum error detection", Phys. Rev. Research 6, 013221 (2024),
arXiv:2306.16608 — H₂ molecule, "[[n+2,n,2]]" code, up to 920 physical two-qubit gates, within 6×10⁻³ Ha.

### 6c. Productised error detection?  (medium)
- Found in software: `leakage_detection` option (QuantinuumConfig / pytket-quantinuum "Leakage Detection
  Gadget"), the May-2026 "Leakage Error Toolkit" (heralded leakage measurement on Helios, leakage repump
  on H2); InQuanto knowledge article "Demonstration of Quantum Error-Corrected Quantum Phase Estimation"
  (https://docs.quantinuum.com/inquanto/tutorials/InQ_KA_h2xh2.html) with module
  `inquanto.experiments.qec_qpe_chem` (encode/decode into the [[7,1,3]] colour code, Clifford+Rz).
- Could not verify any "Iceberg code" feature in InQuanto, qnexus or pytket-quantinuum docs. Treat the
  Iceberg code as a research result, not a product option.

---

## 7. Logical-qubit demonstrations (what, where)

| Result | Device | Source | Confidence |
|---|---|---|---|
| [[7,1,3]] colour (Steane) code and [[12,2,4]] Knill C4/C6 code; logical error rates below physical; repeated EC with [[12,2,4]] (error per cycle ≈ two physical CNOTs); 4 logical qubits from 30 physical | H2 (32-qubit era, Apr 2024) | arXiv:2404.02280 (v1 2 Apr 2024, v3 17 Nov 2024) https://arxiv.org/abs/2404.02280 | high |
| Tesseract subsystem colour code [[16,6,4]] used as 4 logical qubits / 16 physical, distance 4; graph states on up to 12 logical qubits; up to 5 EC rounds | H1 (20q) and H2 (56q) | arXiv:2409.04628 (v1 6 Sep 2024, v2 5 Dec 2024) https://arxiv.org/abs/2409.04628 | high |
| "12 logical qubits" GHZ: logical circuit error 0.0011 vs physical 0.024 | H2 (56 qubits, "99.8% two-qubit fidelity") | Azure blog 10 Sep 2024 https://azure.microsoft.com/en-us/blog/quantum/2024/09/10/microsoft-and-quantinuum-create-12-logical-qubits-and-demonstrate-a-hybrid-end-to-end-chemistry-simulation/ | high |
| Peer-reviewed version: Paetznick, Reichardt, da Silva, Ryan-Anderson, Aasen et al., "Improved quantum processor logical error rates via correction and detection", **Nature 654, 349–355 (2026)**, published 10 June 2026, DOI 10.1038/s41586-026-10628-y — 12-qubit (2 logical) Knill-inspired code + 16-qubit tesseract colour code (4 logical); "improvements in logical error rates ranging from 11× to 800×"; circuits up to 12 logical qubits | Quantinuum QCCD (H2) | https://www.nature.com/articles/s41586-026-10628-y | high |
| Logical teleportation with transversal gates (process fidelity 0.975(2)) and lattice surgery (0.851(9)); Knill-style EC 0.989(2); [[7,1,3]] code, up to 30 ions, real-time decoding | H2 | arXiv:2404.16728 (25 Apr 2024) | high |
| Four logical qubits entangled beyond break-even in a nonlocal [[25,4,3]] "Tanner-transformed long-range-enhanced surface code"; logical GHZ fidelity 99.5–99.7% vs physical 97.8–98.7% (post-selecting >98%) | H2 | arXiv:2406.02666 (Hong, Durso-Sabina, Hayes, Lucas); PRL 133, 180601 (2024) | high |
| Code switching RM[[15,1,3]] → Steane magic state, infidelity ≤ 5.1(2.7)×10⁻⁴, success prob. 82.58% | H2-1 (28 / 56 qubits) | arXiv:2506.14169; Phys. Rev. X 15, 041008 (2025) | high |
| "Breaking even with magic": [[6,2,2]] magic-state pair on 8 qubits, infidelity 7(+3/−1)×10⁻⁵ (14.8% discard); logical CH infidelity ≤ 2.3×10⁻⁴ vs physical 10⁻³ | H1-1 | arXiv:2506.14688 (17 Jun 2025) | high |
| Genons / symplectic double codes, fault-tolerant Clifford demo | H1-1 | arXiv:2406.09951 (14 Jun 2024) | medium |
| "Computing with many encoded logical qubits beyond break-even": iceberg [[k+2,k,2]] and concatenated [[(k₂+2)(k₁+2), k₂k₁, 4]]; 48–94 logical qubits; FT and partially-FT SPAM, QEC-cycle and logical-gate benchmarks, GHZ, 3D XY-model simulation | Helios (98q) | arXiv:2602.22211 (25 Feb 2026; 45 authors) https://arxiv.org/abs/2602.22211 | high |
| C₄-Helix [[20,2,6]] code: repeated QEC ≈ 4.6(+6.2/−2.6)×10⁻⁵ per logical qubit per cycle; two-qubit logical Clifford ≈ 2.8×10⁻⁴; FT interface to a distance-5 surface code (3-logical-qubit heterogeneous GHZ fidelity ≥ 99.925%) — no post-selection | Helios | arXiv:2609.03194 (2 Sep 2026) | high |
| Surface-code / colour-code / bivariate-bicycle *check-structured benchmarks* (LR-QAOA style, up to 81/91/48 data qubits, 480 MCMs) — a benchmark, not a logical memory | Helios-1 and H2-1 | arXiv:2610.05928 (Jülich, independent) | medium |
| Logical chemistry: QPE of H₂ molecule on [[7,1,3]]-encoded qubits with Steane EC gadgets; E − E_FCI = 0.001(13) Ha (v2/v3; v1 reported 0.018(10)); up to 1585 fixed + 7202 conditional physical 2q gates | H2-2 | arXiv:2505.09133 (v1 14 May 2025, v3 16 Sep 2026; page lists DOI 10.1103/m7j3-5sk6, journal not verified) | high (arXiv) / low (journal) |
| Microsoft "end-to-end" chemistry: 2 logical qubits + classical shadows + AI/HPC for the active site of a catalytic intermediate; blog says the logical run was on H1 and "within chemical accuracy" | H1 (per blog) | arXiv:2409.05835 (9 Sep 2024; device/code not in abstract) + Azure blog above | medium |

Not found / could not verify: any Quantinuum **bivariate-bicycle qLDPC** logical-memory experiment on
H2 or Helios (two targeted searches; only benchmarks and theory, e.g. arXiv:2510.18753 concatenated
symplectic double codes, Quantum 10, 2195 (2026), simulation only). The only "surface code" results are
the [[25,4,3]] nonlocal surface-code variant (H2, 2024) and the distance-5 surface-code interface in the
C₄-Helix paper (Helios, 2026). The brief's phrase "colour code logical qubits (2024, Nature?)" maps to
arXiv:2404.02280, which was published in Nature only in June 2026 (merged with the tesseract work).
Press claims of "50 logical qubits" (Dec 2024) could not be tied to a preprint.

---

## 8. Chemistry hardware papers 2024–2026 on Quantinuum machines (Krylov / subspace / QITE / SQD / phase estimation)

Found (one line each):
- arXiv:2309.09685 — Greene-Diniz et al., "Quantum computed Green's functions using a cumulant expansion of the Lanczos method", **Quantum 8, 1383 (2024)**: Hamiltonian moments → Lanczos tridiagonal matrix (a Krylov/moment method, the one behind InQuanto's `KrylovSubspaceComputable`); Hubbard/DMFT impurity models; run on **H1-1**. (high)
- arXiv:2309.10552 — Hémery et al., "Measuring the Loschmidt amplitude for finite-energy properties of the Fermi-Hubbard model on an ion-trap quantum computer", **PRX Quantum 5, 030323 (2024)**: ⟨ψ|e^{−iHt}|ψ⟩ time-series algorithm (the primitive of statistical/Fourier phase estimation) for a 16-site ladder (32 orbitals) on **H2-1**, with algorithm-specific error mitigation. (high)
- arXiv:2306.16608 — Yamamoto et al., Bayesian QPE with error detection, H₂ molecule, 920 2q gates, 6×10⁻³ Ha, PRR 6, 013221 (2024). (high)
- arXiv:2505.09133 — Yamamoto et al., QEC-protected QPE of H₂ on **H2-2** (see §7). (high)
- arXiv:2506.17207 — Tranter, Gowland, Yamamoto, Sze, Muñoz Ramo, "High-precision quantum phase estimation on a trapped-ion quantum computer" (20 Jun 2025): multi-ancilla QPE of H₂ on the 56-qubit machine, 50 bits of precision with Trotter error negated (8.9×10⁻¹⁶ Ha), 32–36 bits including Trotter error, 200 shots per experiment. (high)
- arXiv:2512.14415 — Nützel, Hartmann, Dreyer, Granet, "Ground state energy via adiabatic evolution and phase measurement for a molecular Hamiltonian on an ion-trap quantum computer", Quantum Sci. Technol. 11, 035038 (2026): H₃⁺ (6 qubits), adiabatic prep + noise-resilient iterative QPE; leakage identified as main obstacle to chemical accuracy; device not named in abstract (Quantinuum authors). (medium)
- arXiv:2603.26359 — Finger, Rapp, ..., Meichanetzidis (Quantinuum + Hiverge), "Automated near-term quantum algorithm discovery for molecular ground states", submitted **27 Mar 2026** (v1 only), quant-ph + cs.AI, 17 pp: Hive LLM/evolutionary program synthesis finds heuristic ground-state algorithms for LiH, H₂O, F₂; circuits "benchmark[ed] ... on a Quantinuum System Model H2 quantum computer" to "identify minimum system requirements for chemical precision". Abstract page **exists**: https://arxiv.org/abs/2603.26359 (high)
- arXiv:2607.22468 — Koziell-Pipe, Brewer, Guhit et al., "Learning to prepare molecular ground states with transformer models" (24 Jul 2026): ADAPT-GQE generative circuits for imipramine; "We execute generated circuits on Quantinuum Helios-1". (high)
- (adjacent) arXiv:2609.08414 — Butterworth et al., "Efficient quantum state preparation on Quantinuum hardware" (8 Sep 2026): structured (acoustic-signal) state on H2-1, fidelity 0.929 — not chemistry. (high)

Explicitly NOT Quantinuum hardware:
- arXiv:2510.26951 (SKQD for the Schwinger model, Rosanowski et al., 30 Oct 2025): the trapped-ion runs (N=4) were on the Mainz shuttling-based processor (Kaushal et al. 2020), superconducting runs on IBM Heron `ibm_marrakesh`/`ibm_kingston`. (high)
- arXiv:2504.04958 (probabilistic imaginary-time evolution, PRR 7, 043182 (2025)): "a state-of-the-art trapped-ion quantum device" for a 4-site TFIM; a search snippet names H1-1 but the abstract does not. (low)

Could not find (after six targeted searches): any 2024–2026 hardware paper on H2/Helios using real-time
quantum Krylov subspace diagonalisation, sample-based (Krylov) quantum diagonalisation, or QITE for a
molecule, authored by or run on Quantinuum. Quantinuum's own Krylov work is theory: arXiv:2211.16097
"Variational phase estimation with variational fast forwarding" (Fitzpatrick, Filip, Muñoz Ramo; blog
30 Nov 2022, no hardware run). The InQuanto "Quantinuum Systems – QSE" tutorial
(https://docs.quantinuum.com/inquanto/tutorials/InQ_htut_qsys_qse.html) runs on an emulator.

---

## 9. InQuanto

- What: "InQuanto is Quantinuum's state-of-the-art Python-based quantum computational chemistry platform"
  (https://docs.quantinuum.com/inquanto/introduction/overview.html). Backends via Nexus (`InQuanto-Nexus`)
  or pytket extensions; HUGR/Helios/Selene supported since 5.2.0.
- Current version: **InQuanto 6.1.1** (13 Aug 2026, hotfix "Fix result node generation in InQuanto
  generated HUGRs"); 6.1.0 (10 Jul 2026) added `IterativePhaseDiffEstimation` (QPDE); InQuanto-Nexus 1.3.1
  (17 Aug 2026); 5.2.0 (25 Feb 2026) added HUGR-compatible backends (Helios, Selene).
  https://docs.quantinuum.com/inquanto/misc/changelog.html (page header shows 6.1.1). (high)
  (The product-updates blog only has posts up to v3.5.4/v4.0 — do not use it for the current version.)
- Built-in functionality (all in the 6.1.1 manual):
  - **QSE**: `AlgorithmQSE` with `QSEMatricesComputable` (H and S matrices over single-excitation states,
    generalised eigenproblem HC = SCE) — https://docs.quantinuum.com/inquanto/manual/algorithms/algorithms_qse.html ;
    tutorial on Quantinuum Systems emulator: https://docs.quantinuum.com/inquanto/tutorials/InQ_htut_qsys_qse.html
  - **Krylov**: `inquanto.computables.composite.KrylovSubspaceComputable` → `KrylovSubspace`
    (moments ⟨Hⁿ⟩ → Lanczos coefficients/eigenvalues, Green's functions) —
    https://docs.quantinuum.com/inquanto/manual/computables/greens_function.html. This is a moment/Lanczos
    Krylov, NOT a real-time (e^{−iHt}) quantum Krylov diagonalisation.
  - **Imaginary time**: `AlgorithmMcLachlanImagTime` (variational, McLachlan) and `AlgorithmVQS`,
    `AlgorithmMcLachlanRealTime` — https://docs.quantinuum.com/inquanto/manual/algorithms/te_vqs.html.
    No Motta-style QITE class found.
  - **Phase estimation**: `AlgorithmDeterministicQPE`, iterative PE algorithms, phase-estimation protocols,
    `IterativePhaseDiffEstimation` (6.1.0); QEC-QPE knowledge article (`inquanto.experiments.qec_qpe_chem`).
  - **PMSV / SPAM / Qermit**: `inquanto.protocols.PMSV`, `inquanto.protocols.SPAM`, `run_mitres/run_mitex`
    — https://docs.quantinuum.com/inquanto/manual/errmit.html
  - **Helios/Selene tutorial**: https://docs.quantinuum.com/inquanto/tutorials/InQ_tut_helios.html —
    `HeliosConfig(system_name="Helios-1E", max_cost=500, emulator_config=HeliosEmulatorConfig(n_qubits=10))`;
    local Selene via `inquanto.hugr.hugr_utils` (`SELENE.QUEST`).
  - **"Noise forecast"**: could not verify any feature by that name; closest are the resource-estimation
    protocol page (https://docs.quantinuum.com/inquanto/manual/protocols/resource_estimation.html) and the
    emulator noise models (`error_params` / Selene error models).

---

## Loose ends / caveats for the document
1. Quote H2 data-sheet numbers as "typical 1×10⁻³ two-qubit infidelity (v4.00, Sept 2025)"; the web page
   ">99.9%" and the older v2.00 (Oct 2024) "1.5×10⁻³" are superseded.
2. H1-1 is no longer a cloud target (sunset 2025-10-15); use H2-1/H2-2/Helios-1 names.
3. Helios is HQC-metered but dynamically (per executed branch) and `max_cost` is mandatory.
4. "Colour code logical qubits, Nature 2024" is inaccurate: the arXiv is April 2024, Nature publication is
   June 2026 (Nature 654, 349).
5. The tesseract code is [[16,6,4]] used as 4 logical qubits (two sacrificed); the "12 logical qubits" are
   three tesseract blocks.
6. No Quantinuum-hardware Krylov/SQD/QITE chemistry paper exists as of 2026-10-15 (as far as found);
   the closest are the Lanczos-moment Green's-function paper (H1-1) and the Loschmidt-amplitude paper (H2-1).
