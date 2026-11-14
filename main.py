# btc-cent-forecast-01: forecast BTC's price 240 minutes after each checkpoint.
#
# Model: damped two-scale mean reversion on log returns.
#   guess = last_close * exp(clamp(-0.30 * r240 - 0.20 * r1440, -0.02, +0.02))
# where r240 / r1440 are the log returns over the last 4 h / 24 h up to the
# checkpoint. In the practice window, 4-hour moves revert a fraction of the
# previous 4-hour and 24-hour moves (walk-forward correlation of the forward
# 240-minute return with past returns is about -0.31 at 240 min and -0.57 at
# 24 h). The coefficients are shrunk well below the pooled-OLS fit so the
# forecast stays close to persistence when the signal is weak, and there is
# no drift term: the practice window trends down, but a fixed drift would be
# a bet that the final's regime trends the same way, which nothing supports.
# The +-2% cap on the adjustment never binds on the practice data; it is a
# guardrail so an extreme move in the final's unseen regime cannot push the
# guess far from the checkpoint close.
#
# Deterministic, standard library only, no network, no wall clock, no
# randomness. Reads $MAKEFUN_INPUT_DIR (default /input), writes one
# <id>.out per <id>.in to $MAKEFUN_OUTPUT_DIR (default /output), exactly the
# shape the rules require: {"forecasts": [{"case": "<id>", "price": <n>}]},
# price on the grid's 5 decimals and inside (0, 10_000_000).

import json
import math
import os
from os import path

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

MIN_PRICE = 0.00001
MAX_PRICE = 9_999_999.99999

# Mean-reversion strength on the 4-hour and 24-hour log returns.
A_240 = 0.30
B_1440 = 0.20
# Hard cap on the total log adjustment (guardrail, never binds in practice).
ADJ_CAP = 0.02


def _log_return(prices, last, window):
    """log(prices[last] / prices[last - window]), or 0 if unavailable."""
    idx = last - window
    if idx < 0:
        return 0.0
    prev = prices[idx]
    if prev <= 0.0:
        return 0.0
    return math.log(prices[last] / prev)


def forecast(prices):
    """One price guess from a list of 1-minute closes, last at the checkpoint."""
    if not prices:
        raise ValueError("market has no prices")
    last = len(prices) - 1
    close = prices[last]
    if not isinstance(close, (int, float)) or not math.isfinite(close) or close <= 0:
        raise ValueError("last price is not a positive finite number")
    r240 = _log_return(prices, last, 240)
    r1440 = _log_return(prices, last, 1440)
    adj = -A_240 * r240 - B_1440 * r1440
    adj = max(-ADJ_CAP, min(ADJ_CAP, adj))
    guess = close * math.exp(adj)
    return round(min(MAX_PRICE, max(MIN_PRICE, guess)) * 1e5) / 1e5


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    inputs = sorted(f for f in os.listdir(INPUT_DIR) if f.endswith(".in"))
    for name in inputs:
        case_id = name[: -len(".in")]
        with open(path.join(INPUT_DIR, name), "r", encoding="utf-8") as fh:
            case = json.load(fh)
        markets = case.get("markets")
        if not isinstance(markets, list) or len(markets) != 1:
            raise ValueError("%s does not hold exactly one market" % name)
        price = forecast(markets[0]["prices"])
        out = {"forecasts": [{"case": case_id, "price": price}]}
        with open(path.join(OUTPUT_DIR, case_id + ".out"), "w", encoding="utf-8") as fh:
            fh.write(json.dumps(out) + "\n")


if __name__ == "__main__":
    main()
