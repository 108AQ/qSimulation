"""Toy numerical checks behind study-notes/quantinuum-krylov-review-and-strategy.tex
(formerly two separate scripts, merged on 2026-10-15; results unchanged).

Model: the same 2-qubit H2 Hamiltonian as qite_h2.py (STO-3G, R = 0.735 A, parity mapping + Z2
tapering, electronic energy only), Hartree-Fock start |01>. Statevector emulation; shot noise is a
Gaussian model of Hadamard-test / sampling statistics. NOT a hardware result.

Checks (section labels match the document):
  A. kappa(S) of the real-time Krylov overlap matrix vs dimension K and time step dt.
  B. Shot noise + Gram-matrix thresholding on the coherent Krylov eigenproblem (300 seeds).
  C. Sampled-basis (SKQD-style, S = I) path vs a classical-only control (HF + one connected shell).
  D. Arithmetic re-check of the SKQD report's HQC estimate, Eqs. (9)-(10), and its 'survival fidelity'.
  E. Statistical phase estimation (matrix pencil) vs coherent Krylov built from the SAME noisy
     survival signal s(t_k) = <psi0|e^{-iHt_k}|psi0> (plus h(t_k) = <psi0|H e^{-iHt_k}|psi0> for Krylov).
  F. Iterative (Kitaev) QPE with one ancilla: energy error vs the coherent evolution length it needs.
  G. HQC cost of representative circuits from Quantinuum's published formula
     HQC = 5 + C (N1q + 10 N2q + 5 Nm) / 5000, C = shots.
Writes code/krylov_toy_checks_h2_results.json, figures/krylov-conditioning-h2.png and
figures/spe-vs-krylov-h2.png.
"""
import json, numpy as np, scipy.linalg as sla
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent
I2 = np.eye(2); X = np.array([[0, 1], [1, 0]]); Y = np.array([[0, -1j], [1j, 0]]); Z = np.diag([1., -1.])
P1 = {"I": I2, "X": X, "Y": Y, "Z": Z}
def pauli(s):
    M = np.array([[1.]])
    for c in s: M = np.kron(M, P1[c])
    return M

coef = {"II": -1.052373245772859, "IZ": 0.39793742484318045, "ZI": -0.39793742484318045,
        "ZZ": -0.01128010425623538, "XX": 0.18093119978423156}
terms = [(k, pauli(k), v) for k, v in coef.items()]
H = sum(v * pauli(k) for k, v in coef.items())
w, V = np.linalg.eigh(H); E0 = w[0]
psi0 = np.zeros(4, complex); psi0[int(np.argmin(np.diag(H).real))] = 1.0      # HF = lowest diagonal = |01>
CHEM = 1.6e-3
lam = sum(abs(v) for k, v in coef.items() if k != "II")                        # 1-norm without identity
res = {"E_FCI_electronic": float(E0), "E_HF": float(np.real(psi0.conj() @ H @ psi0)), "chem_acc_Ha": CHEM,
       "lambda_1norm": float(lam),
       "spectrum_and_overlaps": [(float(w[n]), float(abs(V[:, n].conj() @ psi0) ** 2)) for n in range(4)]}

def krylov_states(dt, K):
    U = sla.expm(-1j * H * dt); vs = [psi0]
    for _ in range(K - 1): vs.append(U @ vs[-1])
    return np.array(vs).T                                   # columns = |psi(t_k)>

def ritz(Hm, Sm, thr):
    """Canonical orthogonalisation: drop Gram eigenvalues below thr * max. Returns (E, retained rank)."""
    ev, evec = np.linalg.eigh(Sm); keep = ev > thr * ev.max()
    T = evec[:, keep] / np.sqrt(ev[keep])
    return float(np.linalg.eigvalsh(T.conj().T @ Hm @ T)[0]), int(keep.sum())

# ================================================================ A. exact conditioning
res["A_kappa_S_exact"] = {}
for dt in (0.1, 0.5, 1.0):
    row = {}
    for K in (2, 3, 4, 5):
        B = krylov_states(dt, K); Sm = B.conj().T @ B
        ev = np.linalg.eigvalsh(Sm); ev = np.maximum(ev, 1e-300)
        row[K] = float(ev.max() / ev.min())
    res["A_kappa_S_exact"][str(dt)] = row

# ================================================================ B. shot noise + threshold
def noisy_matrices(dt, K, N, rng):
    """Hadamard-test model: every Toeplitz element <psi0|P e^{-iH m dt}|psi0> (m = 0..K-1), real and
    imaginary part, estimated from N shots of a +-1 observable: Gaussian noise, var = (1-mean^2)/N.
    H is assembled from its 5 Pauli terms, each estimated separately (identity term is exact)."""
    U = sla.expm(-1j * H * dt)
    def est(m):
        var = max(1.0 - m.real**2, 1e-12) / N, max(1.0 - m.imag**2, 1e-12) / N
        return m + rng.normal(0, np.sqrt(var[0])) + 1j * rng.normal(0, np.sqrt(var[1]))
    s_el, h_el = [], []
    v = psi0.copy()
    for m in range(K):
        s_el.append(1.0 + 0j if m == 0 else est(psi0.conj() @ v))
        h = 0j
        for name, P, c in terms:
            h += c * (psi0.conj() @ P @ v if name == "II" else est(psi0.conj() @ P @ v))
        h_el.append(h); v = U @ v
    Sm = np.zeros((K, K), complex); Hm = np.zeros((K, K), complex)
    for j in range(K):
        for k in range(K):
            m = k - j
            Sm[j, k] = s_el[m] if m >= 0 else np.conj(s_el[-m])
            Hm[j, k] = h_el[m] if m >= 0 else np.conj(h_el[-m])
    return Hm, Sm

rng_b = np.random.default_rng(20261015); NSEED = 300
thresholds = [1e-12, 1e-3, 1e-2, 1e-1]
res["B_noisy_krylov"] = {}
for dt in (0.5,):
    for K in (2, 3, 4):
        for N in (10**2, 10**3, 10**4, 10**5):
            errs = {t: [] for t in thresholds}; ranks = {t: [] for t in thresholds}
            for _ in range(NSEED):
                Hm, Sm = noisy_matrices(dt, K, N, rng_b)
                for t in thresholds:
                    try:
                        e, r = ritz(Hm, Sm, t)
                    except Exception:
                        e, r = np.nan, 0
                    errs[t].append(e - E0); ranks[t].append(r)
            for t in thresholds:
                a = np.array(errs[t]); a = a[np.isfinite(a)]
                res["B_noisy_krylov"][f"dt={dt},K={K},N={N},thr={t:g}"] = dict(
                    median_abs_err=float(np.median(np.abs(a))),
                    p90_abs_err=float(np.percentile(np.abs(a), 90)),
                    frac_within_chem=float(np.mean(np.abs(a) < CHEM)),
                    frac_below_E0_by_chem=float(np.mean(a < -CHEM)),       # unphysical: below the true ground energy
                    mean_rank=float(np.mean(ranks[t])), n_fail=int(NSEED - a.size))

# ================================================================ C. sampled basis vs classical control
basis_labels = ["00", "01", "10", "11"]
def diag_in(subset):
    idx = sorted(subset); Hs = H[np.ix_(idx, idx)]
    return float(np.linalg.eigvalsh(Hs)[0]), [basis_labels[i] for i in idx]

hf = int(np.argmax(np.abs(psi0)))
# classical control: HF plus every basis state coupled to it by H (one connected shell), no quantum sampling
shell1 = {hf} | {j for j in range(4) if abs(H[j, hf]) > 1e-12 and j != hf}
e_hf, _ = diag_in({hf}); e_shell, lab_shell = diag_in(shell1)
res["C_classical_control"] = dict(HF_only_err=e_hf - E0, HF_plus_one_shell=dict(space=lab_shell, err=e_shell - E0))
res["C_sampled_basis"] = {}
rng_c = np.random.default_rng(1)
for N in (10, 100, 1024):
    B = krylov_states(0.5, 4); seen = set()
    for k in range(4):
        p = np.abs(B[:, k])**2; p /= p.sum()
        counts = rng_c.multinomial(N, p); seen |= {j for j in range(4) if counts[j] > 0}
    e, lab = diag_in(seen)
    seen_noisy = set(seen)                        # readout-noise variant: 1% bit flips -> other sectors
    for k in range(4):
        p = np.abs(B[:, k])**2; p /= p.sum(); counts = rng_c.multinomial(N, p)
        for j in range(4):
            for _ in range(counts[j]):
                b = j ^ (1 if rng_c.random() < 0.01 else 0) ^ (2 if rng_c.random() < 0.01 else 0)
                seen_noisy.add(b)
    e_n, lab_n = diag_in(seen_noisy)
    res["C_sampled_basis"][str(N)] = dict(space=lab, err=e - E0, with_1pct_readout_noise=dict(space=lab_n, err=e_n - E0))

# ================================================================ D. arithmetic re-checks of the report
N2Q, shots, Nmeas = 5436, 1024, 12
hqc = {}
for n1q in (0, N2Q, 2 * N2Q):
    hqc[f"N1Q={n1q}"] = dict(eq9_denominator_500=(5 + n1q / 10 + N2Q + 5 * Nmeas) * shots / 500,
                             eq10_denominator_336=N2Q * shots / 336)
hqc["report_per_circuit"] = 16568; hqc["report_batch_total"] = 82862.17
hqc["batch_total_over_6"] = 82862.17 / 6; hqc["batch_total_over_5"] = 82862.17 / 5
hqc["official_form_N1Q=N2Q"] = 5 + (N2Q + 10 * N2Q + 5 * Nmeas) / 5000 * shots
res["D_hqc_check"] = hqc
p = 1 - (3e-4) ** (1 / 5436)                     # 'survival fidelity': (1-p)^5436 = 3e-4
res["D_fidelity_check"] = dict(p_2q_implied_by_0p03pct=p, survival_150_gates=(1 - p) ** 150,
                               survival_204_gates=(1 - p) ** 204, survival_150_at_p_1e_3=(1 - 1e-3) ** 150)

# ================================================================ E. SPE vs coherent Krylov on the same data
def survival(ts): return np.array([psi0.conj() @ sla.expm(-1j * H * t) @ psi0 for t in ts])
def h_signal(ts): return np.array([psi0.conj() @ H @ sla.expm(-1j * H * t) @ psi0 for t in ts])

def matrix_pencil(s, dt, L=None, rank=2):
    """Frequencies (energies) of a uniformly sampled signal s_k = sum_n a_n e^{-i E_n k dt}."""
    K = len(s); L = L or K // 2
    Yh = sla.hankel(s[:K - L], s[K - L - 1:])
    Y0, Y1 = Yh[:, :-1], Yh[:, 1:]
    U, sv, Vh = np.linalg.svd(Y0, full_matrices=False)
    r = min(rank, len(sv)); U, sv, Vh = U[:, :r], sv[:r], Vh[:r]
    A = np.diag(1 / sv) @ U.conj().T @ Y1 @ Vh.conj().T
    return np.sort(-np.angle(np.linalg.eigvals(A)) / dt)

def krylov_from_signals(s, h, dt, cutoff=1e-3):
    """Coherent QKSD on t_0..t_{K-1}, K = len(s)//2, Toeplitz S_jk = s(t_k - t_j), H_jk = h(t_k - t_j)."""
    K = len(s) // 2
    def toep(x): return np.array([[x[k - j] if k >= j else np.conj(x[j - k]) for k in range(K)] for j in range(K)])
    S, Hm = toep(s), toep(h)
    S, Hm = (S + S.conj().T) / 2, (Hm + Hm.conj().T) / 2
    ev, evec = np.linalg.eigh(S); keep = ev > cutoff * ev.max()
    if keep.sum() == 0: return np.nan
    T = evec[:, keep] / np.sqrt(ev[keep])
    return float(np.linalg.eigvalsh(T.conj().T @ Hm @ T)[0])

rng_e = np.random.default_rng(11)
dt_e, K_e = 0.3, 24
ts = dt_e * np.arange(K_e); s_exact = survival(ts); h_exact = h_signal(ts)
res["E_setup"] = dict(dt=dt_e, K=K_e, max_evolution_time=float(ts[-1]), seeds=300,
                      exact_pencil_err=float(matrix_pencil(s_exact, dt_e)[0] - E0),
                      shots_total={"spe": "2*K*N (Re and Im of s(t_k))", "krylov": "4*K*N at least (s and h series)"})
res["E_spe"], res["E_krylov_same_data"] = {}, {}
for N in (10**3, 10**4, 10**5):
    e_spe, e_kr = [], []
    for _ in range(300):
        noise = (rng_e.normal(0, 1 / np.sqrt(N), K_e) + 1j * rng_e.normal(0, 1 / np.sqrt(N), K_e))
        s = s_exact + noise; s[0] = 1.0
        # h(t) treated as ONE observable of norm lam measured with N shots (optimistic for Krylov)
        h = h_exact + lam * (rng_e.normal(0, 1 / np.sqrt(N), K_e) + 1j * rng_e.normal(0, 1 / np.sqrt(N), K_e))
        e_spe.append(matrix_pencil(s, dt_e)[0] - E0)
        e_kr.append(krylov_from_signals(s, h, dt_e) - E0)
    e_spe, e_kr = np.array(e_spe), np.array(e_kr)
    for name, e in (("E_spe", e_spe), ("E_krylov_same_data", e_kr)):
        res[name][str(N)] = dict(median_abs_err=float(np.nanmedian(np.abs(e))),
                                 frac_chem_acc=float(np.nanmean(np.abs(e) < CHEM)),
                                 frac_below_E0=float(np.nanmean(e < -CHEM)))

# ================================================================ F. iterative QPE depth check
Emin, Erange = -2.0, 2.0                          # window covering the spectrum [-1.86, -0.22]
Hs = (H - Emin * np.eye(4)) / Erange              # eigenvalues in [0, 1)
U1 = sla.expm(-2j * np.pi * Hs)                   # one unit of evolution: eigenphase e^{-2 pi i phi}
def iqpe_bits(nbits, shots):
    """Kitaev IQPE on the exact ground state (isolates the depth question from the overlap question)."""
    gs = V[:, 0]; phi_true = (E0 - Emin) / Erange; phi_est = 0.0
    for m in range(nbits, 0, -1):                 # least significant bit first
        Um = np.linalg.matrix_power(U1, 2 ** (m - 1))
        omega = np.pi * phi_est                   # known lower bits enter as 0.0 b_{m+1}... = f/2
        amp = gs.conj() @ Um @ gs                 # = e^{-2 pi i 2^{m-1} phi}
        p0 = 0.5 * (1 + np.real(amp * np.exp(1j * omega)))
        bit = int(rng_e.binomial(shots, 1 - np.clip(p0, 0, 1)) > shots / 2)
        phi_est = (phi_est + bit) / 2
    return phi_est, phi_true
nb = 12; phi_est, phi_true = iqpe_bits(nb, shots=50)
res["F_iqpe"] = dict(nbits=nb, shots_per_bit=50, phi_true=float(phi_true), phi_est=float(phi_est),
                     energy_err=float(abs(phi_est - phi_true) * Erange), longest_evolution_units=2 ** (nb - 1),
                     overlap_gs=float(abs(V[:, 0].conj() @ psi0) ** 2))

# ================================================================ G. HQC envelope (published formula)
def hqc_cost(n1q, n2q, nm, C): return 5 + C * (n1q + 10 * n2q + 5 * nm) / 5000
res["G_hqc_examples"] = {
    "hadamard_test_8q_300twoq_1000shots": hqc_cost(600, 300, 9, 1000),
    "hadamard_test_8q_300twoq_10000shots": hqc_cost(600, 300, 9, 10000),
    "sampling_circuit_8q_150twoq_1000shots": hqc_cost(300, 150, 8, 1000),
    "qite_step_prefix_8q_600twoq_1000shots": hqc_cost(1200, 600, 8, 1000),
    "spe_24points_8q_300twoq_10000shots_total": 24 * 2 * hqc_cost(600, 300, 9, 10000),
}

(OUT / "code" / "krylov_toy_checks_h2_results.json").write_text(json.dumps(res, indent=1))
print(json.dumps({k: res[k] for k in ("E_spe", "E_krylov_same_data", "F_iqpe", "G_hqc_examples")}, indent=1))

# ================================================================ figures
COL = {"1e-12": "#2a78d6", "0.001": "#eb6834", "0.01": "#1baf7a", "0.1": "#eda100"}
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 2, figsize=(8.2, 3.2))
Ns = [10**2, 10**3, 10**4, 10**5]
for t in thresholds:
    med = [res["B_noisy_krylov"][f"dt=0.5,K=3,N={N},thr={t:g}"]["median_abs_err"] for N in Ns]
    p90 = [res["B_noisy_krylov"][f"dt=0.5,K=3,N={N},thr={t:g}"]["p90_abs_err"] for N in Ns]
    ax[0].loglog(Ns, med, "-o", ms=4, lw=1.5, color=COL[f"{t:g}"], label=f"cutoff {t:g} (median)")
    ax[0].loglog(Ns, p90, ":", lw=1, color=COL[f"{t:g}"])
ax[0].axhline(CHEM, ls="--", lw=1, color="black"); ax[0].text(1.2e2, 2.1e-3, "chemical accuracy", fontsize=7)
ax[0].set_xlabel("shots per matrix element $N$"); ax[0].set_ylabel(r"$|E-E_{\rm FCI}|$ (Ha)")
ax[0].set_title("Coherent Krylov, $K=3$, $\\Delta t=0.5$ (dotted: 90th pct.)", fontsize=8); ax[0].legend(fontsize=6.5, frameon=False)
for t in thresholds:
    fb = [res["B_noisy_krylov"][f"dt=0.5,K=3,N={N},thr={t:g}"]["frac_below_E0_by_chem"] for N in Ns]
    ax[1].semilogx(Ns, fb, "-o", ms=4, lw=1.5, color=COL[f"{t:g}"], label=f"cutoff {t:g}")
ax[1].set_xlabel("shots per matrix element $N$"); ax[1].set_ylabel("fraction of runs below $E_{\\rm FCI}-1.6$ mHa")
ax[1].set_title("Unphysical (non-variational) outcomes", fontsize=8); ax[1].set_ylim(-0.02, 1.02); ax[1].legend(fontsize=6.5, frameon=False)
fig.tight_layout(); fig.savefig(OUT / "figures" / "krylov-conditioning-h2.png", dpi=200)

fig, ax = plt.subplots(figsize=(6, 3.4))
Ns = [10**3, 10**4, 10**5]
ax.semilogx(Ns, [res["E_spe"][str(n)]["frac_chem_acc"] for n in Ns], "o-", label="statistical PE (matrix pencil)")
ax.semilogx(Ns, [res["E_krylov_same_data"][str(n)]["frac_chem_acc"] for n in Ns], "s--", label="Krylov from the same noisy s(t)")
ax.set_xlabel("shots per (Re, Im) data point"); ax.set_ylabel("fraction of 300 runs within 1.6 mHa")
ax.set_ylim(0, 1.02); ax.legend(fontsize=8)
ax.set_title(r"2-qubit H$_2$ toy, $K=24$ time points, $\Delta t=0.3$", fontsize=9)
fig.tight_layout(); fig.savefig(OUT / "figures" / "spe-vs-krylov-h2.png", dpi=200)
print("wrote figures")
