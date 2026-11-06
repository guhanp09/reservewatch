import numpy as np
import pandas as pd
import pytest

from reservewatch.core import estimate, factors, package_reference, triangle


def test_known_chain_ladder_example_and_bf():
    paid = pd.DataFrame(
        [[100.0, 150.0, 180.0], [200.0, 300.0, np.nan], [400.0, np.nan, np.nan]],
        index=[2000, 2001, 2002],
        columns=[1, 2, 3],
    )
    ldf = factors(paid)
    np.testing.assert_allclose(ldf, [1.5, 1.2])
    e, _ = estimate(paid, pd.Series([300.0, 600.0, 1200.0], index=paid.index))
    np.testing.assert_allclose(e.cl_ultimate, [180, 360, 720])
    assert e.cl_reserve.sum() == pytest.approx(380)
    assert e.iloc[-1].bf_reserve == pytest.approx(1200 * 0.7 * (1 - 1 / 1.8))


def test_future_cells_excluded():
    rows = [
        dict(AccidentYear=y, DevelopmentLag=d, DevelopmentYear=y + d - 1, CumPaidLoss=100 * d)
        for y in range(1998, 2008)
        for d in range(1, 11)
    ]
    data = pd.DataFrame(rows)
    before = triangle(data, 2007)
    data.loc[data.DevelopmentYear > 2007, "CumPaidLoss"] = 999999
    pd.testing.assert_frame_equal(before, triangle(data, 2007))


def test_interior_missing_cell_fails():
    data = pd.DataFrame([dict(AccidentYear=2000, DevelopmentLag=1, DevelopmentYear=2000, CumPaidLoss=1)])
    with pytest.raises(ValueError, match="interior"):
        triangle(data, 2002)


@pytest.mark.parametrize("cutoff", [2007, 2008, 2009])
def test_package_comparison_handles_late_valuation_padding(cutoff):
    rows = [
        dict(
            AccidentYear=year,
            DevelopmentLag=lag,
            DevelopmentYear=year + lag - 1,
            CumPaidLoss=(1000 + 50 * (year - 1998)) * (1 - 0.55**lag) * (1 + 0.015 * np.sin(year + lag)),
        )
        for year in range(1998, 2008)
        for lag in range(1, 11)
    ]
    data = pd.DataFrame(rows)
    ref = package_reference(data, cutoff)
    e, _ = estimate(triangle(data, cutoff), pd.Series(2000.0, index=range(1998, 2008)))
    assert e.cl_reserve.sum() == pytest.approx(ref["package_cl_reserve"])
    assert np.isfinite(ref["mack_standard_error"])
    assert ref["mack_standard_error"] >= 0
