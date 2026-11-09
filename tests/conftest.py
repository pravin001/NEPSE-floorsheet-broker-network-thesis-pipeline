import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# belt-and-braces: make src/ importable even without the editable install
SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture
def toy_floorsheet() -> pd.DataFrame:
    """Deterministic 3-day, 3-symbol toy floorsheet in CANONICAL schema,
    mimicking the real archive: contract_no strictly increasing per
    (symbol, date) with documentable gaps; ~15% self-loop rows; file order
    deliberately SHUFFLED (real archive rows are not tx-ordered)."""
    rng = np.random.default_rng(7)
    brokers = ["01", "02", "03", "04", "05"]
    dates = ["2024-01-02", "2024-01-03", "2024-01-04"]
    symbols = ["NABIL", "HBL"]
    rows = []
    contract = 20240102000000
    for d_i, date in enumerate(dates):
        for sym in symbols:
            contract += rng.integers(50, 100)  # daily-global gap between (symbol,date) blocks
            for t in range(40):
                isc_loop = rng.random() < 0.15
                buyer = rng.choice(brokers)
                seller = buyer if isc_loop else rng.choice([b for b in brokers if b != buyer])
                vol = int(rng.integers(10, 1000))
                price = float(rng.choice([400.0, 401.0, 402.5]))
                rows.append({
                    "date": date, "contract_no": contract, "symbol": sym,
                    "price": price, "volume": vol, "amount": vol * price,
                    "buyer_broker_id": buyer, "seller_broker_id": seller,
                })
                contract += rng.integers(1, 3)  # occasional +2 gap, strictly increasing
    df = pd.DataFrame(rows)
    return df.sample(frac=1.0, random_state=3).reset_index(drop=True)  # shuffled


@pytest.fixture
def toy_feature_frame() -> pd.DataFrame:
    """96 sessions × 3 symbols of synthetic network features for the
    walk-forward / anomaly pipeline (Labelled [SYNTHETIC] everywhere)."""
    rng = np.random.default_rng(11)
    dates = pd.bdate_range("2024-01-01", periods=96).date.tolist()
    frames = []
    for sym in ["NABIL", "HBL", "EBL"]:
        f = pd.DataFrame({
            "date": dates,
            "buyer_hhi": rng.beta(2, 8, 96),
            "seller_hhi": rng.beta(2, 8, 96),
            "self_loop_ratio": rng.beta(1.2, 20, 96),
            "end_of_day_concentration": rng.beta(5, 20, 96),
            "reciprocity": rng.beta(2, 5, 96),
            "density": rng.beta(3, 20, 96),
            "max_betweenness": rng.beta(2, 6, 96),
            "core_periphery_coeff": rng.beta(2, 3, 96),
        })
        f["symbol"] = sym
        frames.append(f)
    return pd.concat(frames, ignore_index=True)
