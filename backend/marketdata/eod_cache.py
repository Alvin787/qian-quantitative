from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pandas as pd

from backend.marketdata.yahoo import yahoo_symbol

_REQUIRED_COLUMNS = ("Open", "High", "Low", "Close", "Volume")


def cache_path(cache_root: Path, as_of_session: str, symbol: str) -> Path:
    session_str = as_of_session.isoformat() if hasattr(as_of_session, "isoformat") else str(as_of_session)
    sym = yahoo_symbol(symbol)
    return Path(cache_root) / session_str / f"{sym}.csv"


def read_eod_cache(cache_root: Path, as_of_session: str, symbol: str) -> pd.DataFrame | None:
    path = cache_path(cache_root, as_of_session, symbol)
    if not path.is_file():
        return None
    try:
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return None
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        if not isinstance(df.index, pd.DatetimeIndex) or df.index.empty:
            return None
        if any(col not in df.columns for col in _REQUIRED_COLUMNS):
            return None
        df = df.loc[:, list(_REQUIRED_COLUMNS)].astype(float)
        if df.isna().all().all() or any(df[col].isna().all() for col in _REQUIRED_COLUMNS):
            return None
        session_str = as_of_session.isoformat() if hasattr(as_of_session, "isoformat") else str(as_of_session)
        last_dt = df.index[-1]
        if hasattr(last_dt, "strftime"):
            last_date_str = last_dt.strftime("%Y-%m-%d")
        elif hasattr(last_dt, "date"):
            last_date_str = last_dt.date().isoformat()
        else:
            last_date_str = str(last_dt)[:10]
        if last_date_str != session_str:
            return None
        return df
    except Exception:
        return None


def write_eod_cache(cache_root: Path, as_of_session: str, symbol: str, df: pd.DataFrame) -> None:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return
    path = cache_path(cache_root, as_of_session, symbol)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_file = tempfile.mkstemp(dir=path.parent, prefix=f"{path.stem}_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="") as f:
            df.to_csv(f, index=True)
        os.replace(tmp_file, path)
    except Exception:
        if os.path.exists(tmp_file):
            try:
                os.remove(tmp_file)
            except OSError:
                pass
        raise
