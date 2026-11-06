import pandas as pd
import plotly.express as px
import streamlit as st

from .core import estimate, triangle
from .io import ROOT, require, theme


def main():
    theme("ReserveWatch", "Paid claims development, historical valuations, and reserve sensitivity")
    require(ROOT / "reports/metrics.json", "reservewatch run")
    require(ROOT / "data/processed/selected_insurers.csv", "reservewatch run")
    st.caption(
        "US private passenger auto · net of reinsurance · source Schedule P monetary units (USD thousands)"
    )
    data = pd.read_csv(ROOT / "data/processed/selected_insurers.csv")
    names = data.groupby("GRCODE").GRNAME.first().to_dict()
    code = st.sidebar.selectbox("Insurer", list(names), format_func=lambda c: names[c])
    cutoff = st.sidebar.selectbox("Valuation year", [2007, 2008, 2009])
    elr = st.sidebar.slider("Assumed BF expected loss ratio", 0.3, 1.2, 0.7, 0.01)
    tail = st.sidebar.slider("Assumed terminal tail factor", 1.0, 1.1, 1.0, 0.005)
    insurer = data[data.GRCODE == code]
    paid = triangle(insurer, cutoff)
    premium = insurer[insurer.DevelopmentYear <= cutoff].groupby("AccidentYear").EarnedPremNet.last()
    e, ldf = estimate(paid, premium, elr, tail=tail)
    cols = st.columns(3)
    cols[0].metric("Chain-ladder reserve", f"{e.cl_reserve.sum():,.0f}")
    cols[1].metric("BF reserve", f"{e.bf_reserve.sum():,.0f}")
    refs = pd.read_csv(ROOT / "reports/package_verification.csv")
    ref = refs[(refs.insurer == code) & (refs.cutoff == cutoff)].iloc[0]
    cols[2].metric("Mack standard error, base tail", f"{ref.mack_standard_error:,.0f}")
    st.caption(
        "Mack error applies to base chain ladder with no added tail. Lag-10 outcomes are finite development, not guaranteed ultimate losses."
    )
    tabs = st.tabs(["Observed triangle", "Reserves", "Backtests", "Sensitivity"])
    with tabs[0]:
        st.dataframe(paid.style.format("{:,.0f}", na_rep="unobserved"))
        st.dataframe(pd.DataFrame({"lag": range(1, 10), "factor": ldf}), hide_index=True)
    with tabs[1]:
        st.plotly_chart(
            px.bar(e, x="accident_year", y=["cl_reserve", "bf_reserve"], barmode="group"), width="stretch"
        )
        st.dataframe(e, hide_index=True)
    with tabs[2]:
        b = pd.read_csv(ROOT / "reports/backtests.csv")
        st.dataframe(b[(b.insurer == code) & (b.cutoff == cutoff)], hide_index=True)
        st.dataframe(refs, hide_index=True)
    with tabs[3]:
        st.dataframe(pd.read_csv(ROOT / "reports/sensitivity.csv").query("insurer == @code"), hide_index=True)
    st.download_button(
        "Download editable insurer-43 calculation",
        (ROOT / "reports/reserve_review.xlsx").read_bytes(),
        "reserve_review.xlsx",
    )
