# Build report — btc-cent-forecast-01 entry

Built 15 Nov 2026, ~03:10–03:35 WIB, in a fresh session started after the
competition opened. Implemented from the kit's `RULES.txt` /
`competition.yaml` and the practice data only; no earlier make.fun entry was
read. `main.py` was written, run, then revised once (coefficients 0.30/0.15
→ 0.30/0.20 plus the ±2% cap) after a second round of validation.

## What was built

`main.py` — Python 3.13, standard library only (`json`, `math`, `os`), no
network, no wall clock, no randomness. Model: damped two-scale mean
reversion, `guess = last_close * exp(clamp(-0.30*r240 - 0.20*r1440, ±0.02))`,
price rounded to 5 decimals and clamped inside (0, 10,000,000). Reads
`$MAKEFUN_INPUT_DIR` / writes `$MAKEFUN_OUTPUT_DIR` (defaults `/input`,
`/output`), one `<id>.out` per `<id>.in`, exactly the required shape.

`score.py` — local scorer: runs `main.py` on the six practice cases, scores
against known actuals, checks determinism and per-case runtime.

## Validation results

### Walk-forward (the evidence the model choice rests on)

Sub-cases cut inside each practice case's own 72-hour history (checkpoint
every 60 min from t=1440, target t+240, forecast using only data up to t;
44 sub-cases per case, 264 total):

| case | model (cents) | persistence (cents) |
|---|---|---|
| p00 | 34,623.4 | 40,330.2 |
| p01 | 37,004.1 | 42,140.0 |
| p02 | 38,673.1 | 43,945.3 |
| p03 | 46,156.0 | 50,899.8 |
| p04 | 42,501.8 | 47,270.3 |
| p05 | 41,252.0 | 46,114.3 |
| **mean** | **40,035.0** | **45,116.6** |

**11.3% better than persistence, better on all 6 cases.** Block bootstrap
(240-min blocks, 1,000 resamples) of the paired difference for the same
model family: mean −5,037 cents, 95% CI [−7,325, −2,845] — entirely below
zero. Rejected alternatives: rolling per-case OLS (43,999), EMA reversion
(42,613–43,864), symmetric mix with larger 24 h coefficient (worse past
b=0.20), trend-relative / asymmetric variants (worse walk-forward; their
exact-5 gains came from 1–3 checkpoints only).

### Exact practice targets (p00–p04; actual = next case's checkpoint close)

| case | checkpoint | guess | actual | error (cents) | persistence (cents) |
|---|---|---|---|---|---|
| p00 | 74,764.91526 | 74,770.09597 | 74,447.80384 | 32,229.21 | 31,711.14 |
| p01 | 74,447.80384 | 74,497.27551 | 73,680.83594 | 81,643.96 | 76,696.79 |
| p02 | 73,680.83594 | 74,108.23888 | 73,210.50202 | 89,773.69 | 47,033.39 |
| p03 | 73,210.50202 | 73,654.41530 | 73,777.35178 | 12,293.65 | 56,684.98 |
| p04 | 73,777.35178 | 73,837.60669 | 73,545.88170 | 29,172.50 | 23,147.01 |
| **mean (5)** | | | | **49,022.60** | **47,054.66** |

Read honestly: on these five points the model is **worse** than persistence
by 1,968 cents. But a 5-point mean here has a standard error of roughly
12,000 cents (the p02/p03 paired differences, +42,740 and −44,391, nearly
cancel) — the gap is 0.16 standard errors, i.e. noise, and it does not
overturn the 264-sub-case walk-forward evidence. p01/p02 are the two
checkpoints where the price kept falling after a drop, exactly the move a
mean-reversion model misses; p03 is the mirror image where it wins big.

### p05 sensitivity (actual NOT in the kit)

The official 6-case persistence baseline (44,521.576667) implies p05's
persistence error is 31,857.33 cents, so p05's actual is 73,864.455 or
73,227.308. The model's guess is 73,907.42682, giving a 6-case mean of
**41,568.36** cents (first candidate — beats the baseline) or **52,187.48**
(second candidate — does not). Which one is real cannot be known from the
kit; report both, claim neither.

### Dev gate (score.py, run 15 Nov ~03:30 WIB)

- Determinism: two full 6-case runs byte-identical — **pass**.
- Runtime per case (incl. interpreter start): 37–47 ms — **pass** (cap
  8,000 ms). Full 6-case run: 0.05 s.
- Output format: exactly `{"forecasts": [{"case": "<id>", "price": <n>}]}`,
  finite price in (0, 10,000,000), all 6 cases — **pass**.
- `makefun check` was NOT run (it needs a repo + bundle; see below).

## What is NOT done (morning session, with unot)

1. Create a public GitHub repo (after opening — already open) and push
   these files (`main.py`, `README.md`, `LICENSE`, `REPORT.md`, `score.py`).
2. Bundle the transcripts of this build session
   (`node <kit>/cli/makefun.mjs bundle ...`) — this session started after
   the 03:00 WIB opening, so the thinking-in-window gate is satisfied.
3. `makefun check` on the repo + bundle, then `submit` before the
   15:00 WIB deadline — the submit needs unot's MetaMask signature.
4. Nothing here needs a wallet, keypair, or secret; none was touched.

## Honest caveats for the final

- The practice score is no guide to the final (the rules say so, and the
  numbers above show why: 5 points cannot rank a model). The bet is the
  walk-forward mean-reversion effect, measured on one 4-day downtrend
  window (7–11 Nov). If the final's 48-hour regime (15–17 Nov) is a strong
  one-way trend, mean reversion can underperform persistence; the ±2% cap
  bounds how far any single guess can stray from the checkpoint close.
- Prize needs a score strictly below the house baseline **on the final**,
  not on practice. This entry is built to beat it on expectation, not by
  construction.
