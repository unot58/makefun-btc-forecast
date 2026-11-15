# btc-cent-forecast-01 — Bitcoin 4-hour-ahead price forecast

[![make.fun](https://make.fun/badge/btc-cent-forecast-01.svg)](https://make.fun/bounty/btc-cent-forecast-01)
[![rank](https://make.fun/badge/btc-cent-forecast-01/unot58/makefun-btc-forecast/rank.svg)](https://make.fun/bounty/btc-cent-forecast-01)
[![reward](https://make.fun/badge/btc-cent-forecast-01/unot58/makefun-btc-forecast/reward.svg)](https://make.fun/bounty/btc-cent-forecast-01)

Entry for [make.fun's "Forecast Bitcoin's price 4 hours ahead, 12 times over
48 hours"](https://make.fun/bounty/btc-cent-forecast-01) ($250). One program, `main.py` (Python 3.13, standard library
only), reads each case's 4,320 one-minute BTC closes (72 hours up to the
checkpoint) and writes one guess: the price 240 minutes after the checkpoint.

## How the model works

Damped two-scale mean reversion on log returns:

```
guess = last_close * exp(clamp(-0.30 * r240 - 0.20 * r1440, -0.02, +0.02))
```

where `r240` / `r1440` are the log returns over the last 4 hours / 24 hours
up to the checkpoint. The forecast is the checkpoint close pulled back
toward the recent path: after a rise it guesses a little lower, after a drop
a little higher — never more than 2% away from the checkpoint close (the cap
is a guardrail for unseen regimes; it never binds on the practice data).

Why this shape, and why not persistence:

- In the practice window, the forward 240-minute return is negatively
  correlated with past returns: about **-0.31** with the past 4-hour return
  and **-0.57** with the past 24-hour return. Short-horizon moves partly
  revert over the next 4 hours.
- A pooled OLS fit on walk-forward sub-cases gives coefficients of about
  -0.17 (4 h) and -0.37 (24 h). The shipped coefficients (0.30 / 0.20) are
  deliberately shrunk and re-balanced by grid search on walk-forward
  validation, not fitted in-sample.
- There is **no drift term**: the practice window trends down, but a fixed
  drift would be a bet that the final's unseen 48-hour regime trends the
  same way. Nothing supports that bet.
- A per-case rolling OLS was tried and rejected: it is noisier than the
  fixed-coefficient model (walk-forward 43,999 vs 40,035 cents) and blows up
  on some cases. Fixed coefficients, fitted once from validation, are more
  robust for 12 unseen cases.

## Running it locally

```sh
mkdir -p out
MAKEFUN_INPUT_DIR=<kit>/input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Reads every `*.in` in the input dir (name order) and writes one `<id>.out`
per case: `{"forecasts": [{"case": "<id>", "price": <number>}]}`.

## Local validation (`score.py`)

```sh
python3 score.py [path-to-kit-input-dir]
```

`score.py` runs `main.py` on the six practice cases, scores each guess
against the actual close 240 minutes after its checkpoint, checks that two
full runs are byte-identical, and times one case at a time (as the grader
runs it).

Results (measured 15 Nov 2026, see `REPORT.md` for the full story):

| Check | Result |
|---|---|
| Walk-forward, 264 sub-cases inside the practice histories (model vs persistence) | **40,035.0 vs 45,116.6 cents — 11.3% better**, better on all 6 cases |
| Exact 5 practice targets with known actuals (p00–p04) | 49,022.60 vs persistence 47,054.66 cents — see REPORT.md: a 5-point mean has a ~12,000-cent standard error, so this does not overturn the walk-forward evidence |
| p05 (actual not in the kit; two candidates from the official baseline) | 6-case mean 41,568.36 or 52,187.48 cents vs official baseline 44,521.58 |
| Determinism (two full runs byte-identical) | pass |
| Runtime per case (incl. interpreter start) | 37–47 ms (cap 8,000 ms) |
| Output format | valid on all 6 cases |

## Files

- `main.py` — the entrypoint (the only file the grader runs).
- `score.py` — local scorer / determinism / runtime checks (dev tool).
- `README.md` — this file.
- `LICENSE` — MIT.
- `REPORT.md` — build report: what was built, full validation numbers,
  and what is still left for the morning session (repo + submit + sign).
