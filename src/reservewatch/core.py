"""Valuation-safe paid development and Bornhuetter–Ferguson estimates."""

import numpy as np
import pandas as pd


def triangle(records, cutoff):
    observed = records[records.DevelopmentYear <= cutoff]
    if observed.duplicated(["AccidentYear", "DevelopmentLag"]).any():
        raise ValueError("Duplicate triangle cell")
    years = sorted(records.AccidentYear.unique())
    result = observed.pivot(index="AccidentYear", columns="DevelopmentLag", values="CumPaidLoss").reindex(
        index=years, columns=range(1, 11)
    )
    for year in years:
        expected = min(10, max(0, cutoff - year + 1))
        if result.loc[year].notna().sum() != expected:
            raise ValueError("Missing interior triangle cell")
    return result


def factors(paid, recent=None):
    selected = []
    for lag in paid.columns[:-1]:
        pairs = paid[[lag, lag + 1]].dropna()
        if recent:
            pairs = pairs.tail(recent)
        if pairs.empty or (pairs[lag] <= 0).any():
            raise ValueError("Insufficient positive development base")
        selected.append(float(pairs[lag + 1].sum() / pairs[lag].sum()))
    return np.array(selected)


def estimate(paid, premium, expected_loss_ratio=0.7, recent=None, tail=1.0):
    if not 0 < expected_loss_ratio < 3 or tail < 1:
        raise ValueError("Invalid expected loss ratio or tail")
    ldf = factors(paid, recent)
    cdf = np.r_[np.cumprod(ldf[::-1])[::-1], 1.0] * tail
    rows = []
    for year, row in paid.iterrows():
        known = row.dropna()
        if known.empty:
            continue
        age = int(known.index[-1])
        latest = float(known.iloc[-1])
        cl_ultimate = latest * cdf[age - 1]
        prior_ultimate = float(premium.loc[year]) * expected_loss_ratio
        bf_reserve = prior_ultimate * (1 - 1 / cdf[age - 1])
        rows.append(
            dict(
                accident_year=int(year),
                latest_lag=age,
                latest_paid=latest,
                cdf=float(cdf[age - 1]),
                cl_ultimate=cl_ultimate,
                cl_reserve=cl_ultimate - latest,
                bf_ultimate=latest + bf_reserve,
                bf_reserve=bf_reserve,
                earned_premium=float(premium.loc[year]),
                assumed_loss_ratio=expected_loss_ratio,
            )
        )
    return pd.DataFrame(rows), ldf


def package_reference(records, cutoff):
    """Independent chainladder package fit on observations available at valuation."""
    import chainladder as cl

    observed = records[records.DevelopmentYear <= cutoff].copy()
    observed["origin"] = pd.to_datetime(observed.AccidentYear.astype(str))
    observed["valuation"] = pd.to_datetime(observed.DevelopmentYear.astype(str)) + pd.offsets.YearEnd(0)
    tri = cl.Triangle(
        observed, origin="origin", development="valuation", columns="CumPaidLoss", cumulative=True
    )
    # Calendar construction pads later valuations with nonexistent origin years and
    # wholly unobserved development beyond the source's terminal lag. Remove that
    # padding before fitting; otherwise point reserves survive but Mack errors are NaN.
    tri = tri.iloc[:, :, : observed.AccidentYear.nunique(), : int(observed.DevelopmentLag.max())]
    fit = cl.Chainladder().fit(tri)
    mack = cl.MackChainladder().fit(tri)
    stderr = float(np.asarray(mack.total_mack_std_err_).reshape(-1)[0])
    if not np.isfinite(stderr):
        raise ValueError("Mack uncertainty is unavailable for this triangle; investigate development data")
    return dict(
        package_cl_reserve=float(np.nansum(fit.ibnr_.values)),
        mack_standard_error=stderr,
        package="chainladder-python; volume-weighted development; no additional tail",
    )
