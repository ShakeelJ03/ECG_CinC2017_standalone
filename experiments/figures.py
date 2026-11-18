"""
experiments/figures.py — the figures the report needs, from the cached data and results.

    python experiments/figures.py --data data_cache/ecg_cinc2017 --tag dev431

Writes PNGs to results/<tag>/figures/:
  fig1_rpeaks.png      supplied detector vs our Pan–Tompkins on records where they disagree
  fig2_spectra.png     median power spectrum per class — is there mains hum / wander to filter?
  fig3_poincare.png    Poincaré plots (RR_i vs RR_i+1) for N, A, O and ~ examples
  fig4_iterations.png  macro-F1 ± fold SD for every experiment, coloured by verdict
  fig5_confusion.png   confusion matrices: supplied baseline vs final pipeline
  qrs_agreement.md     both R-peak detectors checked against wfdb's XQRS detector
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
import numpy as np                                    # noqa: E402
from scipy.signal import welch                        # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import ROOT, CLASSES                     # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "tracks"))
from ecg_team import ECGTeamTrack, rpeaks_pan_tompkins   # noqa: E402
from ecg_cinc2017 import _rpeaks                      # noqa: E402

COL = {"N": "#4C72B0", "A": "#DD8452", "O": "#55A868", "~": "#8172B3"}
NAME = {"N": "Normal", "A": "AF", "O": "Other", "~": "Noisy"}


def fig_rpeaks(recs, out):
    picks = []
    for want in ("N", "A", "~"):
        best, gap = None, -1
        for r in recs:
            if r.labels[0] != want:
                continue
            x = r.epochs["ecg"][0]
            a, b = len(_rpeaks(x, r.fs)), len(rpeaks_pan_tompkins(x, r.fs))
            if b - a > gap and len(x) / r.fs >= 20:
                best, gap = r, b - a
        picks.append(best)
    fig, axs = plt.subplots(3, 1, figsize=(11, 7.5))
    for ax, r in zip(axs, picks):
        x = r.epochs["ecg"][0]; fs = r.fs
        t = np.arange(len(x)) / fs
        m = t < 12
        a, b = _rpeaks(x, fs), rpeaks_pan_tompkins(x, fs)
        ax.plot(t[m], x[m], lw=0.6, color="0.3")
        ax.plot(a[a < 12 * fs] / fs, x[a[a < 12 * fs]], "v", ms=8, color="#C44E52",
                label=f"supplied detector ({len(a)} beats in record)")
        ax.plot(b[b < 12 * fs] / fs, x[b[b < 12 * fs]], "o", ms=5, mfc="none", color="#4C72B0",
                label=f"our Pan–Tompkins ({len(b)} beats)")
        ax.set_title(f"{r.group} — {NAME[r.labels[0]]}", loc="left", fontsize=10)
        ax.legend(loc="upper right", fontsize=8, frameon=False)
        ax.set_ylabel("mV")
    axs[-1].set_xlabel("time (s), first 12 s shown")
    fig.tight_layout(); fig.savefig(out, dpi=150); plt.close(fig)


def fig_spectra(recs, out):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for c in CLASSES:
        P = []
        for r in recs:
            if r.labels[0] == c:
                x = r.epochs["ecg"][0]
                f, p = welch(x - x.mean(), fs=r.fs, nperseg=1200)
                P.append(p / p.sum())
        ax.semilogy(f, np.median(P, 0), color=COL[c], label=f"{NAME[c]} (n={len(P)})")
    for f0 in (50, 60):
        ax.axvline(f0, ls=":", color="0.5")
        ax.text(f0 + 0.5, 1e-7, f"{f0} Hz", fontsize=8, color="0.4")
    ax.set_xlim(0, 150); ax.set_xlabel("frequency (Hz)"); ax.set_ylabel("relative power (median)")
    ax.set_title("No mains line at 50/60 Hz; content above ~40 Hz is already gone (device filter)",
                 fontsize=10, loc="left")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout(); fig.savefig(out, dpi=150); plt.close(fig)


def fig_poincare(recs, out):
    fig, axs = plt.subplots(1, 4, figsize=(12, 3.3), sharex=True, sharey=True)
    for ax, c in zip(axs, CLASSES):
        for r in [r for r in recs if r.labels[0] == c][:12]:
            pk = rpeaks_pan_tompkins(r.epochs["ecg"][0], r.fs)
            rr = np.diff(pk) / r.fs
            ax.plot(rr[:-1], rr[1:], ".", ms=3, color=COL[c], alpha=0.6)
        ax.plot([0.2, 2], [0.2, 2], color="0.7", lw=0.8)
        ax.set_title(f"{NAME[c]} (12 records)", fontsize=10)
        ax.set_xlabel("RR$_i$ (s)")
    axs[0].set_ylabel("RR$_{i+1}$ (s)"); axs[0].set_xlim(0.2, 2); axs[0].set_ylim(0.2, 2)
    fig.tight_layout(); fig.savefig(out, dpi=150); plt.close(fig)


def fig_iterations(res, out):
    ids = sorted(res, key=lambda k: (k[1:3], k))
    col = {"real gain": "#55A868", "real loss": "#C44E52", "no detectable difference": "#9E9E9E"}
    fig, ax = plt.subplots(figsize=(11, 4.5))
    for i, k in enumerate(ids):
        r = res[k]
        v = r.get("vs_ref", {}).get("verdict", "baseline")
        ax.errorbar(i, r["mean"]["macro_f1"], yerr=r["sd"]["macro_f1"], fmt="o", capsize=3,
                    color=col.get(v, "#4C72B0"))
    ax.axhline(res["E00"]["mean"]["macro_f1"], ls="--", color="#4C72B0", lw=0.8)
    ax.text(len(ids) - 0.5, res["E00"]["mean"]["macro_f1"] + 0.005, "supplied baseline",
            ha="right", fontsize=8, color="#4C72B0")
    ax.set_xticks(range(len(ids))); ax.set_xticklabels(ids, rotation=45, fontsize=8)
    ax.set_ylabel("macro-F1 (mean ± SD, 25 folds)")
    for v, c in col.items():
        ax.plot([], [], "o", color=c, label=f"vs its reference: {v}")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout(); fig.savefig(out, dpi=150); plt.close(fig)


def fig_confusion(res, out, final_id):
    fig, axs = plt.subplots(1, 2, figsize=(9, 4))
    for ax, k in zip(axs, ("E00", final_id)):
        cm = np.array(res[k]["confusion_rep0"])
        rown = cm / cm.sum(1, keepdims=True)
        ax.imshow(rown, cmap="Blues", vmin=0, vmax=1)
        for i in range(4):
            for j in range(4):
                ax.text(j, i, f"{cm[i, j]}\n{rown[i, j]:.0%}", ha="center", va="center", fontsize=8,
                        color="white" if rown[i, j] > 0.6 else "black")
        ax.set_xticks(range(4)); ax.set_yticks(range(4))
        ax.set_xticklabels([NAME[c] for c in CLASSES]); ax.set_yticklabels([NAME[c] for c in CLASSES])
        ax.set_xlabel("predicted"); ax.set_ylabel("true")
        ax.set_title(f"{k}: macro-F1 {res[k]['mean']['macro_f1']:.3f}", fontsize=10)
    fig.tight_layout(); fig.savefig(out, dpi=150); plt.close(fig)


def qrs_agreement(recs, out):
    """Validate both detectors against an independent one (wfdb's XQRS): beat-matching F1 with a
    150-ms tolerance, per class. CinC-2017 has no beat annotations, so agreement with an
    established detector is the check we can do."""
    import contextlib, io, logging
    import wfdb.processing as wp
    from ecg_team import _match_fraction
    logging.disable(logging.CRITICAL)
    rows = {c: [] for c in CLASSES}
    for r in recs:
        x = r.epochs["ecg"][0]
        with contextlib.redirect_stdout(io.StringIO()):
            ref = wp.xqrs_detect(x, fs=r.fs, verbose=False)
        tol = int(0.15 * r.fs)
        rows[r.labels[0]].append((_match_fraction(_rpeaks(x, r.fs), ref, tol),
                                  _match_fraction(rpeaks_pan_tompkins(x, r.fs), ref, tol)))
    lines = ["| Class | n | supplied detector: mean F1 vs XQRS | records < 0.8 | "
             "our Pan–Tompkins: mean F1 vs XQRS | records < 0.8 |", "|---|---|---|---|---|---|"]
    for c in CLASSES:
        v = np.array(rows[c])
        lines.append(f"| {NAME[c]} | {len(v)} | {v[:, 0].mean():.3f} | {np.mean(v[:, 0] < 0.8):.0%} "
                     f"| {v[:, 1].mean():.3f} | {np.mean(v[:, 1] < 0.8):.0%} |")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--final", default="E03a", help="experiment id of the chosen pipeline")
    a = ap.parse_args()
    out = os.path.join(ROOT, "results", a.tag, "figures")
    os.makedirs(out, exist_ok=True)
    recs = ECGTeamTrack().load_cached(a.data)
    res = {os.path.basename(p)[:-5]: json.load(open(p)) for p in
           glob.glob(os.path.join(ROOT, "results", a.tag, "E*.json"))}
    fig_rpeaks(recs, os.path.join(out, "fig1_rpeaks.png"))
    fig_spectra(recs, os.path.join(out, "fig2_spectra.png"))
    fig_poincare(recs, os.path.join(out, "fig3_poincare.png"))
    qrs_agreement(recs, os.path.join(out, "qrs_agreement.md"))
    if "E00" in res:
        fig_iterations(res, os.path.join(out, "fig4_iterations.png"))
        if a.final in res:
            fig_confusion(res, os.path.join(out, "fig5_confusion.png"), a.final)
    print("figures in", out)
