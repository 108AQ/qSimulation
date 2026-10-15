"""QITE on 2-qubit H2 (STO-3G, R=0.735 A, parity mapping + Z2 tapering), vs exact ITE and a
real-time Quantum Krylov (QKSD) baseline. Statevector emulation; S and b are expectation
values that a device would estimate from shots. Writes figures/*.png and results.json.
"""
import json, itertools, numpy as np, scipy.linalg as sla
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent
rng = np.random.default_rng(7)
I2 = np.eye(2); X = np.array([[0,1],[1,0]]); Y = np.array([[0,-1j],[1j,0]]); Z = np.diag([1.,-1.])
P1 = {"I": I2, "X": X, "Y": Y, "Z": Z}
def pauli(s):
    M = np.array([[1.]])
    for c in s: M = np.kron(M, P1[c])
    return M

# H2, R = 0.735 A, STO-3G, electronic part (nuclear repulsion 0.7199689944 Ha not included)
coef = {"II": -1.052373245772859, "IZ": 0.39793742484318045, "ZI": -0.39793742484318045,
        "ZZ": -0.01128010425623538, "XX": 0.18093119978423156}
terms = [(pauli(k), v) for k, v in coef.items() if k != "II"]
H = sum(v * pauli(k) for k, v in coef.items())
w, V = np.linalg.eigh(H); E0 = w[0]; gap = w[1] - w[0]
psi0 = np.zeros(4, complex); psi0[int(np.argmin(np.diag(H).real))] = 1.0   # Hartree-Fock (best basis state)
E = lambda p: float(np.real(p.conj() @ H @ p) / np.real(p.conj() @ p))
print("FCI (electronic)", E0, " HF", E(psi0), " gap", gap)

DT, NSTEP = 0.1, 60
def exact_ite(p, dt, n):
    out = [E(p)]
    U = sla.expm(-dt * H)
    for _ in range(n):
        p = U @ p; p /= np.linalg.norm(p); out.append(E(p))
    return np.array(out)

# full 2-qubit Pauli domain, only strings with odd #Y (A real-coefficient, iA real) -> 6 strings
dom = ["".join(s) for s in itertools.product("IXYZ", repeat=2)]
dom = [s for s in dom if s.count("Y") % 2 == 1]
def qite(p, dt, n, shots=None, reg=1e-6):
    sig = [pauli(s) for s in dom]
    out = [E(p)]; nm = 0
    for _ in range(n):
        for Pm, h in terms:                       # first-order Trotter over Hamiltonian terms
            Ph = sla.expm(-dt * h * Pm) @ p       # exact non-unitary target (emulation only)
            c = np.real(Ph.conj() @ Ph); Ph = Ph / np.sqrt(c)
            d = (Ph - p) / dt
            Sp = [s @ p for s in sig]
            S = np.array([[np.real(a.conj() @ b) for b in Sp] for a in Sp])
            b = np.array([-np.imag(a.conj() @ d) for a in Sp])
            if shots:                              # crude shot-noise model on S, b entries
                S = S + rng.normal(0, 1/np.sqrt(shots), S.shape); S = (S+S.T)/2
                b = b + rng.normal(0, 1/np.sqrt(shots), b.shape)
            a = np.linalg.lstsq(S + reg*np.eye(len(dom)), b, rcond=None)[0]
            A = sum(ai * s for ai, s in zip(a, sig))
            p = sla.expm(-1j * dt * A) @ p; p /= np.linalg.norm(p)
        out.append(E(p))
    return np.array(out)

def qksd(p, dt, K, thr=1e-8):
    """Real-time Krylov: basis e^{-iH k dt}|psi0>, k=0..K-1; generalized eigenproblem."""
    U = sla.expm(-1j * H * dt); vs = [p]
    for _ in range(K - 1): vs.append(U @ vs[-1])
    B = np.array(vs).T
    Hm, Sm = B.conj().T @ H @ B, B.conj().T @ B
    ev, evec = np.linalg.eigh(Sm); keep = ev > thr * ev.max()
    T = evec[:, keep] / np.sqrt(ev[keep])
    return float(np.linalg.eigvalsh(T.conj().T @ Hm @ T)[0])

e_ite = exact_ite(psi0, DT, NSTEP)
e_q = qite(psi0, DT, NSTEP)
NSEED = 20
runs = {N: [qite(psi0, DT, NSTEP, shots=N) for _ in range(NSEED)] for N in (10**3, 10**5)}
e_qn = {N: np.median(r, axis=0) for N, r in runs.items()}                       # median trajectory
tail = {N: float(np.mean([abs(x[-10:].mean() - E0) for x in r])) for N, r in runs.items()}  # plateau error
ks = list(range(1, 5)); e_k = [qksd(psi0, 0.5, k) for k in ks]
tau = DT * np.arange(NSTEP + 1)
res = dict(E_FCI=E0, E_HF=E(psi0), gap=gap, dt=DT, steps=NSTEP, domain=dom,
           qite_final=e_q[-1], ite_final=e_ite[-1], qite_err_final=e_q[-1]-E0,
           qite_shots_plateau_err_mean_over_20_seeds={str(N): v for N, v in tail.items()},
           qksd={int(k): float(e-E0) for k, e in zip(ks, e_k)},
           steps_to_1mHa_qite=int(np.argmax(e_q - E0 < 1.6e-3)),
           steps_to_1mHa_ite=int(np.argmax(e_ite - E0 < 1.6e-3)))
(OUT / "code" / "results.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
ax[0].semilogy(tau, np.maximum(e_ite - E0, 1e-16), "k-", label="exact ITE")
ax[0].semilogy(tau, np.maximum(e_q - E0, 1e-16), "o", ms=3, color="#1f77b4", label="QITE (exact S, b)")
for N, c in zip(e_qn, ("#d62728", "#2ca02c")):
    ax[0].semilogy(tau, np.maximum(np.abs(e_qn[N] - E0), 1e-16), "-", lw=1, color=c, label=f"QITE, {N:.0e} shots/entry (median of 20)")
ax[0].axhline(1.6e-3, ls=":", color="gray"); ax[0].text(4.2, 2.2e-3, "chem. accuracy", color="gray", fontsize=8)
ax[0].set_xlabel(r"imaginary time $\tau$"); ax[0].set_ylabel(r"$E(\tau)-E_{\rm FCI}$ (Ha)"); ax[0].legend(fontsize=7)
ax[1].semilogy(ks, [max(e, 1e-16) for e in np.abs(np.array(e_k) - E0)], "s-", color="#9467bd")
ax[1].set_xlabel("Krylov dimension $K$"); ax[1].set_ylabel(r"$|E-E_{\rm FCI}|$ (Ha)"); ax[1].set_xticks(ks)
ax[1].set_title("Quantum Krylov (real time, $\\Delta t=0.5$)", fontsize=9)
fig.tight_layout(); fig.savefig(OUT / "figures" / "h2_convergence.png", dpi=200)

# schematic of imaginary-time filtering
fig, ax = plt.subplots(figsize=(4.6, 3.0)); En = np.array([0, 1, 2.2]); c = np.array([.5, .6, .62])
for t, ls in zip((0, .5, 1.5, 4), ("-", "--", "-.", ":")):
    w_ = c * np.exp(-t * En); w_ = w_ / np.linalg.norm(w_)
    ax.plot(En, w_**2, "o" + ls, label=rf"$\tau={t}$")
ax.set_xlabel(r"energy $E_n-E_0$"); ax.set_ylabel(r"weight $|c_n(\tau)|^2$"); ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(OUT / "figures" / "filter.png", dpi=200)

# ---- diagnostics added 2026-10-12: where does the plateau come from, and what does the ridge do? ----
extra = {}
# (1) plateau vs step size, with exact S,b; compare to Trotter-only (exact term filters, no QITE fit)
extra["plateau_vs_dt"] = {}
for dt in (0.1, 0.05, 0.025):
    n = int(6 / dt); p = psi0.copy(); Us = [sla.expm(-dt * h * Pm) for Pm, h in terms]
    for _ in range(n):
        for U in Us: p = U @ p; p /= np.linalg.norm(p)
    extra["plateau_vs_dt"][str(dt)] = dict(qite=float(qite(psi0, dt, n)[-1] - E0), trotter_only=float(E(p) - E0))
# (2) shot noise: ridge strength vs error, mean over 20 seeds of the mean error over the last 10 steps
extra["ridge_sweep_mean_err"] = {}
for N in (10**3, 10**5):
    extra["ridge_sweep_mean_err"][str(N)] = {
        str(reg): float(np.mean([abs(qite(psi0, DT, NSTEP, shots=N, reg=reg)[-10:].mean() - E0) for _ in range(20)]))
        for reg in (1e-6, 1e-2, 1e-1)}
res.update(extra); (OUT / "code" / "results.json").write_text(json.dumps(res, indent=1)); print(json.dumps(extra, indent=1))
