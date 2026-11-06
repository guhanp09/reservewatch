# Paid claims development review

US private passenger auto liability/medical data accessed from the CAS website, compiled for the CAS by S&P Global Market Intelligence. Monetary units: thousands of USD as reported in Schedule P. All claims and premiums are net of reinsurance. The panel comprises fixed insurer codes [43, 388, 1090, 2003, 4839]; it is an illustrative panel, not a market estimate.

The analysis reconstructs paid development triangles for accident years 1998–2007 at valuations 2007, 2008 and 2009. Only cells with development year at or before each cutoff enter development-factor fitting. Later cells are reserved for evaluation. Latest available net earned premiums at the cutoff supply the BF prior exposure base.

Volume-weighted chain ladder is independently reproduced against chainladder-python at all 15 insurer/valuation combinations. Maximum reserve difference: 0.000000000. Bornhuetter–Ferguson uses an externally assumed 70% expected loss ratio, not a ratio fitted using later losses. See the editable insurer-43 Excel example for cell-level calculations.

Backtests compare projected payments with subsequently observed development through lag 10. Results: {'bf': {'cell_mae': 4379.242694336097, 'aggregate_bias': 0.08912660704353471}, 'cl': {'cell_mae': 5896.132062637238, 'aggregate_bias': 0.1472525130063251}}. Lag 10 is a finite observed horizon and may differ from ultimate loss. The base assumes no development beyond lag 10; tail factors 1.02 and 1.05 are sensitivity assumptions without comparable observed tail outcomes.

Mack standard errors are package-calculated model-dependent reserve uncertainties. They rely on chain-ladder assumptions and do not cover structural changes, tail uncertainty, or all selection risk. Paid recoveries and unusual development must be investigated rather than silently clipped.

Recommendation: review insurer-specific method differences and sensitivity before adopting a central estimate. Compare the BF prior's stabilizing effect for immature accident years with chain ladder's reliance on observed development. A lower historical error does not remove uncertainty about future business.

Reserve movements include normal payment runoff and changing selected factors. reserve_movement.csv reports net movements; a causal attribution to claims inflation or operational changes cannot be established from these triangles alone. This is an analytical review pack, not a statutory submission.
