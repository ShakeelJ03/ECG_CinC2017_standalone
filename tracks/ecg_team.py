"""
tracks.ecg_team — our team's version of the ECG CinC-2017 track.

It subclasses the supplied `ECGCinC2017Track`, so download/load/hold-out/`write_submission()`
all keep working unchanged, and replaces the three stages we own:

    preprocess()        stage 2  supplied menu + keeps an untouched copy of the raw strip
    extract_features()  stage 3  our own DSP: R-peak detection, rhythm, morphology,
                                 atrial activity, signal quality, wavelet, envelope
    baseline()          stage 5  random forest (supplied) or one of our other classifiers

Every choice is a cfg key, so each experiment changes exactly one of them:

    cfg = {
      "preprocess":  "none" | "bandpass" | "wavelet" | "denoise"   (supplied menu)
      "qrs":         "simple" (supplied detector) | "pt" (our Pan–Tompkins with adaptive thresholds)
      "feature_set": "base" or a "+"-joined list, e.g. "base+rr+morph+sqi"
                     groups: base, rr, morph, sqi, wav, env
      "quality_on":  "clean" (quality features see the preprocessed signal, as the supplied code does)
                     | "raw" (quality features see the untouched signal; rhythm still uses the clean one)
      "clf":         "rf" | "et" | "hgb" | "logreg" | "svm"
      "imbalance":   "balanced" | "none" | "smote" | ...   (supplied menu; "balanced"/"none" for all clf)
    }

With the defaults (none / simple / base / clean / rf) the features are identical to the supplied
baseline's, which is what makes every later comparison a controlled one.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, filtfilt, find_peaks, welch, hilbert
from scipy.stats import kurtosis, skew

from ecg_cinc2017 import ECGCinC2017Track, _rpeaks as _rpeaks_simple
from adapter import default_baseline
import biosignals as bio

#: bump when the feature code changes, so cached feature matrices are rebuilt
FEATURE_VERSION = 3

TEAM_CFG_KEYS = frozenset({"qrs", "feature_set", "quality_on", "clf"})


# --------------------------------------------------------------------------- helpers
def _bp(x, fs, lo, hi, order=2):
    nyq = fs / 2
    hi = min(hi, nyq * 0.95)
    b, a = butter(order, [lo / nyq, hi / nyq], "band")
    return filtfilt(b, a, x)


def _band_power(x, fs, band):
    return float(bio.bandpower(x, fs, band))


def _finite(v):
    v = np.asarray(v, dtype=float)
    return np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0)


# --------------------------------------------------------------------------- QRS detection
def rpeaks_pan_tompkins(ecg, fs):
    """Pan & Tompkins (1985), the parts that matter on 30-s handheld strips:

    1. band-pass 5–15 Hz (QRS energy band), 2. five-point derivative, 3. squaring,
    4. 150-ms moving-window integration, 5. **adaptive** signal/noise peak levels
    (SPKI/NPKI) instead of one fixed 30 %-of-max threshold, 6. 200-ms refractory period,
    7. T-wave rejection (a candidate < 360 ms after a beat with less than half its slope),
    8. **search-back** at half threshold when no beat is found for 1.66 × the mean RR.
    Finally each beat is moved to the largest |deflection| of the 5–25 Hz signal within ±80 ms.

    The supplied detector uses one global threshold (30 % of the largest integrated peak), so one
    motion-artifact spike can hide every real beat in the record; that is the failure this fixes.
    """
    x = np.asarray(ecg, float)
    if len(x) < fs * 2 or not np.any(np.isfinite(x)) or np.std(x) == 0:
        return np.array([], dtype=int)
    f = _bp(x, fs, 5, 15, order=2)
    d = np.zeros_like(f)
    d[2:-2] = (-f[:-4] - 2 * f[1:-3] + 2 * f[3:-1] + f[4:]) * (fs / 8.0)
    sq = d ** 2
    w = max(1, int(0.150 * fs))
    integ = np.convolve(sq, np.ones(w) / w, "same")

    cand, _ = find_peaks(integ, distance=int(0.2 * fs))
    if len(cand) == 0:
        return np.array([], dtype=int)
    init = integ[: int(2 * fs)]
    spki = 0.25 * np.max(init) if len(init) else np.max(integ)
    npki = 0.5 * np.mean(init) if len(init) else 0.0
    thr = npki + 0.25 * (spki - npki)

    beats, slopes = [], []
    rr_hist = []
    i = 0
    cand_vals = integ[cand]
    last_beat_idx = -1                      # index into cand of last accepted beat
    while i < len(cand):
        p, v = cand[i], cand_vals[i]
        if v > thr:
            slope = np.max(np.abs(d[max(0, p - w):p + 1])) if p > 0 else 0.0
            if beats and (p - beats[-1]) < 0.36 * fs and slope < 0.5 * slopes[-1]:
                npki = 0.125 * v + 0.875 * npki          # T wave -> treat as noise
            else:
                if beats:
                    rr_hist.append(p - beats[-1])
                beats.append(p); slopes.append(slope); last_beat_idx = i
                spki = 0.125 * v + 0.875 * spki
        else:
            npki = 0.125 * v + 0.875 * npki
        thr = npki + 0.25 * (spki - npki)

        # search-back: long gap since the last beat -> look for the best missed candidate
        if beats and len(rr_hist) >= 2:
            rr_mean = np.mean(rr_hist[-8:])
            nxt = cand[i + 1] if i + 1 < len(cand) else len(integ)
            if nxt - beats[-1] > 1.66 * rr_mean:
                lo = last_beat_idx + 1
                window = [j for j in range(lo, i + 1)
                          if cand[j] - beats[-1] > 0.36 * fs and cand_vals[j] > 0.5 * thr]
                if window:
                    j = max(window, key=lambda k: cand_vals[k])
                    p2 = cand[j]
                    rr_hist.append(p2 - beats[-1])
                    beats.append(p2); slopes.append(slopes[-1]); last_beat_idx = j
                    spki = 0.25 * cand_vals[j] + 0.75 * spki
                    thr = npki + 0.25 * (spki - npki)
                    i = j + 1
                    continue
        i += 1

    if not beats:
        return np.array([], dtype=int)
    # move each beat to the true R location (largest |deflection|) of a wider-band signal
    g = _bp(x, fs, 5, 25, order=2)
    r = int(0.08 * fs)
    out = []
    for p in beats:
        lo, hi = max(0, p - r), min(len(g), p + r + 1)
        out.append(lo + int(np.argmax(np.abs(g[lo:hi]))))
    out = np.unique(out)
    # enforce the refractory period after refinement
    keep = [out[0]]
    for p in out[1:]:
        if p - keep[-1] >= 0.2 * fs:
            keep.append(p)
        elif abs(g[p]) > abs(g[keep[-1]]):
            keep[-1] = p
    return np.asarray(keep, dtype=int)


def _match_fraction(a, b, tol):
    """F1-style agreement between two beat lists (bSQI, Li, Clifford & Mark 2008)."""
    if len(a) == 0 and len(b) == 0:
        return 1.0
    if len(a) == 0 or len(b) == 0:
        return 0.0
    j = np.searchsorted(b, a)
    hit = 0
    for k, p in zip(j, a):
        best = min([abs(p - b[q]) for q in (k - 1, k) if 0 <= q < len(b)], default=tol + 1)
        hit += best <= tol
    return 2.0 * hit / (len(a) + len(b))


# --------------------------------------------------------------------------- RR features
def _sampen(x, m=2, r=0.2):
    """Sample entropy (Richman & Moorman 2000); r is in units of the series."""
    x = np.asarray(x, float)
    n = len(x)
    if n < m + 3:
        return 0.0

    def _count(mm):
        t = np.array([x[i:i + mm] for i in range(n - m)])
        c = 0
        for i in range(len(t) - 1):
            c += np.sum(np.max(np.abs(t[i + 1:] - t[i]), axis=1) <= r)
        return c
    b, a = _count(m), _count(m + 1)
    if a == 0 or b == 0:
        return float(np.log((n - m) * (n - m - 1) / 2.0))        # upper bound when no matches
    return float(-np.log(a / b))


RR_NAMES = ["rr_median", "rr_mad_rel", "rr_range_rel", "rr_min_rel", "rr_max_rel",
            "poincare_sd1", "poincare_sd2", "poincare_ratio",
            "dRR_median_rel", "dRR_frac_gt10", "dRR_frac_gt20",
            "sampen_rr", "cosen", "lorenz_occupied", "lorenz_origin_frac",
            "dRR_autocorr1", "rr_autocorr1", "turning_point_ratio",
            "premature_frac", "hr_min", "hr_max"]


def rr_features(rr):
    """Rhythm features that target AF's 'irregularly irregular' signature and Other's patterns.

    * robust spread (MAD, percentile range) — insensitive to one missed beat, unlike SDNN
    * Poincaré SD1/SD2 (Brennan et al. 2001): AF fills the plot, sinus rhythm is an ellipse
    * successive-difference fractions: share of beats changing by >10 % / >20 %
    * sample entropy and COSEn (Lake & Moorman 2011), built for short AF strips
    * Lorenz-plot occupancy of (ΔRR_i, ΔRR_i+1) (Sarkar, Ritscher & Mehra 2008, 'AF evidence')
    * lag-1 autocorrelation of ΔRR: strongly negative in bigeminy/ectopy (Other), ~0 in AF
    * premature-beat fraction and min/max heart rate for brady/tachycardia (Other)
    """
    rr = np.asarray(rr, float)
    rr = rr[(rr > 0.2) & (rr < 3.0)]
    if len(rr) < 4:
        return np.zeros(len(RR_NAMES))
    med = np.median(rr)
    d = np.diff(rr)
    sd1 = np.std(d) / np.sqrt(2)
    sd2 = np.sqrt(max(2 * np.var(rr) - np.var(d) / 2, 1e-12))
    r = 0.2 * np.std(rr) + 1e-6
    se = _sampen(rr, m=1, r=r)
    cosen = se + np.log(2 * r * 1000) - np.log(np.mean(rr) * 1000)
    # Lorenz plot of successive differences, 40-ms bins
    if len(d) >= 3:
        pts = np.stack([d[:-1], d[1:]], 1)
        cells = np.floor(pts / 0.04).astype(int)
        occupied = len({tuple(c) for c in cells}) / len(cells)
        origin = np.mean(np.all(np.abs(pts) < 0.02, axis=1))
    else:
        occupied, origin = 0.0, 1.0
    ac_d = np.corrcoef(d[:-1], d[1:])[0, 1] if len(d) >= 4 and np.std(d) > 0 else 0.0
    ac_r = np.corrcoef(rr[:-1], rr[1:])[0, 1] if len(rr) >= 4 and np.std(rr) > 0 else 0.0
    if len(rr) >= 3:
        tp = np.sum((rr[1:-1] - rr[:-2]) * (rr[1:-1] - rr[2:]) > 0) / (len(rr) - 2)
    else:
        tp = 0.0
    local = np.array([np.median(rr[max(0, i - 4):i + 5]) for i in range(len(rr))])
    prem = np.mean([(rr[i] < 0.85 * local[i]) and (rr[i + 1] > 1.10 * local[i])
                    for i in range(len(rr) - 1)])
    return _finite([med, np.median(np.abs(rr - med)) / med,
                    (np.percentile(rr, 95) - np.percentile(rr, 5)) / med,
                    rr.min() / med, rr.max() / med,
                    sd1, sd2, sd1 / sd2,
                    np.median(np.abs(d)) / med, np.mean(np.abs(d) > 0.1 * med),
                    np.mean(np.abs(d) > 0.2 * med),
                    se, cosen, occupied, origin, ac_d, ac_r, tp, prem,
                    60.0 / rr.max(), 60.0 / rr.min()])


# --------------------------------------------------------------------------- morphology
MORPH_NAMES = ["polarity", "r_amp", "r_amp_cv", "beat_corr_mean", "beat_corr_p10",
               "qrs_width_ms", "p_amp_rel", "p_corr_mean", "t_amp_rel",
               "atrial_resid_rel", "atrial_4_9hz_frac"]

PRE, POST = 0.30, 0.45                   # beat window around R (s)


def morph_features(ecg, pk, fs):
    """Beat-morphology and atrial-activity features from the median beat template.

    * polarity: about 15 % of CinC-2017 strips are recorded upside-down (Teijeiro et al. 2018),
      so the strip is flipped before any shape is measured
    * beat-to-template correlation: ectopic beats (Other) and noise both lower it
    * QRS width: wide QRS (> 110 ms) is one of the 'Other' criteria in Teijeiro et al.
    * P wave: amplitude in the template and how consistent the P window is beat to beat —
      a missing/inconsistent P wave is the second half of the AF definition
    * QRST cancellation: subtract the scaled template from each beat; what is left between QRS
      complexes is atrial activity, and AF's fibrillatory waves put its power in 4–9 Hz
    """
    x = _bp(np.asarray(ecg, float), fs, 0.5, 40, order=2)
    a, b = int(PRE * fs), int(POST * fs)
    pk = np.asarray([p for p in pk if p - a >= 0 and p + b < len(x)], int)
    if len(pk) < 4:
        return np.zeros(len(MORPH_NAMES))
    pol = 1.0 if np.median(x[pk]) >= 0 else -1.0
    x = x * pol
    beats = np.stack([x[p - a:p + b] for p in pk])
    beats = beats - np.median(beats[:, : int(0.05 * fs)], axis=1, keepdims=True)
    tpl = np.median(beats, axis=0)
    r_idx = a
    r_amp = tpl[r_idx]
    if abs(r_amp) < 1e-9:
        return np.zeros(len(MORPH_NAMES))
    corr = np.array([np.corrcoef(bt, tpl)[0, 1] if np.std(bt) > 0 else 0.0 for bt in beats])
    amps = beats[:, r_idx]
    # QRS width: contiguous region around R where |template| > 20 % of R amplitude
    thr = 0.2 * abs(r_amp)
    lo = r_idx
    while lo > 0 and abs(tpl[lo]) > thr:
        lo -= 1
    hi = r_idx
    while hi < len(tpl) - 1 and abs(tpl[hi]) > thr:
        hi += 1
    # widen by the S wave / Q wave if they follow immediately
    width = (hi - lo) / fs * 1000
    # P wave window 250–80 ms before R
    p0, p1 = r_idx - int(0.25 * fs), r_idx - int(0.08 * fs)
    pw = tpl[p0:p1]
    p_amp = (pw.max() - np.median(pw[:5])) / abs(r_amp)
    pwins = beats[:, p0:p1]
    p_corr = np.mean([np.corrcoef(w, pw)[0, 1] if np.std(w) > 0 and np.std(pw) > 0 else 0.0
                      for w in pwins])
    t_amp = np.max(np.abs(tpl[r_idx + int(0.12 * fs):])) / abs(r_amp)
    # QRST cancellation -> atrial residual
    resid = x.copy()
    for p in pk:
        seg = x[p - a:p + b]
        s = np.dot(seg, tpl) / (np.dot(tpl, tpl) + 1e-12)
        resid[p - a:p + b] = seg - s * tpl
        resid[max(0, p - int(0.05 * fs)):p + int(0.06 * fs)] = 0.0       # blank the QRS itself
    used = resid[pk[0] - a: pk[-1] + b]
    if len(used) > fs * 2:
        f, P = welch(used, fs=fs, nperseg=min(len(used), int(4 * fs)))
        tot = P[(f >= 1) & (f <= 40)].sum() + 1e-12
        af_frac = P[(f >= 4) & (f <= 9)].sum() / tot
    else:
        af_frac = 0.0
    return _finite([pol, abs(r_amp), np.std(amps) / (abs(np.mean(amps)) + 1e-9),
                    np.mean(corr), np.percentile(corr, 10), width, p_amp, p_corr, t_amp,
                    np.std(used) / abs(r_amp), af_frac])


# --------------------------------------------------------------------------- signal quality
SQI_NAMES = ["bsqi", "skew", "baseline_pow_frac", "psqi_5_15_over_5_40", "spec_entropy",
             "flat_frac", "clip_frac", "rms_burst", "hr_implausible"]


def sqi_features(ecg, fs, pk_a, pk_b, rr):
    """Signal-quality indices for the Noisy class (Li, Clifford & Mark 2008; Clifford et al. 2012):
    detector agreement (bSQI), skewness, baseline-wander and QRS-band power fractions, spectral
    entropy, flat-line and clipped fractions, and how bursty the 1-s RMS is (motion artifact)."""
    x = np.asarray(ecg, float)
    tol = int(0.15 * fs)
    bsqi = _match_fraction(np.asarray(pk_a), np.asarray(pk_b), tol)
    f, P = welch(x - np.mean(x), fs=fs, nperseg=min(len(x), int(4 * fs)))
    tot = P[f <= 100].sum() + 1e-12
    base = P[f < 1].sum() / tot
    psqi = P[(f >= 5) & (f <= 15)].sum() / (P[(f >= 5) & (f <= 40)].sum() + 1e-12)
    pn = P[f <= 100] / tot
    sent = -np.sum(pn * np.log(pn + 1e-12)) / np.log(len(pn))
    dx = np.abs(np.diff(x))
    flat = np.mean(dx < 1e-6 * (np.std(x) + 1e-12) + 1e-9)
    mx = np.max(np.abs(x)) + 1e-12
    clip = np.mean(np.abs(x) > 0.98 * mx)
    w = int(fs)
    rms = np.array([np.sqrt(np.mean(x[i:i + w] ** 2)) for i in range(0, len(x) - w + 1, w)])
    burst = np.std(rms) / (np.median(rms) + 1e-12) if len(rms) > 1 else 0.0
    rr = np.asarray(rr, float)
    implaus = np.mean((rr < 0.27) | (rr > 2.0)) if len(rr) else 1.0
    return _finite([bsqi, skew(x), base, psqi, sent, flat, clip, burst, implaus])


# --------------------------------------------------------------------------- wavelet + envelope
WAV_NAMES = [f"wav_E_{n}" for n in ("A6", "D6", "D5", "D4", "D3", "D2", "D1")]


def wavelet_features(ecg, fs):
    """Relative energy per db4 sub-band (6 levels at 300 Hz: D1 75–150 Hz … D6 2.3–4.7 Hz,
    A6 < 2.3 Hz). QRS energy sits in D3–D4, noise in D1–D2, baseline wander in A6."""
    import pywt
    c = pywt.wavedec(np.asarray(ecg, float), "db4", level=6)
    e = np.array([np.sum(ci ** 2) for ci in c])
    return _finite(e / (e.sum() + 1e-12))


ENV_NAMES = ["env_period_peak", "env_period_lag_s", "env_period_2nd_ratio"]


def envelope_features(ecg, fs):
    """Periodicity of the QRS-band Hilbert envelope, measured without any beat detector:
    a regular rhythm gives a tall autocorrelation peak at one RR lag; AF and noise do not."""
    g = _bp(np.asarray(ecg, float), fs, 5, 25, order=2)
    env = np.abs(hilbert(g))
    env = env - env.mean()
    n = len(env)
    if n < 3 * fs or np.std(env) == 0:
        return np.zeros(len(ENV_NAMES))
    nfft = 1 << int(np.ceil(np.log2(2 * n)))
    F = np.fft.rfft(env, nfft)
    ac = np.fft.irfft(F * np.conj(F), nfft)[:n]
    ac = ac / (ac[0] + 1e-12)
    lo, hi = int(0.3 * fs), int(2.0 * fs)
    seg = ac[lo:hi]
    k = int(np.argmax(seg))
    peak, lag = seg[k], (lo + k) / fs
    k2 = lo + k
    second = ac[2 * k2] if 2 * k2 < n else 0.0
    return _finite([peak, lag, second / (peak + 1e-12)])


BASE_NAMES = ["hr", "sdnn_ms", "rmssd_ms", "pnn50", "rr_cv", "rr_irr_frac", "n_beats",
              "qrs_hf_ratio", "powerline_49_51", "std", "kurtosis"]
GROUP_NAMES = {"base": BASE_NAMES, "rr": RR_NAMES, "morph": MORPH_NAMES, "sqi": SQI_NAMES,
               "wav": WAV_NAMES, "env": ENV_NAMES}
QUALITY_BASE = {"qrs_hf_ratio", "powerline_49_51", "std", "kurtosis"}


# --------------------------------------------------------------------------- the track
class ECGTeamTrack(ECGCinC2017Track):
    """The supplied ECG track with our own stages 2, 3 and 5 (see module docstring)."""

    SUPPORTED_CFG_KEYS = ECGCinC2017Track.SUPPORTED_CFG_KEYS | TEAM_CFG_KEYS

    TEAM_DEFAULTS = {"qrs": "simple", "feature_set": "base", "quality_on": "clean", "clf": "rf"}

    def _team(self, cfg):
        cfg = self._cfg(cfg)
        return {k: (cfg.get(k) if cfg.get(k) is not None else v) for k, v in self.TEAM_DEFAULTS.items()}, cfg

    # ---- stage 2 ----
    def preprocess(self, rec, cfg=None):
        """The supplied menu (none/bandpass/wavelet/denoise), plus an untouched copy of the strip
        under epochs['ecg_raw'] so quality features can be computed on the raw signal when
        cfg['quality_on'] == 'raw'."""
        raw = rec.epochs["ecg"]
        out = super().preprocess(rec, cfg)
        return out.replace_epochs({**out.epochs, "ecg_raw": raw})

    # ---- stage 3 ----
    def feature_names(self, cfg=None):
        team, _ = self._team(cfg)
        names = []
        for gname in team["feature_set"].split("+"):
            names += GROUP_NAMES[gname]
        return names

    def extract_features(self, rec, cfg=None):
        team, cfg = self._team(cfg)
        groups = team["feature_set"].split("+")
        bad = [g for g in groups if g not in GROUP_NAMES]
        if bad:
            raise ValueError(f"unknown feature group(s) {bad}; choose from {list(GROUP_NAMES)}")
        fs = rec.fs
        clean = rec.epochs["ecg"][0]
        raw = rec.epochs.get("ecg_raw", rec.epochs["ecg"])[0]
        qsig = raw if team["quality_on"] == "raw" else clean

        pk_simple = _rpeaks_simple(clean, fs)
        pk = rpeaks_pan_tompkins(clean, fs) if team["qrs"] == "pt" else pk_simple
        rr = np.diff(pk) / fs

        feats = []
        for gname in groups:
            if gname == "base":
                feats += self._base(clean, qsig, fs, rr, cfg)
            elif gname == "rr":
                feats += list(rr_features(rr))
            elif gname == "morph":
                feats += list(morph_features(clean, pk, fs))
            elif gname == "sqi":
                pk_other = rpeaks_pan_tompkins(qsig, fs) if team["qrs"] == "simple" else _rpeaks_simple(qsig, fs)
                feats += list(sqi_features(qsig, fs, pk, pk_other, rr))
            elif gname == "wav":
                feats += list(wavelet_features(qsig, fs))
            elif gname == "env":
                feats += list(envelope_features(clean, fs))
        return np.array([_finite(feats)]), np.array([rec.labels[0]]), rec.group

    def _base(self, clean, qsig, fs, rr, cfg):
        """The supplied 11 features, same formulas; the four quality ones read `qsig`."""
        from adapter import spectral_bandpower
        method = str(cfg.get("spectral_method", "welch") or "welch").lower()
        mkw = {"ar_order": int(cfg.get("ar_order", 16)), "bandwidth": float(cfg.get("mt_bandwidth", 4.0))}

        def _p(sig, band):
            if method in ("welch", "default"):
                return bio.bandpower(sig, fs, band)
            return spectral_bandpower(sig, fs, band, method=method, **mkw)
        if len(rr) >= 3:
            hr = 60.0 / np.mean(rr); sdnn = np.std(rr) * 1000
            rmssd = np.sqrt(np.mean(np.diff(rr) ** 2)) * 1000
            pnn50 = np.mean(np.abs(np.diff(rr)) > 0.05) * 100
            cv = np.std(rr) / (np.mean(rr) + 1e-9)
            irr = np.mean((rr < 0.6) | (rr > 1.2))
        else:
            hr = sdnn = rmssd = pnn50 = cv = irr = 0.0
        qrs_bp = _p(qsig, (5, 15))
        hf = _p(qsig, (40, min(fs / 2 - 1, 90)))
        return [hr, sdnn, rmssd, pnn50, cv, irr, float(len(rr)),
                qrs_bp / (hf + 1e-9), _p(qsig, (49, 51)),
                float(np.std(qsig)), float(kurtosis(qsig))]

    # ---- stage 4 ----
    def select_features(self, X, y, cfg=None):
        """The supplied selector menu, except that mutual information gets a fixed random_state:
        the supplied `SelectKBest(mutual_info_classif)` is not seeded, so two identical runs gave
        slightly different scores (found when re-running the dev plan from a clean copy)."""
        cfg = self._cfg(cfg)
        if str(cfg.get("select", "none")).lower() in ("mutual_info", "mi"):
            from functools import partial
            from sklearn.feature_selection import SelectKBest, mutual_info_classif
            k = min(int(cfg.get("select_k", 20)), X.shape[1])
            score = partial(mutual_info_classif, random_state=int(cfg.get("seed", 0)))
            return SelectKBest(score, k=k).fit(X, y)
        return super().select_features(X, y, cfg)

    # ---- stage 5 ----
    def baseline(self, cfg=None):
        """'rf' is the supplied random forest (so the whole imbalance menu works). The others are
        our alternatives, each in a Pipeline with the scaler refit inside every fold."""
        team, cfg = self._team(cfg)
        kind = team["clf"]
        seed = int(cfg.get("seed", 0))
        imb = str(cfg.get("imbalance", "balanced") or "none").lower()
        if kind == "rf":
            return super().baseline(cfg)
        cw = "balanced" if imb in ("balanced", "balanced_subsample") else None
        if imb not in ("balanced", "balanced_subsample", "none", "off"):
            raise ValueError(f"imbalance={imb!r} is only wired for clf='rf'; use 'balanced' or 'none'")
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        if kind == "et":
            from sklearn.ensemble import ExtraTreesClassifier
            m = ExtraTreesClassifier(n_estimators=400, class_weight=cw, random_state=seed, n_jobs=-1)
        elif kind == "hgb":
            from sklearn.ensemble import HistGradientBoostingClassifier
            m = HistGradientBoostingClassifier(learning_rate=0.05, max_iter=300, max_leaf_nodes=15,
                                               l2_regularization=1.0, class_weight=cw,
                                               random_state=seed)
        elif kind == "logreg":
            from sklearn.linear_model import LogisticRegression
            m = LogisticRegression(C=1.0, max_iter=5000, class_weight=cw)
        elif kind == "svm":
            from sklearn.svm import SVC
            m = SVC(C=3.0, gamma="scale", class_weight=cw, random_state=seed)
        else:
            raise ValueError(f"unknown clf {kind!r}")
        return Pipeline([("scale", StandardScaler()), ("clf", m)])
