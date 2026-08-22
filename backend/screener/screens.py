"""Central Finviz screen catalog.

`strongest_mover_1m` and `strongest_mover_1m_strong_market` differ only in their
performance filter (`ta_perf_4w30o` vs `ta_perf_4w50o`), the latter being the
strong-market variant.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FinvizScreen:
    id: str
    label: str
    url: str
    max_pages: int = 20


SCREENS: dict[str, FinvizScreen] = {
    "reversal_pullback": FinvizScreen(
        id="reversal_pullback",
        label="Mean reversion pullback entry",
        url="https://finviz.com/screener?v=111&f=cap_midover,geo_usa,sh_avgvol_o1000,sh_price_o5,ta_perf_13wup,ta_perf2_26wup,ta_sma20_pb,ta_sma200_sb50,ta_sma50_pa,ta_volatility_mo2&ft=4&o=change&preset=s151691954",
    ),
    "canslim_calibrated": FinvizScreen(
        id="canslim_calibrated",
        label="CANSLIM-inspired calibrated",
        url="https://finviz.com/screener?v=111&f=cap_midover,fa_salesqoq_high,fa_salesyoyttm_high,geo_usa,sh_avgvol_o500,sh_curvol_o2000,sh_insttrans_pos,ta_highlow20d_a5h,ta_highlow50d_a5h,ta_volatility_wo4&ft=4&o=change&preset=s151703676",
    ),
    "high_adr_hottest": FinvizScreen(
        id="high_adr_hottest",
        label="High ADR% hottest stocks",
        url="https://finviz.com/screener?v=131&f=cap_smallover%2Cind_stocksonly%2Csh_avgvol_o1000%2Csh_float_u100%2Csh_short_o30%2Cta_volatility_wo5&ft=4&preset=s151703685",
    ),
    "high_adr_short_squeeze": FinvizScreen(
        id="high_adr_short_squeeze",
        label="High ADR% short squeeze",
        url="https://finviz.com/screener?v=131&f=cap_smallover%2Csh_avgvol_o2000%2Csh_curvol_o1000%2Csh_insttrans_pos%2Csh_short_high%2Cta_perf_13w30o%2Cta_volatility_wo5&ft=4&preset=s151703700",
    ),
    "extended_base_above_sma200": FinvizScreen(
        id="extended_base_above_sma200",
        label="Extended base above SMA200",
        url="https://finviz.com/screener?v=111&f=cap_small%2Csh_avgvol_o1000%2Csh_curvol_o1000%2Csh_insttrans_pos%2Csh_price_o1%2Cta_alltime_b70h%2Cta_highlow50d_a15h%2Cta_highlow52w_b30h%2Cta_perf_ytddown%2Cta_sma200_pa%2Cta_volatility_wo4&ft=4&preset=s151705019",
    ),
    "extended_base_below_sma200": FinvizScreen(
        id="extended_base_below_sma200",
        label="Extended base below SMA200",
        url="https://finviz.com/screener?v=111&f=cap_small,sh_avgvol_o1000,sh_curvol_o1000,sh_insttrans_pos,sh_price_o1,ta_alltime_b70h,ta_highlow50d_a15h,ta_highlow52w_b30h,ta_perf_ytddown,ta_sma200_pb,ta_volatility_wo4&ft=4&preset=s151705020",
    ),
    "strongest_mover_1w": FinvizScreen(
        id="strongest_mover_1w",
        label="Strongest mover, 1 week +20%",
        url="https://finviz.com/screener?v=111&f=cap_smallover%2Cgeo_usa%2Csh_avgvol_o300%2Csh_curvol_o100%2Cta_perf_1w20o%2Cta_volatility_wo4&ft=4&o=-marketcap",
    ),
    "strongest_mover_1w_tight": FinvizScreen(
        id="strongest_mover_1w_tight",
        label="Strongest mover, 1 week +30%",
        url="https://finviz.com/screener?v=111&f=cap_smallover%2Cgeo_usa%2Csh_avgvol_o400%2Csh_curvol_o100%2Cta_perf_1w30o%2Cta_volatility_wo4&ft=4&o=-marketcap&preset=s151705047",
    ),
    "strongest_mover_1m": FinvizScreen(
        id="strongest_mover_1m",
        label="Strongest mover, 1 month",
        url="https://finviz.com/screener?v=111&f=cap_smallover%2Csh_avgvol_o300%2Csh_curvol_o100%2Cta_perf_4w30o%2Cta_volatility_mo5&ft=4&o=-marketcap&preset=s151705048",
    ),
    "strongest_mover_1m_strong_market": FinvizScreen(
        id="strongest_mover_1m_strong_market",
        label="Strongest mover, 1 month +50%",
        url="https://finviz.com/screener?v=111&f=cap_smallover%2Csh_avgvol_o300%2Csh_curvol_o100%2Cta_perf_4w50o%2Cta_volatility_mo5&ft=4&o=-marketcap&preset=s151705049",
    ),
    "strongest_mover_3m": FinvizScreen(
        id="strongest_mover_3m",
        label="Strongest mover, 3 months",
        url="https://finviz.com/screener?v=111&f=cap_smallover%2Csh_avgvol_o1000%2Csh_curvol_o200%2Cta_perf_13w50o%2Cta_volatility_mo5&ft=4&o=-marketcap&preset=s151705051",
    ),
    "strongest_mover_6m": FinvizScreen(
        id="strongest_mover_6m",
        label="Strongest mover, 6 months",
        url="https://finviz.com/screener?v=111&f=cap_smallover%2Csh_avgvol_o1000%2Csh_curvol_o200%2Cta_perf_26w100o%2Cta_volatility_mo5&ft=4&o=-marketcap&preset=s151705055",
    ),
    "ipo_this_year": FinvizScreen(
        id="ipo_this_year",
        label="IPO within the last year",
        url="https://finviz.com/screener?v=111&f=cap_midover,fa_epsyoy1_pos,ipodate_prevyear,sh_avgvol_o1000&ft=4&o=industry&preset=s151705057",
    ),
    "high_short_float": FinvizScreen(
        id="high_short_float",
        label="High short float",
        url="https://finviz.com/screener?v=131&f=cap_smallover%2Cind_stocksonly%2Csh_avgvol_o1000%2Csh_float_u100%2Csh_short_o30&ft=4&preset=s151705067",
    ),
    "liquid_leveraged_etf": FinvizScreen(
        id="liquid_leveraged_etf",
        label="Liquid Leveraged & Inverse ETFs",
        url="",
        max_pages=0,
    ),
}


SCREEN_FAMILY: dict[str, str] = {
    "canslim_calibrated": "quality_growth",
    "high_adr_hottest": "speculative_short_volatility",
    "high_adr_short_squeeze": "speculative_short_volatility",
    "high_short_float": "speculative_short_volatility",
    "extended_base_above_sma200": "base",
    "extended_base_below_sma200": "base",
    "strongest_mover_1w": "momentum",
    "strongest_mover_1w_tight": "momentum",
    "strongest_mover_1m": "momentum",
    "strongest_mover_1m_strong_market": "momentum",
    "strongest_mover_3m": "momentum",
    "strongest_mover_6m": "momentum",
    "ipo_this_year": "ipo",
    "liquid_leveraged_etf": "etf",
}


def screen_family_ids(source_screens: list[str]) -> list[str]:
    """Unique families in first-seen order for ids that exist in SCREEN_FAMILY."""
    families: list[str] = []
    seen: set[str] = set()
    for screen_id in source_screens:
        family = SCREEN_FAMILY.get(screen_id)
        if family is not None and family not in seen:
            seen.add(family)
            families.append(family)
    return families


def screen_family_count(source_screens: list[str]) -> int:
    return len(screen_family_ids(source_screens))


def get_screen(screen_id: str) -> FinvizScreen:
    if screen_id not in SCREENS:
        raise KeyError(screen_id)
    return SCREENS[screen_id]


def list_screens() -> list[FinvizScreen]:
    return list(SCREENS.values())
