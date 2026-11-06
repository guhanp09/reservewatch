# ReserveWatch methodology

Only cells with DevelopmentYear ≤ valuation year enter each fit. AccidentYear, DevelopmentLag and DevelopmentYear are kept distinct. Missing interior cells fail validation. Source earned premium is selected using observations available at the valuation cutoff.

The volume-weighted link ratio at lag j is sum(C[i,j+1])/sum(C[i,j]) over eligible pairs. The cumulative factor is the product of remaining link ratios and any assumed tail. Chain-ladder ultimate equals latest paid × cumulative factor; reserve is ultimate minus latest paid. The BF reserve equals assumed ultimate (net earned premium × assumed ELR) times the undeveloped proportion 1 − 1/CDF. The base ELR is externally assumed 70%, not estimated from later outcomes.

The base assumes no development after lag ten. Backtests compare future payments predicted at each cutoff with subsequently observed payments through lag ten. Those outcomes may still differ from ultimate. Tail factors 1.02/1.05 are sensitivities with no corresponding observed tail validation. Fifteen estimates are independently checked against chainladder-python; NaN mature-cell reserves are excluded from package aggregation, and nonfinite verification differences fail explicitly.

The reference adapter trims calendar-padding origin years and wholly unobserved development beyond lag ten before fitting. This preserves the source horizon and prevents missing uncertainty values at later valuations. Nonfinite Mack outputs fail explicitly.

Mack standard errors come from the independent package under its chain-ladder assumptions, with no added tail. They do not cover all structural, prior, tail or selection uncertainty. Historical valuations overlap. Insurer-level MAE and aggregate bias are descriptive, not independent trials. The workbook exposes eligible sums, factors, CDFs and method formulas for insurer 43. This is a methodological review pack, not a statutory submission.

## Data flow

CAS Schedule P square → insurer panel → valuation cutoff → observed paid triangle → link factors / BF prior → independent package check → later-development comparison → reserve review pack.
