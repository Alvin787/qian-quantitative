"""Unit tests for position sizing and stop book."""

from __future__ import annotations

import math

import pytest

from backend.positions.sizing import compute_size
from backend.positions.stops import split_tranches


def test_split_tranches_1000() -> None:
    assert split_tranches(1000) == (333, 333, 334)


def test_fixed_pct_known_fixture() -> None:
    result = compute_size(
        equity=100_000,
        entry_price=50,
        final_stop=49,
        method="fixed_pct",
        risk_pct=0.5,
    )
    assert result.risk_dollars == 500
    assert result.shares == 500
    assert len(result.stop_book) == 3
    assert math.isclose(result.stop_book[0].price, 49.67, abs_tol=1e-9)
    assert math.isclose(result.stop_book[1].price, 49.34, abs_tol=1e-9)
    assert math.isclose(result.stop_book[2].price, 49.0, abs_tol=1e-9)


def test_kelly_clamps_to_max_risk_pct() -> None:
    # High edge: f* = 0.6 - 0.4/2 = 0.4 → 40% which clamps to max_risk_pct=1.0
    result = compute_size(
        equity=100_000,
        entry_price=50,
        final_stop=49,
        method="kelly",
        max_risk_pct=1.0,
        win_rate=0.6,
        avg_win_r=2.0,
        avg_loss_r=1.0,
    )
    assert result.kelly_f_star is not None
    assert result.kelly_f_star > 0.01
    assert result.risk_pct == 1.0
    assert result.shares == 1000


def test_kelly_non_positive_raises() -> None:
    with pytest.raises(ValueError, match="Kelly fraction is non-positive"):
        compute_size(
            equity=100_000,
            entry_price=50,
            final_stop=49,
            method="kelly",
            win_rate=0.3,
            avg_win_r=1.0,
            avg_loss_r=1.0,
        )


def test_shares_less_than_one_raises() -> None:
    with pytest.raises(ValueError, match="Computed shares < 1"):
        compute_size(
            equity=10,
            entry_price=50,
            final_stop=49,
            method="fixed_pct",
            risk_pct=0.5,
        )
