import numpy as np
import pandas as pd
import plotly.express as px
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name

from .core import estimate, package_reference, triangle
from .io import ROOT, chart, dump, fetch, report

SOURCE = "https://www.casact.org/sites/default/files/2026-03/ppauto_pos98-07%20%281%29.csv"
INSURERS = [43, 388, 1090, 2003, 4839]


def prepare(refresh=False):
    raw = pd.read_csv(fetch(SOURCE, ROOT / "data/raw/ppauto.csv", refresh))
    if raw.duplicated(["GRCODE", "AccidentYear", "DevelopmentLag"]).any():
        raise ValueError("Duplicate source triangle cells")
    out = ROOT / "data/processed"
    out.mkdir(parents=True, exist_ok=True)
    selected = raw[raw.GRCODE.isin(INSURERS)].copy()
    selected.to_csv(out / "selected_insurers.csv", index=False)
    dump(
        ROOT / "data/provenance.json",
        dict(
            source=SOURCE,
            webpage="https://www.casact.org/publications-research/research/research-resources/loss-reserving-data-pulled-naic-schedule-p",
            acknowledgement="Accessed from CAS, compiled for the CAS by S&P Global Market Intelligence",
            line="US private passenger auto liability/medical; net of reinsurance",
            units="Schedule P monetary units as published (thousands of USD)",
            insurer_codes=INSURERS,
            scope="fixed illustrative insurer panel; not market-representative; accident years 1998–2007; development through lag 10",
        ),
    )
    return selected


def workbook(paid, estimate_frame, ldf):
    with xlsxwriter.Workbook(ROOT / "reports/reserve_review.xlsx") as book:
        head = book.add_format({"bold": True, "bg_color": "#17324d", "font_color": "white"})
        money = book.add_format({"num_format": "#,##0.00"})
        tri = book.add_worksheet("Paid")
        tri.write_row(0, 0, ["Accident year"] + list(paid.columns), head)
        for i, (year, row) in enumerate(paid.iterrows(), 1):
            tri.write(i, 0, int(year))
            for j, val in enumerate(row, 1):
                if pd.notna(val):
                    tri.write_number(i, j, float(val), money)
        factors = book.add_worksheet("Factors")
        factors.write_row(
            0, 0, ["Lag", "Sum current eligible", "Sum next eligible", "Selected factor", "CDF"], head
        )
        cdf = np.r_[np.cumprod(ldf[::-1])[::-1], 1]
        for lag in range(1, 10):
            eligible = [
                i + 2
                for i, (_, row) in enumerate(paid.iterrows())
                if pd.notna(row[lag]) and pd.notna(row[lag + 1])
            ]
            a, b = xl_col_to_name(lag), xl_col_to_name(lag + 1)
            current = sum(float(paid.iloc[r - 2][lag]) for r in eligible)
            nxt = sum(float(paid.iloc[r - 2][lag + 1]) for r in eligible)
            factors.write(lag, 0, lag)
            factors.write_formula(lag, 1, "=" + "+".join(f"Paid!{a}{r}" for r in eligible), money, current)
            factors.write_formula(lag, 2, "=" + "+".join(f"Paid!{b}{r}" for r in eligible), money, nxt)
            factors.write_formula(lag, 3, f"=C{lag + 1}/B{lag + 1}", None, ldf[lag - 1])
            factors.write_formula(lag, 4, f"=PRODUCT(D{lag + 1}:D10)", None, cdf[lag - 1])
        factors.write_row(10, 0, [10, 0, 0, 1, 1])
        results = book.add_worksheet("Reserves")
        results.write_row(
            0,
            0,
            [
                "Year",
                "Latest lag",
                "Latest paid",
                "CDF",
                "CL ultimate",
                "CL reserve",
                "Premium",
                "Assumed ELR",
                "BF reserve",
            ],
            head,
        )
        for i, row in enumerate(estimate_frame.itertuples(), 1):
            n = i + 1
            results.write_row(i, 0, [row.accident_year, row.latest_lag, row.latest_paid])
            results.write_formula(i, 3, f"=INDEX(Factors!E2:E11,B{n})", None, row.cdf)
            results.write_formula(i, 4, f"=C{n}*D{n}", money, row.cl_ultimate)
            results.write_formula(i, 5, f"=E{n}-C{n}", money, row.cl_reserve)
            results.write_number(i, 6, row.earned_premium, money)
            results.write_number(i, 7, row.assumed_loss_ratio)
            results.write_formula(i, 8, f"=G{n}*H{n}*(1-1/D{n})", money, row.bf_reserve)
        for sheet in [tri, factors, results]:
            sheet.set_column(0, 10, 20)
            sheet.freeze_panes(1, 1)


def run(refresh=False):
    data = prepare(refresh)
    estimates, backtests, summaries, sensitivity, references = [], [], [], [], []
    for code, insurer in data.groupby("GRCODE"):
        outcome = insurer[insurer.DevelopmentLag == 10].set_index("AccidentYear").CumPaidLoss
        for cutoff in [2007, 2008, 2009]:
            paid = triangle(insurer, cutoff)
            premium = (
                insurer[insurer.DevelopmentYear <= cutoff]
                .sort_values("DevelopmentYear")
                .groupby("AccidentYear")
                .EarnedPremNet.last()
            )
            e, ldf = estimate(paid, premium)
            e["insurer"] = int(code)
            e["cutoff"] = cutoff
            e["observed_lag10"] = e.accident_year.map(outcome)
            e["actual_future_to_lag10"] = e.observed_lag10 - e.latest_paid
            estimates.append(e)
            for method in ["cl", "bf"]:
                for row in e.itertuples():
                    backtests.append(
                        dict(
                            insurer=int(code),
                            cutoff=cutoff,
                            accident_year=row.accident_year,
                            method=method,
                            predicted_future=getattr(row, f"{method}_reserve"),
                            actual_future=row.actual_future_to_lag10,
                            error=getattr(row, f"{method}_reserve") - row.actual_future_to_lag10,
                        )
                    )
            ref = package_reference(insurer, cutoff)
            diff = float(e.cl_reserve.sum() - ref["package_cl_reserve"])
            if not np.isfinite(diff) or abs(diff) > max(0.01, abs(ref["package_cl_reserve"]) * 1e-7):
                raise ValueError(f"Independent package mismatch: {diff}")
            references.append(
                dict(
                    insurer=int(code),
                    cutoff=cutoff,
                    own_cl_reserve=float(e.cl_reserve.sum()),
                    difference=diff,
                    **ref,
                )
            )
            summaries.append(
                dict(
                    insurer=int(code),
                    name=insurer.GRNAME.iloc[0],
                    cutoff=cutoff,
                    cl_reserve=float(e.cl_reserve.sum()),
                    bf_reserve=float(e.bf_reserve.sum()),
                    actual_future_to_lag10=float(e.actual_future_to_lag10.sum()),
                    mack_standard_error=ref["mack_standard_error"],
                )
            )
            if cutoff == 2007:
                for elr in [0.6, 0.7, 0.8]:
                    for tail in [1.0, 1.02, 1.05]:
                        s, _ = estimate(paid, premium, elr, tail=tail)
                        sensitivity.append(
                            dict(
                                insurer=int(code),
                                assumed_elr=elr,
                                tail_factor=tail,
                                cl_reserve=float(s.cl_reserve.sum()),
                                bf_reserve=float(s.bf_reserve.sum()),
                            )
                        )
                if code == 43:
                    workbook(paid, e, ldf)
    estimates = pd.concat(estimates)
    backtests = pd.DataFrame(backtests)
    summaries = pd.DataFrame(summaries)
    sensitivity = pd.DataFrame(sensitivity)
    pd.DataFrame(references).to_csv(ROOT / "reports/package_verification.csv", index=False)
    estimates.to_csv(ROOT / "reports/accident_year_estimates.csv", index=False)
    summaries.to_csv(ROOT / "reports/valuation_summary.csv", index=False)
    backtests.to_csv(ROOT / "reports/backtests.csv", index=False)
    sensitivity.to_csv(ROOT / "reports/sensitivity.csv", index=False)
    movement = summaries.sort_values(["insurer", "cutoff"]).copy()
    movement["reserve_change"] = movement.groupby("insurer").cl_reserve.diff()
    movement.to_csv(ROOT / "reports/reserve_movement.csv", index=False)
    performance = {
        method: dict(
            cell_mae=float(g.error.abs().mean()), aggregate_bias=float(g.error.sum() / g.actual_future.sum())
        )
        for method, g in backtests.groupby("method")
    }
    metrics = dict(
        insurers=len(summaries.insurer.unique()),
        valuation_dates=[2007, 2008, 2009],
        backtest_cells=len(backtests),
        performance=performance,
        maximum_package_difference=float(max(abs(r["difference"]) for r in references)),
        assumed_bf_loss_ratio=0.7,
        tail="lag-10 terminal assumption for base; 1.02 and 1.05 sensitivity, not observed outcomes",
    )
    chart(
        px.line(
            summaries,
            x="cutoff",
            y="cl_reserve",
            color="name",
            markers=True,
            title="Reserve movement — net paid development",
        ),
        "reserve_movement",
    )
    chart(
        px.scatter(
            summaries,
            x="actual_future_to_lag10",
            y="cl_reserve",
            color="name",
            hover_data=["cutoff"],
            title="Estimated reserves versus subsequently observed payments to lag 10",
        ),
        "backtests",
    )
    report(
        "ReserveWatch",
        f"""# Paid claims development review

US private passenger auto liability/medical data accessed from the CAS website, compiled for the CAS by S&P Global Market Intelligence. Monetary units: thousands of USD as reported in Schedule P. All claims and premiums are net of reinsurance. The panel comprises fixed insurer codes {INSURERS}; it is an illustrative panel, not a market estimate.

The analysis reconstructs paid development triangles for accident years 1998–2007 at valuations 2007, 2008 and 2009. Only cells with development year at or before each cutoff enter development-factor fitting. Later cells are reserved for evaluation. Latest available net earned premiums at the cutoff supply the BF prior exposure base.

Volume-weighted chain ladder is independently reproduced against chainladder-python at all 15 insurer/valuation combinations. Maximum reserve difference: {metrics["maximum_package_difference"]:.9f}. Bornhuetter–Ferguson uses an externally assumed 70% expected loss ratio, not a ratio fitted using later losses. See the editable insurer-43 Excel example for cell-level calculations.

Backtests compare projected payments with subsequently observed development through lag 10. Results: {performance}. Lag 10 is a finite observed horizon and may differ from ultimate loss. The base assumes no development beyond lag 10; tail factors 1.02 and 1.05 are sensitivity assumptions without comparable observed tail outcomes.

Mack standard errors are package-calculated model-dependent reserve uncertainties. They rely on chain-ladder assumptions and do not cover structural changes, tail uncertainty, or all selection risk. Paid recoveries and unusual development must be investigated rather than silently clipped.

Recommendation: review insurer-specific method differences and sensitivity before adopting a central estimate. Compare the BF prior's stabilizing effect for immature accident years with chain ladder's reliance on observed development. A lower historical error does not remove uncertainty about future business.

Reserve movements include normal payment runoff and changing selected factors. reserve_movement.csv reports net movements; a causal attribution to claims inflation or operational changes cannot be established from these triangles alone. This is an analytical review pack, not a statutory submission.
""",
        metrics,
    )
    return metrics
