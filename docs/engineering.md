# Engineering notes

Triangle construction separates accident year, development lag and valuation year. Cells
later than the valuation cutoff are excluded from fitting; interior missing cells are rejected.
Chain-ladder factors use eligible observed pairs, and the BF prior is an explicit assumption.

An independent chainladder-python calculation verifies each insurer/valuation result. The
adapter removes calendar padding beyond observed origin years and the terminal source lag
before fitting. Nonfinite uncertainty estimates fail explicitly. Regression fixtures cover
both the original and later valuation dates.

Backtest outcomes are subsequently observed payments through development lag ten. Tail
factors are sensitivity assumptions, not observed ultimate outcomes. Excel exhibits expose
the eligible sums, selected factors, cumulative factors and reserve calculations.

Tested dependency versions are recorded in constraints.txt and environment.json. NumPy is
constrained below 2.4 for compatibility with the tested pandas/chainladder combination.
