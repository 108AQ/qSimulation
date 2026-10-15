"""Circuit-level prototype of the four benchmark arms, written against Quantinuum's stack (pytket).

Arms (see study-notes/quantinuum-krylov-review-and-strategy.pdf):
  (i)   SKQD  : sample bitstrings from Trotterised e^{-iHt_k}|HF>, diagonalise H in the sampled (sector-filtered)
                basis, optionally after one connected-expansion shell; classical control = HF + one shell.
  (ii)  Krylov: coherent quantum Krylov with one-ancilla Hadamard tests of <HF| P U(m dt) |HF>, Toeplitz
                S and H matrices, canonical-orthogonalisation threshold; register measured in qubit-wise
                commuting Pauli bases so that every Hamiltonian term of one basis shares a circuit.
  (iii) QITE  : per-term imaginary-time step fitted from measured Pauli expectations (S a = b), the step
                unitary appended as Pauli rotations; the circuit grows with the number of steps.
  (iv)  SPE   : statistical phase estimation (QCELS-type single-frequency least squares, plus matrix pencil)
                on the survival signal s(m dt) taken from the SAME Hadamard-test shots as arm (ii).

Every circuit is compiled to the H-series native gate set {PhasedX, Rz, ZZPhase} with pytket and costed with
Quantinuum's published formula HQC = 5 + C (N1q + 10 N2q + 5 Nm) / 5000 (C = shots), so the budget axis is
honest even when the run is local.

Backends
  statevector (default, runs here): pytket Circuit.get_statevector(), measurement probabilities computed exactly,
              shots drawn from a multinomial. shots=None gives exact expectation values.
  qnexus      : Quantinuum Nexus (emulators H1-1E/H2-1E/H2-2E/Helios-1E..., hardware H2-1/H2-2/Helios-1).
              Requires `pip install qnexus` and `qnx.login()` once; the code path is written against the
              documented API but has NOT been executed from this server (no credentials).

Usage
  python3 qkrylov_quantinuum.py --instance h2-2q --seeds 50
  python3 qkrylov_quantinuum.py --instance h2-4q --seeds 20
  python3 qkrylov_quantinuum.py --instance h2-2q --backend qnexus --device H2-1E --shots 1000   (later)

Writes code/qkrylov_<instance>_results.json and figures/qkrylov-<instance>-budget.png.
"""
from __future__ import annotations
import argparse, itertools, json, math, time
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np
import scipy.linalg as sla
import scipy.optimize as sopt
from pytket import Circuit, OpType, Qubit
from pytket.circuit import PauliExpBox
from pytket.pauli import Pauli, QubitPauliString
from pytket.utils import QubitPauliOperator
from pytket.passes import DecomposeBoxes, AutoRebase, RemoveRedundancies, FullPeepholeOptimise, SequencePass

OUT = Path(__file__).resolve().parent.parent
CHEM = 1.6e-3
NATIVE = {OpType.ZZPhase, OpType.PhasedX, OpType.Rz}
PAULI = {"I": Pauli.I, "X": Pauli.X, "Y": Pauli.Y, "Z": Pauli.Z}

# ----------------------------------------------------------------------------------------------- Hamiltonians
@dataclass
class Instance:
    name: str
    n_qubits: int
    terms: dict                     # Pauli string (str) -> coefficient (Ha); may include the identity
    hf_bits: str                    # HF occupation, qubit 0 first
    sector: dict = field(default_factory=dict)   # {"n_particles": int, "alpha": [...], "beta": [...]} or {}
    note: str = ""

    @property
    def constant(self):
        return self.terms.get("I" * self.n_qubits, 0.0)

    def operator(self, with_identity=False) -> QubitPauliOperator:
        d = {}
        for s, c in self.terms.items():
            if not with_identity and set(s) == {"I"}:
                continue
            d[QubitPauliString([Qubit(i) for i in range(self.n_qubits)], [PAULI[ch] for ch in s])] = c
        return QubitPauliOperator(d)

    def matrix(self):
        """Dense Hamiltonian including the constant, in pytket's ILO-BE basis ordering (qubit 0 = MSB)."""
        return np.asarray(self.operator(with_identity=True).to_sparse_matrix(self.n_qubits).todense())

    def pauli_terms(self):
        return [(s, c) for s, c in self.terms.items() if set(s) != {"I"}]


def h2_2q() -> Instance:
    """H2, STO-3G, R = 0.735 A, parity mapping + Z2 tapering (electronic energy only). Same as qite_h2.py."""
    return Instance("h2-2q", 2, {"II": -1.052373245772859, "IZ": 0.39793742484318045, "ZI": -0.39793742484318045,
                                 "ZZ": -0.01128010425623538, "XX": 0.18093119978423156},
                    hf_bits="01", sector={},
                    note="tapered 2-qubit H2; HF = |01>; ground state lives in span{|01>,|10>}")


def h2_4q() -> Instance:
    """H2, STO-3G, R = 0.8 A, Jordan-Wigner, 4 spin-orbitals (OpenFermion tutorial Hamiltonian; includes the
    nuclear constant). Qubits 0,1 = spatial orbital 0 (alpha, beta); 2,3 = orbital 1. HF = |1100>."""
    t = {"IIII": -0.1673339890569520, "XXYY": -0.0461566958890153, "XYYX": 0.0461566958890153,
         "YXXY": 0.0461566958890153, "YYXX": -0.0461566958890153, "ZIII": 0.1625164874887164,
         "ZZII": 0.1658325372159041, "ZIZI": 0.1172036472019586, "ZIIZ": 0.1633603430909739,
         "IZII": 0.1625164874887164, "IZZI": 0.1633603430909739, "IZIZ": 0.1172036472019586,
         "IIZI": -0.1974429369975584, "IIZZ": 0.1716978839228672, "IIIZ": -0.1974429369975584}
    return Instance("h2-4q", 4, t, hf_bits="1100",
                    sector={"n_particles": 2, "alpha": [0, 2], "beta": [1, 3]},
                    note="JW 4-qubit H2 (R = 0.8 A), total energy; HF = |1100>")


INSTANCES = {"h2-2q": h2_2q, "h2-4q": h2_4q}

# ----------------------------------------------------------------------------------------------- circuits
def hf_circuit(inst: Instance, n_extra=0) -> Circuit:
    c = Circuit(inst.n_qubits + n_extra)
    for i, b in enumerate(inst.hf_bits):
        if b == "1":
            c.X(i + n_extra)
    return c


def add_pauli_rotation(c: Circuit, pstring: str, theta: float, qubits):
    """Append exp(-i theta P) on the given qubits (P acts on the non-identity positions of pstring)."""
    idx = [q for q, ch in zip(qubits, pstring) if ch != "I"]
    paulis = [PAULI[ch] for ch in pstring if ch != "I"]
    if not idx:
        return
    c.add_pauliexpbox(PauliExpBox(paulis, 2 * theta / math.pi), idx)   # PauliExpBox(t) = exp(-i pi t P / 2)


def trotter_schedule(inst: Instance, t: float, steps: int, order: int):
    """List of (pauli string, angle) implementing exp(-i (H - const) t): first-order (order 1) or symmetric
    second-order (order 2, forward half-step then backward half-step) product formula with `steps` steps."""
    terms = inst.pauli_terms(); sched = []
    for _ in range(steps):
        if order == 1:
            sched += [(s, coeff * t / steps) for s, coeff in terms]
        else:
            sched += [(s, coeff * t / (2 * steps)) for s, coeff in terms]
            sched += [(s, coeff * t / (2 * steps)) for s, coeff in reversed(terms)]
    return sched


def trotter_circuit(inst: Instance, t: float, steps: int, qubits=None, c: Circuit | None = None, order: int = 2) -> Circuit:
    """Trotter approximation of exp(-i (H - const) t) appended to c (or a new circuit)."""
    qubits = list(range(inst.n_qubits)) if qubits is None else qubits
    c = Circuit(inst.n_qubits) if c is None else c
    for s, angle in trotter_schedule(inst, t, steps, order):
        add_pauli_rotation(c, s, angle, qubits)
    return c


def add_controlled_pauli_rotation(c: Circuit, pstring: str, theta: float, qubits, anc):
    """Controlled exp(-i theta P): basis change, CX ladder, CRz(2 theta) on the ladder end, undo.
    Costs 2(w-1) + 2 two-qubit gates for a weight-w string (before optimisation)."""
    idx = [q for q, ch in zip(qubits, pstring) if ch != "I"]
    chars = [ch for ch in pstring if ch != "I"]
    if not idx:
        return
    for q, ch in zip(idx, chars):
        if ch == "X":
            c.H(q)
        elif ch == "Y":
            c.Sdg(q); c.H(q)
    for a, b in zip(idx[:-1], idx[1:]):
        c.CX(a, b)
    c.add_gate(OpType.CRz, 2 * theta / math.pi, [anc, idx[-1]])   # CRz(alpha) = diag(1, exp(-i pi alpha Z/2)) on target when control=1
    for a, b in reversed(list(zip(idx[:-1], idx[1:]))):
        c.CX(a, b)
    for q, ch in zip(idx, chars):
        if ch == "X":
            c.H(q)
        elif ch == "Y":
            c.H(q); c.S(q)


def controlled_trotter(c: Circuit, inst: Instance, t: float, steps: int, qubits, anc, order: int = 2):
    for s, angle in trotter_schedule(inst, t, steps, order):
        add_controlled_pauli_rotation(c, s, angle, qubits, anc)


def hadamard_test_circuit(inst: Instance, m: int, dt: float, steps: int, basis: str, imag: bool, order: int = 2) -> Circuit:
    """Ancilla q0 in |+>, controlled U(m dt) on the register (q1..qn) prepared in HF, ancilla measured in X
    (real part) or Y (imaginary part), register measured in the Pauli basis `basis` (e.g. 'ZZXX').
    <X_anc (x) P> = Re <HF| P U |HF>,  <Y_anc (x) P> = -Im <HF| P U |HF>  for every P diagonal in `basis`."""
    n = inst.n_qubits
    c = hf_circuit(inst, n_extra=1)
    reg = list(range(1, n + 1))
    c.H(0)
    controlled_trotter(c, inst, m * dt, steps, reg, 0, order)
    # ancilla readout basis
    if imag:
        c.Sdg(0)
    c.H(0)
    # register readout basis
    for q, ch in zip(reg, basis):
        if ch == "X":
            c.H(q)
        elif ch == "Y":
            c.Sdg(q); c.H(q)
    return c


def sampling_circuit(inst: Instance, t: float, steps: int, order: int = 2) -> Circuit:
    return trotter_circuit(inst, t, steps, c=hf_circuit(inst), order=order)


def measurement_basis_circuit(base: Circuit, basis: str, qubits=None) -> Circuit:
    c = base.copy()
    qubits = list(range(len(basis))) if qubits is None else qubits
    for q, ch in zip(qubits, basis):
        if ch == "X":
            c.H(q)
        elif ch == "Y":
            c.Sdg(q); c.H(q)
    return c


# ----------------------------------------------------------------------------------------------- compilation / cost
def compile_native(c: Circuit) -> Circuit:
    c = c.copy()
    SequencePass([DecomposeBoxes(), FullPeepholeOptimise(), AutoRebase(NATIVE), RemoveRedundancies()]).apply(c)
    return c


def gate_counts(c: Circuit, n_measured: int) -> dict:
    n2 = c.n_gates_of_type(OpType.ZZPhase) + c.n_gates_of_type(OpType.ZZMax)
    n1 = c.n_gates_of_type(OpType.PhasedX) + c.n_gates_of_type(OpType.Rz)
    return dict(n1q=int(n1), n2q=int(n2), nmeas=int(n_measured), depth=int(c.depth()), depth_2q=int(c.depth_by_type(OpType.ZZPhase)))


def hqc(counts: dict, shots: int) -> float:
    """Quantinuum H-series credit formula (verified 2026-10-15): 5 + C (N1q + 10 N2q + 5 Nm)/5000."""
    return 5 + shots * (counts["n1q"] + 10 * counts["n2q"] + 5 * counts["nmeas"]) / 5000


# ----------------------------------------------------------------------------------------------- backends
class StatevectorBackend:
    """Exact local simulation (runs on this server). A 'job' is a list of (circuit, measured_qubits)."""
    name = "statevector"

    def __init__(self, rng: np.random.Generator):
        self.rng = rng
        self._cache = {}

    def probabilities(self, c: Circuit, measured):
        key = id(c)
        if key not in self._cache:
            psi = c.get_statevector()                       # ILO-BE: qubit 0 is the most significant bit
            # keep a reference to c in the cache: otherwise a freed temporary circuit's id() can be reused
            # by a new circuit and the stale probabilities would be returned
            self._cache[key] = (np.abs(psi) ** 2, c.n_qubits, c)
        p, n, _ = self._cache[key]
        # marginal over measured qubits (ordered as given), as a dict bitstring -> probability
        idx = np.arange(len(p))
        bits = ((idx[:, None] >> (n - 1 - np.array(measured))[None, :]) & 1)
        keys = bits @ (1 << np.arange(len(measured))[::-1])
        marg = np.bincount(keys, weights=p, minlength=1 << len(measured))
        return marg

    def counts(self, c: Circuit, measured, shots):
        """Return {bitstring: count} (bitstring in the order of `measured`); shots=None -> exact probabilities."""
        p = self.probabilities(c, measured)
        p = np.clip(p, 0, None); p /= p.sum()
        if shots is None:
            return {format(i, f"0{len(measured)}b"): float(v) for i, v in enumerate(p) if v > 0}
        cts = self.rng.multinomial(shots, p)
        return {format(i, f"0{len(measured)}b"): int(v) for i, v in enumerate(cts) if v > 0}


class QnexusBackend:
    """Quantinuum Nexus submission path (emulators and hardware). Written against the qnexus API; untested here.
    Install: pip install qnexus ; authenticate once with `qnx.login()` (browser) in the same environment."""
    name = "qnexus"

    def __init__(self, device="H2-1E", project="quantinuum-aq-benchmark", noisy=True):
        import qnexus as qnx                                     # lazy import: optional dependency
        self.qnx = qnx
        self.project = qnx.projects.get_or_create(name=project)
        self.config = qnx.QuantinuumConfig(device_name=device, noisy_simulation=noisy)
        self.device = device

    def counts(self, c: Circuit, measured, shots):
        qnx = self.qnx
        c = c.copy()
        bits = c.add_c_register("c", len(measured))
        for b, q in zip(bits, measured):
            c.Measure(Qubit(q), b)
        ref = qnx.circuits.upload(circuit=c, name=f"{self.device}-{int(time.time())}", project=self.project)
        comp = qnx.start_compile_job(programs=[ref], backend_config=self.config, optimisation_level=2,
                                     name="compile", project=self.project)
        qnx.jobs.wait_for(comp)
        compiled = qnx.jobs.results(comp)[0].get_output()
        job = qnx.start_execute_job(programs=[compiled], n_shots=[shots], backend_config=self.config,
                                    name="execute", project=self.project)
        qnx.jobs.wait_for(job)
        result = qnx.jobs.results(job)[0].download_result()
        return {"".join(str(b) for b in k): int(v) for k, v in result.get_counts().items()}


# ----------------------------------------------------------------------------------------------- measurement helpers
def qwc_groups(strings):
    """Greedy qubit-wise-commuting grouping. Returns list of (basis string, [strings]). Identity letters match anything."""
    groups = []
    for s in strings:
        for g in groups:
            basis = g[0]
            if all(a == "I" or b == "I" or a == b for a, b in zip(s, basis)):
                g[0] = "".join(a if a != "I" else b for a, b in zip(s, basis)); g[1].append(s)
                break
        else:
            groups.append([s, [s]])
    return [(g[0].replace("I", "Z"), g[1]) for g in groups]


def expectation_from_counts(counts: dict, positions) -> float:
    """<P> from Z-basis-rotated counts: parity over the listed bit positions."""
    tot = sum(counts.values())
    if tot == 0:
        return 0.0
    val = 0.0
    for bs, n in counts.items():
        par = sum(int(bs[i]) for i in positions) % 2
        val += (1 - 2 * par) * n
    return val / tot


def pauli_product(a: str, b: str):
    """Product of two Pauli strings: returns (phase, string)."""
    table = {("X", "Y"): (1j, "Z"), ("Y", "Z"): (1j, "X"), ("Z", "X"): (1j, "Y"),
             ("Y", "X"): (-1j, "Z"), ("Z", "Y"): (-1j, "X"), ("X", "Z"): (-1j, "Y")}
    phase, out = 1 + 0j, []
    for x, y in zip(a, b):
        if x == "I":
            out.append(y)
        elif y == "I":
            out.append(x)
        elif x == y:
            out.append("I")
        else:
            ph, ch = table[(x, y)]; phase *= ph; out.append(ch)
    return phase, "".join(out)


# ----------------------------------------------------------------------------------------------- arms
def classical_energy(inst: Instance, basis_states, H):
    idx = sorted(basis_states)
    return float(np.linalg.eigvalsh(H[np.ix_(idx, idx)])[0]), idx


def in_sector(inst: Instance, bitstring: str) -> bool:
    sec = inst.sector
    if not sec:
        return True
    if sum(int(b) for b in bitstring) != sec["n_particles"]:
        return False
    na = sum(int(bitstring[i]) for i in sec["alpha"]); nb = sum(int(bitstring[i]) for i in sec["beta"])
    return na == nb


def connected_shell(inst: Instance, states, H):
    out = set(states)
    for s in states:
        out |= {j for j in np.nonzero(np.abs(H[:, s]) > 1e-12)[0] if in_sector(inst, format(j, f"0{inst.n_qubits}b"))}
    return out


def arm_skqd(inst, H, backend, circuits, shots, shell=True):
    """circuits: list of compiled sampling circuits (one per time point). Returns (energy, dimension, hqc)."""
    n = inst.n_qubits; seen = set(); cost = 0.0
    for c, cnt in circuits:
        counts = backend.counts(c, list(range(n)), shots)
        cost += hqc(cnt, shots if shots else 1)
        seen |= {int(bs, 2) for bs in counts if in_sector(inst, bs)}
    seen |= {int(inst.hf_bits, 2)}
    if shell:
        seen = connected_shell(inst, seen, H)
    e, idx = classical_energy(inst, seen, H)
    return e, len(idx), cost


def hadamard_data(inst, backend, ht_circuits, shots):
    """ht_circuits: dict (m, basis, imag) -> (compiled circuit, counts dict). Returns s[m], h[m] (complex arrays),
    the per-term Pauli expectations and the HQC spent; s uses only the Z-basis circuits (P = I)."""
    K = 1 + max(m for m, _, _ in ht_circuits)
    s = np.zeros(K, complex); h = np.zeros(K, complex); cost = 0.0; cost_s_only = 0.0
    terms = inst.pauli_terms()
    groups = qwc_groups([t for t, _ in terms])
    for m in range(K):
        if m == 0:
            s[0] = 1.0; h[0] = sum(c * (1 if all(ch == "I" or ch == "Z" for ch in t) else 0)
                                   * (-1) ** sum(int(inst.hf_bits[i]) for i, ch in enumerate(t) if ch == "Z")
                                   for t, c in terms)
            continue
        for basis, members in groups:
            for imag in (False, True):
                c, cnt = ht_circuits[(m, basis, imag)]
                counts = backend.counts(c, list(range(inst.n_qubits + 1)), shots)
                cost += hqc(cnt, shots if shots else 1)
                if basis == groups[0][0]:
                    cost_s_only += hqc(cnt, shots if shots else 1)
                # ancilla alone -> survival amplitude (only from the first group, to avoid double counting)
                # <X_anc> = Re<U>, <Y_anc> = +Im<U> (ancilla read in Y via Sdg;H)
                if basis == groups[0][0]:
                    v = expectation_from_counts(counts, [0])
                    s[m] += (1j * v) if imag else v
                for t in members:
                    coeff = dict(terms)[t]
                    pos = [0] + [1 + i for i, ch in enumerate(t) if ch != "I"]
                    v = expectation_from_counts(counts, pos)
                    h[m] += coeff * ((1j * v) if imag else v)
    return s, h, cost, cost_s_only


def toeplitz(x):
    K = len(x)
    return np.array([[x[k - j] if k >= j else np.conj(x[j - k]) for k in range(K)] for j in range(K)])


def arm_krylov(s, h, cutoff=1e-2):
    S, Hm = toeplitz(s), toeplitz(h)
    S, Hm = (S + S.conj().T) / 2, (Hm + Hm.conj().T) / 2
    ev, evec = np.linalg.eigh(S); keep = ev > cutoff * ev.max()
    if keep.sum() == 0:
        return np.nan, 0
    T = evec[:, keep] / np.sqrt(ev[keep])
    return float(np.linalg.eigvalsh(T.conj().T @ Hm @ T)[0]), int(keep.sum())


def arm_spe(s, dt, window):
    """QCELS-type single-frequency fit of s_k ~ r exp(-i E k dt) (r complex), E in `window` (Ha, relative to
    the constant-free Hamiltonian); grid search then local refinement. Also returns the matrix-pencil estimate."""
    k = np.arange(len(s))
    def loss(E):
        z = np.exp(-1j * E * k * dt)
        r = (z.conj() @ s) / len(s)                 # optimal complex amplitude
        return float(np.sum(np.abs(s - r * z) ** 2))
    grid = np.linspace(window[0], window[1], 4001)
    E0 = grid[int(np.argmin([loss(E) for E in grid]))]
    res = sopt.minimize_scalar(loss, bounds=(E0 - 0.05, E0 + 0.05), method="bounded")
    e_qcels = float(res.x) if res.success else float(E0)
    # matrix pencil, rank 2
    K = len(s); L = K // 2
    Yh = sla.hankel(s[:K - L], s[K - L - 1:]); Y0, Y1 = Yh[:, :-1], Yh[:, 1:]
    U, sv, Vh = np.linalg.svd(Y0, full_matrices=False); r = min(2, len(sv))
    A = np.diag(1 / sv[:r]) @ U[:, :r].conj().T @ Y1 @ Vh[:r].conj().T
    e_mp = float(np.min(-np.angle(np.linalg.eigvals(A)) / dt))
    return e_qcels, e_mp


def qite_pool(inst: Instance):
    if inst.n_qubits == 2:
        return [s for s in ("".join(p) for p in itertools.product("IXYZ", repeat=2)) if s.count("Y") % 2 == 1]
    # 4-qubit JW H2: the ground state is HF + a double excitation; weight-4 odd-Y strings generate it
    return [s for s in ("".join(p) for p in itertools.product("XY", repeat=4)) if s.count("Y") % 2 == 1]


def arm_qite(inst, H, backend, shots, dtau, nsteps, ridge, seed_rng):
    """Per-term QITE (Motta et al.) with Pauli expectations measured from circuits. Returns trajectory, cost per step."""
    n = inst.n_qubits; pool = qite_pool(inst); terms = inst.pauli_terms()
    base = hf_circuit(inst)                                   # grows by one Pauli rotation per pool element per term
    energies, costs, counts2q = [], [], []
    # strings needed for S (products) and b (products with the term), grouped once
    prod_cache = {}
    def product(a, b):
        if (a, b) not in prod_cache:
            prod_cache[(a, b)] = pauli_product(a, b)
        return prod_cache[(a, b)]
    def measure_expectations(circ, strings):
        """Expectation values of a set of Pauli strings on the state prepared by circ (statevector or sampled)."""
        groups = qwc_groups([s for s in strings if set(s) != {"I"}])
        vals = {"I" * n: 1.0}; cost = 0.0
        for basis, members in groups:
            mc = compile_native(measurement_basis_circuit(circ, basis))
            cnt = gate_counts(mc, n)
            counts = backend.counts(mc, list(range(n)), shots)
            cost += hqc(cnt, shots if shots else 1)
            for s in members:
                vals[s] = expectation_from_counts(counts, [i for i, ch in enumerate(s) if ch != "I"])
        return vals, cost
    def energy(circ):
        vals, cost = measure_expectations(circ, [t for t, _ in terms])
        return inst.constant + sum(c * vals[t] for t, c in terms), cost
    e, cost = energy(base); energies.append(e); costs.append(cost); counts2q.append(gate_counts(compile_native(base), n)["n2q"])
    for step in range(nsteps):
        step_cost = 0.0
        for t, alpha in terms:
            needed = set()
            for a in pool:
                for b in pool:
                    needed.add(product(a, b)[1])
                needed.add(product(a, t)[1])
            needed.add(t)
            vals, cost = measure_expectations(base, needed); step_cost += cost
            # S_{mu nu} = Re <sigma_mu sigma_nu>, b_mu = sinh(dtau alpha)/(dtau sqrt(c)) Im <sigma_mu P>
            S = np.zeros((len(pool), len(pool)))
            for i, a in enumerate(pool):
                for j, b in enumerate(pool):
                    ph, s = product(a, b); S[i, j] = np.real(ph * vals[s])
            c_norm = math.cosh(2 * dtau * alpha) - math.sinh(2 * dtau * alpha) * vals[t]
            bvec = np.zeros(len(pool))
            for i, a in enumerate(pool):
                ph, s = product(a, t); bvec[i] = math.sinh(dtau * alpha) / (dtau * math.sqrt(max(c_norm, 1e-12))) * np.imag(ph * vals[s])
            avec = np.linalg.solve(S + ridge * np.eye(len(pool)), bvec)
            for a_coeff, pstr in zip(avec, pool):
                if abs(a_coeff) > 1e-10:
                    add_pauli_rotation(base, pstr, dtau * a_coeff, list(range(n)))
        e, cost = energy(base); step_cost += cost
        energies.append(e); costs.append(step_cost); counts2q.append(gate_counts(compile_native(base), n)["n2q"])
    return np.array(energies), np.array(costs), counts2q


# ----------------------------------------------------------------------------------------------- experiment
def build_circuits(inst, K, dt, steps, K_spe=None, order=2):
    """Compile all circuits once. Returns sampling circuits (K time points), Hadamard-test circuits for the
    Krylov arm (m = 1..K-1, every measurement basis, Re and Im) and the Z-basis-only Hadamard tests for the
    statistical-PE arm on its own, longer grid (m = 1..K_spe-1; the first K-1 are shared with Krylov)."""
    n = inst.n_qubits; K_spe = K_spe or K
    samp = []
    for k in range(K):
        c = compile_native(sampling_circuit(inst, k * dt, steps, order)); samp.append((c, gate_counts(c, n)))
    groups = qwc_groups([t for t, _ in inst.pauli_terms()])
    ht = {}
    for m in range(1, K):
        for basis, _ in groups:
            for imag in (False, True):
                c = compile_native(hadamard_test_circuit(inst, m, dt, steps, basis, imag, order))
                ht[(m, basis, imag)] = (c, gate_counts(c, n + 1))
    spe = {}
    for m in range(1, K_spe):
        for imag in (False, True):
            key = (m, groups[0][0], imag)
            if key in ht:
                spe[(m, imag)] = ht[key]
            else:
                c = compile_native(hadamard_test_circuit(inst, m, dt, steps, groups[0][0], imag, order))
                spe[(m, imag)] = (c, gate_counts(c, n + 1))
    return samp, ht, spe, groups


def survival_data(inst, backend, spe_circuits, shots):
    """Survival amplitudes s(m dt) from ancilla-only readout of the Z-basis Hadamard tests; returns (s, HQC)."""
    K = 1 + max(m for m, _ in spe_circuits)
    s = np.zeros(K, complex); s[0] = 1.0; cost = 0.0
    for m in range(1, K):
        for imag in (False, True):
            c, cnt = spe_circuits[(m, imag)]
            counts = backend.counts(c, list(range(inst.n_qubits + 1)), shots)
            cost += hqc(cnt, shots if shots else 1)
            v = expectation_from_counts(counts, [0])
            s[m] += (1j * v) if imag else v
    return s, cost


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", default="h2-2q", choices=list(INSTANCES))
    ap.add_argument("--backend", default="statevector", choices=["statevector", "qnexus"])
    ap.add_argument("--device", default="H2-1E")
    ap.add_argument("--seeds", type=int, default=50)
    ap.add_argument("--shots", type=int, nargs="*", default=[100, 300, 1000, 3000, 10000])
    ap.add_argument("--K", type=int, default=None, help="number of Krylov time points (default per instance)")
    ap.add_argument("--K-spe", type=int, default=None, help="time points for the statistical-PE arm on its own grid (default 2K)")
    ap.add_argument("--dt", type=float, default=None)
    ap.add_argument("--trotter", type=int, default=None, help="Trotter steps per circuit")
    ap.add_argument("--trotter-order", type=int, default=2, choices=[1, 2])
    ap.add_argument("--cutoff", type=float, default=1e-3)
    ap.add_argument("--qite-steps", type=int, default=8)
    ap.add_argument("--qite-dtau", type=float, default=0.2)
    ap.add_argument("--qite-ridge", type=float, default=0.1)
    args = ap.parse_args()

    inst = INSTANCES[args.instance]()
    defaults = {"h2-2q": dict(K=6, dt=0.5, trotter=2), "h2-4q": dict(K=6, dt=0.5, trotter=2)}[args.instance]
    K = args.K or defaults["K"]; dt = args.dt or defaults["dt"]; steps = args.trotter or defaults["trotter"]
    K_spe = args.K_spe or 2 * K; order = args.trotter_order
    H = inst.matrix(); w, V = np.linalg.eigh(H); E_fci = float(w[0])
    hf_index = int(inst.hf_bits, 2); E_hf = float(H[hf_index, hf_index].real)
    overlap = float(abs(V[hf_index, 0]) ** 2)
    print(f"{inst.name}: E_FCI = {E_fci:.6f}  E_HF = {E_hf:.6f}  |<HF|E0>|^2 = {overlap:.4f}  K={K} K_spe={K_spe} dt={dt} "
          f"trotter={steps} (order {order})")
    window = (E_hf - inst.constant - 0.5, E_hf - inst.constant + 0.1)      # QCELS search window from HF, not from the answer

    rng = np.random.default_rng(2026)
    backend = StatevectorBackend(rng) if args.backend == "statevector" else QnexusBackend(args.device)

    # sanity: Trotter circuit vs exact propagator; Hadamard-test sign conventions (exact expectations)
    t0 = time.time()
    samp, ht, spe, groups = build_circuits(inst, K, dt, steps, K_spe, order)
    n_extra = sum(1 for k in spe if k[0] >= K)
    print(f"built and compiled {len(samp)} sampling + {len(ht)} Hadamard-test + {n_extra} extra SPE circuits in "
          f"{time.time()-t0:.1f}s; measurement bases per time point: {[g[0] for g in groups]}")
    exact_backend = StatevectorBackend(np.random.default_rng(0))
    Hc = H - inst.constant * np.eye(len(H))
    hf = np.zeros(len(H), complex); hf[hf_index] = 1
    s_ex = np.array([hf.conj() @ sla.expm(-1j * Hc * m * dt) @ hf for m in range(K_spe)])
    s_m, h_m, _, _ = hadamard_data(inst, exact_backend, ht, None)
    s_long, _ = survival_data(inst, exact_backend, spe, None)
    trotter_err = float(np.max(np.abs(s_long - s_ex)))
    print(f"max |s_trotter - s_exact| over the SPE grid = {trotter_err:.2e} (Trotter + sign-convention check)")
    e_kr_exact, rank = arm_krylov(s_m, h_m, args.cutoff)
    e_spe_exact, e_mp_exact = arm_spe(s_m, dt, window)
    e_spe_long_exact, _ = arm_spe(s_long, dt, window)
    print(f"noiseless (shots=None): Krylov {e_kr_exact + inst.constant - E_fci:+.2e} Ha (rank {rank}), "
          f"QCELS same data {e_spe_exact + inst.constant - E_fci:+.2e}, QCELS own grid {e_spe_long_exact + inst.constant - E_fci:+.2e}, "
          f"pencil {e_mp_exact + inst.constant - E_fci:+.2e}")

    # classical control
    hf_shell = connected_shell(inst, {hf_index}, H)
    e_shell, idx_shell = classical_energy(inst, hf_shell, H)
    print(f"classical control HF + one shell: dim {len(idx_shell)}, error {e_shell - E_fci:+.2e} Ha")

    # per-circuit ledger
    ledger = {"sampling": [dict(t=k * dt, **cnt, hqc_1000=hqc(cnt, 1000)) for k, (c, cnt) in enumerate(samp)],
              "hadamard": [dict(m=m, basis=b, imag=im, **cnt, hqc_1000=hqc(cnt, 1000)) for (m, b, im), (c, cnt) in ht.items()],
              "spe_extra": [dict(m=m, imag=im, **cnt, hqc_1000=hqc(cnt, 1000)) for (m, im), (c, cnt) in spe.items() if m >= K]}

    results = dict(instance=inst.name, note=inst.note, E_FCI=E_fci, E_HF=E_hf, overlap_HF=overlap, K=K, K_spe=K_spe, dt=dt,
                   trotter_steps=steps, trotter_order=order, cutoff=args.cutoff, trotter_check=trotter_err,
                   qcels_window=window, backend=backend.name,
                   classical_control=dict(dim=len(idx_shell), err=e_shell - E_fci),
                   noiseless=dict(krylov=e_kr_exact + inst.constant - E_fci, krylov_rank=rank,
                                  qcels_same=e_spe_exact + inst.constant - E_fci, qcels_long=e_spe_long_exact + inst.constant - E_fci,
                                  pencil=e_mp_exact + inst.constant - E_fci),
                   ledger=ledger, arms={})

    # budget sweep (shots per circuit); every seed re-samples all circuits
    for shots in args.shots:
        rows = {"skqd": [], "skqd_noshell": [], "krylov": [], "spe_qcels_same": [], "spe_pencil_same": [], "spe_qcels": []}
        for seed in range(args.seeds):
            e, dim, cost = arm_skqd(inst, H, backend, samp, shots, shell=True); rows["skqd"].append((e - E_fci, cost, dim))
            e, dim, cost = arm_skqd(inst, H, backend, samp, shots, shell=False); rows["skqd_noshell"].append((e - E_fci, cost, dim))
            s, h, cost, cost_s = hadamard_data(inst, backend, ht, shots)
            e, rank = arm_krylov(s, h, args.cutoff); rows["krylov"].append((e + inst.constant - E_fci, cost, rank))
            eq, emp = arm_spe(s, dt, window)
            rows["spe_qcels_same"].append((eq + inst.constant - E_fci, cost_s, K)); rows["spe_pencil_same"].append((emp + inst.constant - E_fci, cost_s, K))
            s2, cost2 = survival_data(inst, backend, spe, shots)
            eq2, _ = arm_spe(s2, dt, window); rows["spe_qcels"].append((eq2 + inst.constant - E_fci, cost2, K_spe))
        summ = {}
        for arm, r in rows.items():
            a = np.array([x[0] for x in r]); cost = float(np.mean([x[1] for x in r])); aux = float(np.mean([x[2] for x in r]))
            a_ok = a[np.isfinite(a)]
            summ[arm] = dict(hqc=cost, median_abs_err=float(np.median(np.abs(a_ok))), p25=float(np.percentile(np.abs(a_ok), 25)),
                             p75=float(np.percentile(np.abs(a_ok), 75)), frac_chem=float(np.mean(np.abs(a_ok) < CHEM)),
                             frac_below=float(np.mean(a_ok < -CHEM)), aux=aux, n=int(a_ok.size))
        results["arms"][str(shots)] = summ
        print(f"shots/circuit {shots:>6}: " + "  ".join(f"{k}: med {v['median_abs_err']*1e3:6.2f} mHa, P(chem) {v['frac_chem']:.2f}, HQC {v['hqc']:8.0f}" for k, v in summ.items()))

    # QITE arm: a few seeds per shot budget (slower: circuits are rebuilt per step)
    results["qite"] = {}
    for shots in args.shots:
        traj, cost, n2q = [], None, None
        nseed = max(3, args.seeds // 10)
        for seed in range(nseed):
            e, c, n2 = arm_qite(inst, H, backend, shots, args.qite_dtau, args.qite_steps, args.qite_ridge, rng)
            traj.append(e - E_fci); cost = c; n2q = n2
        traj = np.array(traj)
        results["qite"][str(shots)] = dict(err_median_per_step=np.median(np.abs(traj), axis=0).tolist(),
                                           frac_chem_final=float(np.mean(np.abs(traj[:, -1]) < CHEM)),
                                           hqc_per_step=cost.tolist(), hqc_cumulative=np.cumsum(cost).tolist(),
                                           n2q_per_step=n2q, seeds=nseed, dtau=args.qite_dtau, ridge=args.qite_ridge)
        print(f"QITE shots {shots:>6}: final median err {np.median(np.abs(traj[:, -1]))*1e3:.2f} mHa, "
              f"P(chem) {np.mean(np.abs(traj[:, -1]) < CHEM):.2f}, cumulative HQC {np.cumsum(cost)[-1]:.0f}, 2q gates/step {n2q}")
    e_exact_qite, _, _ = arm_qite(inst, H, exact_backend, None, args.qite_dtau, args.qite_steps, args.qite_ridge, rng)
    results["qite"]["noiseless_err_per_step"] = (e_exact_qite - E_fci).tolist()

    out = OUT / "code" / f"qkrylov_{inst.name}_results.json"
    out.write_text(json.dumps(results, indent=1, default=float))
    print("wrote", out)
    plot(results, inst)


def plot(results, inst):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    style = {"skqd": ("#2a78d6", "o-", "SKQD (sample + 1 shell)"), "krylov": ("#eb6834", "s-", f"coherent Krylov (K={results['K']})"),
             "spe_qcels_same": ("#1baf7a", "v:", "statistical PE, QCELS on the Krylov data"),
             "spe_qcels": ("#1baf7a", "^-", f"statistical PE, QCELS, own grid (K={results['K_spe']}, Z-basis only)")}
    for arm, (col, mk, lab) in style.items():
        xs = [v[arm]["hqc"] for v in results["arms"].values()]
        med = [max(v[arm]["median_abs_err"], 1e-7) for v in results["arms"].values()]
        lo = [max(v[arm]["p25"], 1e-7) for v in results["arms"].values()]; hi = [max(v[arm]["p75"], 1e-7) for v in results["arms"].values()]
        ax[0].plot(xs, med, mk, color=col, ms=4, label=lab); ax[0].fill_between(xs, lo, hi, color=col, alpha=0.15)
        ax[1].plot(xs, [v[arm]["frac_chem"] for v in results["arms"].values()], mk, color=col, ms=4, label=lab)
    q = results["qite"]; shots_keys = [k for k in q if k != "noiseless_err_per_step"]
    xs = [q[k]["hqc_cumulative"][-1] for k in shots_keys]; med = [max(q[k]["err_median_per_step"][-1], 1e-7) for k in shots_keys]
    ax[0].plot(xs, med, "D-", color="#9a4bd6", ms=4, label=f"QITE ({q[shots_keys[0]]['seeds']} seeds)")
    ax[1].plot(xs, [q[k]["frac_chem_final"] for k in shots_keys], "D-", color="#9a4bd6", ms=4, label="QITE")
    cc = abs(results["classical_control"]["err"])
    ax[0].axhline(max(cc, 1e-7), color="gray", ls="-.", lw=1, label=f"classical control (HF + 1 shell, dim {results['classical_control']['dim']})")
    ax[0].axhline(CHEM, color="black", ls="--", lw=1); ax[0].text(ax[0].get_xlim()[0] * 1.5 if ax[0].get_xlim()[0] > 0 else 10, CHEM * 1.3, "chemical accuracy", fontsize=7)
    ax[0].set_xscale("log"); ax[0].set_yscale("log"); ax[0].set_xlabel("cumulative HQC (published formula, compiled native gates)")
    ax[0].set_ylabel(r"$|E - E_{\rm FCI}|$ (Ha), median and IQR"); ax[0].legend(fontsize=6.5, frameon=False)
    ax[1].set_xscale("log"); ax[1].set_xlabel("cumulative HQC"); ax[1].set_ylabel("P(within 1.6 mHa)"); ax[1].set_ylim(-0.02, 1.02)
    fig.suptitle(f"{inst.name}: error versus hardware cost, local statevector backend with sampled shots (not hardware)", fontsize=9)
    fig.tight_layout(); fig.savefig(OUT / "figures" / f"qkrylov-{inst.name}-budget.png", dpi=200)
    print("wrote figure")


if __name__ == "__main__":
    main()
