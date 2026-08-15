"""Unit tests for position management plan (Tickets 2–3)."""

from __future__ import annotations

import pytest

from backend.positions.plan import compute_plan


def test_day0_init_no_current_price() -> None:
    result = compute_plan(
        shares=300,
        entry_price=50.0,
        final_stop=49.0,
        entry_date="2026-08-10",
        as_of_date="2026-08-10",
    )
    assert result.day_index == 0
    assert result.phase == "day0_init"
    assert result.stop_mode == "three_tier"
    assert len(result.stop_book) == 3
    assert result.net_shares == 300
    assert result.unrealized_r is None
    assert result.actions == []


def test_day0_at_2r_shave() -> None:
    result = compute_plan(
        shares=300,
        entry_price=50.0,
        final_stop=49.0,
        entry_date="2026-08-10",
        as_of_date="2026-08-10",
        current_price=52.0,  # +2R
    )
    assert result.phase == "day0_2"
    assert any(a.code == "SHAVE_2R" for a in result.actions)
    assert result.net_shares == 200  # sold 100 = 300 // 3
    assert result.stop_mode == "three_tier"
    assert sum(level.shares for level in result.stop_book) == 200


def test_day3_consolidate_be() -> None:
    result = compute_plan(
        shares=300,
        entry_price=50.0,
        final_stop=49.0,
        entry_date="2026-08-10",
        as_of_date="2026-08-13",  # day_index 3
    )
    assert result.day_index == 3
    assert result.phase == "day3"
    assert any(a.code == "DAY3_CONSOLIDATE_BE" for a in result.actions)
    assert result.stop_mode == "breakeven"
    assert len(result.stop_book) == 1
    assert result.stop_book[0].label == "BE"
    assert result.stop_book[0].price == 50.0


def test_day4_plus_mental_10ma() -> None:
    result = compute_plan(
        shares=300,
        entry_price=50.0,
        final_stop=49.0,
        entry_date="2026-08-10",
        as_of_date="2026-08-14",  # day_index 4
    )
    assert result.day_index == 4
    assert result.phase == "day4_plus"
    assert result.mental_stop == "10-MA"
    assert any(a.code == "POST4_MENTAL_10MA" for a in result.actions)
    assert result.stop_mode == "breakeven"


def test_orl_set_after_close_below() -> None:
    result = compute_plan(
        shares=200,
        entry_price=50.0,
        final_stop=49.0,
        entry_date="2026-08-10",
        as_of_date="2026-08-17",  # day_index >= 4
        close_below_10ma_date="2026-08-14",
        orl=49.5,
    )
    assert any(a.code == "ORL_SET" for a in result.actions)
    assert result.stop_mode == "orl"
    assert result.stop_book[0].label == "ORL"
    assert result.stop_book[0].price == 49.5


def test_as_of_before_entry_raises() -> None:
    with pytest.raises(ValueError):
        compute_plan(
            shares=100,
            entry_price=50.0,
            final_stop=49.0,
            entry_date="2026-08-13",
            as_of_date="2026-08-10",
        )


def test_day0_2r_and_extension_10_catalyst() -> None:
    result = compute_plan(
        shares=300,
        entry_price=50.0,
        final_stop=49.0,
        entry_date="2026-08-10",
        as_of_date="2026-08-10",
        current_price=52.0,  # +2R
        extension_override=10.0,
    )
    assert any(a.code == "SHAVE_2R" for a in result.actions)
    assert any(a.code == "CATALYST_10X_ATR" for a in result.actions)


def test_day5_extension_9_post4_shave() -> None:
    result = compute_plan(
        shares=300,
        entry_price=50.0,
        final_stop=49.0,
        entry_date="2026-08-10",
        as_of_date="2026-08-17",  # day_index 5
        extension_override=9.0,
    )
    assert result.day_index == 5
    assert any(a.code == "POST4_EXTENSION_SHAVE" for a in result.actions)
    assert result.net_shares == 200  # sold 100 = 300 // 3
    assert result.stop_mode == "breakeven"
    assert result.stop_book[0].label == "BE"
    assert result.stop_book[0].shares == 200


def test_day1_stops_33_rescale_alert_and_add() -> None:
    alert_only = compute_plan(
        shares=300,
        entry_price=50.0,
        final_stop=49.0,
        entry_date="2026-08-10",
        as_of_date="2026-08-11",  # day_index 1
        stops_33_hit=True,
    )
    assert any(a.code == "RESCALE_ALERT" for a in alert_only.actions)
    assert not any(a.code == "RESCALE_ADD" for a in alert_only.actions)
    assert alert_only.net_shares == 300

    with_add = compute_plan(
        shares=300,
        entry_price=50.0,
        final_stop=49.0,
        entry_date="2026-08-10",
        as_of_date="2026-08-11",
        stops_33_hit=True,
        rescale_alert_triggered=True,
    )
    assert any(a.code == "RESCALE_ALERT" for a in with_add.actions)
    assert any(a.code == "RESCALE_ADD" for a in with_add.actions)
    assert with_add.net_shares == 450  # 300 + 300 // 2


def test_day10_sideways_consolidation_add() -> None:
    result = compute_plan(
        shares=300,
        entry_price=50.0,
        final_stop=49.0,
        entry_date="2026-08-10",
        as_of_date="2026-08-24",  # day_index 10
        sideways_consolidation=True,
        extension_override=3.0,
    )
    assert result.day_index == 10
    assert any(a.code == "ADD_ON_CONSOLIDATION" for a in result.actions)
    assert result.net_shares == 450  # 300 + 300 // 2
    assert result.stop_mode == "breakeven"


def test_defaults_only_day0_no_new_codes() -> None:
    result = compute_plan(
        shares=300,
        entry_price=50.0,
        final_stop=49.0,
        entry_date="2026-08-10",
        as_of_date="2026-08-10",
    )
    codes = {a.code for a in result.actions}
    assert codes.isdisjoint(
        {
            "CATALYST_10X_ATR",
            "POST4_EXTENSION_SHAVE",
            "RESCALE_ALERT",
            "RESCALE_ADD",
            "ADD_ON_CONSOLIDATION",
        }
    )
    assert result.actions == []
    assert result.net_shares == 300
    assert result.stop_mode == "three_tier"


def test_parabolic_4r_with_shave_already_taken_rebuilds_be() -> None:
    """Rule A must consolidate to singular BE even when SHAVE is skipped."""
    result = compute_plan(
        shares=300,
        entry_price=50.0,
        final_stop=49.0,
        entry_date="2026-08-10",
        as_of_date="2026-08-11",  # day_index 1 < 4
        current_price=54.0,  # +4R
        shave_2r_taken=True,
    )
    assert any(a.code == "PARABOLIC_4R_TO_BE" for a in result.actions)
    assert not any(a.code == "SHAVE_2R" for a in result.actions)
    assert result.net_shares == 300
    assert result.stop_mode == "breakeven"
    assert len(result.stop_book) == 1
    assert result.stop_book[0].label == "BE"
    assert result.stop_book[0].price == 50.0
    assert result.stop_book[0].shares == 300


def test_consolidated_to_be_flag_rebuilds_be_before_day4() -> None:
    """Input consolidated_to_be must yield singular BE without Day-4 path."""
    result = compute_plan(
        shares=300,
        entry_price=50.0,
        final_stop=49.0,
        entry_date="2026-08-10",
        as_of_date="2026-08-11",  # day_index 1
        consolidated_to_be=True,
    )
    assert result.stop_mode == "breakeven"
    assert len(result.stop_book) == 1
    assert result.stop_book[0].label == "BE"
    assert result.stop_book[0].price == 50.0
    assert result.stop_book[0].shares == 300


def test_catalyst_extension_from_ma50_atr_not_override() -> None:
    """Extension resolution must use atr_extension when override is absent."""
    # atr_extension = ((52-50)/50*100)/0.4 = 10.0
    result = compute_plan(
        shares=300,
        entry_price=50.0,
        final_stop=49.0,
        entry_date="2026-08-10",
        as_of_date="2026-08-10",
        current_price=52.0,
        ma50=50.0,
        atr_pct=0.4,
    )
    assert any(a.code == "SHAVE_2R" for a in result.actions)
    assert any(a.code == "CATALYST_10X_ATR" for a in result.actions)


def test_orl_pending_when_orl_missing() -> None:
    result = compute_plan(
        shares=200,
        entry_price=50.0,
        final_stop=49.0,
        entry_date="2026-08-10",
        as_of_date="2026-08-17",
        close_below_10ma_date="2026-08-14",
    )
    codes = {a.code for a in result.actions}
    assert "ORL_PENDING" in codes
    assert "ORL_SET" not in codes
    assert "ORL_RESET_IF_SURVIVES" in codes
    assert result.stop_mode == "breakeven"


def test_day3_skips_size_down_when_shave_already_taken() -> None:
    result = compute_plan(
        shares=300,
        entry_price=50.0,
        final_stop=49.0,
        entry_date="2026-08-10",
        as_of_date="2026-08-13",
        shave_2r_taken=True,
    )
    codes = {a.code for a in result.actions}
    assert "DAY3_SIZE_DOWN" not in codes
    assert "DAY3_CONSOLIDATE_BE" in codes
    assert result.net_shares == 300
    assert result.stop_mode == "breakeven"
