"""Local scorer for the btc-cent-forecast-01 entry (dev tool, not part of the entry).

Runs main.py on the kit's six practice cases, scores each guess against the
actual close 240 minutes after its checkpoint, and checks determinism (two
runs byte-identical) and per-case runtime.

Actuals p00..p04 are exact: each is the next case's checkpoint close.
Actual p05 is NOT in the kit; the official 6-case persistence baseline
(44521.576667 cents) implies p05's persistence error is 31857.33 cents, so
p05's actual is either 73864.455 or 73227.308 -- both are reported as a
sensitivity range, never as a fact.

Usage: python3 score.py [path-to-kit-input-dir]
"""
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_INPUT = sys.argv[1] if len(sys.argv) > 1 else (
    os.path.join(os.path.dirname(HERE), "btc-cent-forecast-01-kit", "input"))

CASES = ["p00", "p01", "p02", "p03", "p04", "p05"]
# Next case's checkpoint close = this case's actual (exact for p00..p04).
NEXT = {"p00": "p01", "p01": "p02", "p02": "p03", "p03": "p04", "p04": "p05"}
P05_CANDIDATES = [73864.455, 73227.308]
BASELINE_6CASE = 44521.576667  # official persistence score, RULES.txt


def load_case(cid):
    with open(os.path.join(KIT_INPUT, cid + ".in"), encoding="utf-8") as fh:
        return json.load(fh)


def run_main(out_dir):
    env = dict(os.environ)
    env["MAKEFUN_INPUT_DIR"] = KIT_INPUT
    env["MAKEFUN_OUTPUT_DIR"] = out_dir
    t0 = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, os.path.join(HERE, "main.py")],
        env=env, capture_output=True, text=True, timeout=120)
    dt = time.perf_counter() - t0
    if proc.returncode != 0:
        print("main.py FAILED:\n", proc.stdout, proc.stderr)
        sys.exit(1)
    return dt


def read_out(out_dir, cid):
    with open(os.path.join(out_dir, cid + ".out"), encoding="utf-8") as fh:
        raw = fh.read()
    data = json.loads(raw)
    assert set(data) == {"forecasts"}, data
    assert len(data["forecasts"]) == 1, data
    row = data["forecasts"][0]
    assert set(row) == {"case", "price"}, row
    assert row["case"] == cid, row
    price = row["price"]
    assert isinstance(price, (int, float)) and math.isfinite(price)
    assert 0 < price < 10_000_000, price
    return price, raw


def main():
    cases = {cid: load_case(cid) for cid in CASES}
    actual = {}
    for cid in CASES[:5]:
        actual[cid] = cases[NEXT[cid]]["markets"][0]["prices"][-1]
    checkpoint = {cid: cases[cid]["markets"][0]["prices"][-1] for cid in CASES}

    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        run_main(d1)
        dt2 = run_main(d2)
        # determinism: byte-identical outputs across two runs
        deterministic = True
        for cid in CASES:
            with open(os.path.join(d1, cid + ".out"), "rb") as fh:
                h1 = hashlib.sha256(fh.read()).hexdigest()
            with open(os.path.join(d2, cid + ".out"), "rb") as fh:
                h2 = hashlib.sha256(fh.read()).hexdigest()
            if h1 != h2:
                deterministic = False
                print(f"NON-DETERMINISTIC: {cid}")
        guesses = {}
        for cid in CASES:
            guesses[cid], _ = read_out(d1, cid)

    # per-case runtime (one case at a time, as the grader runs it)
    runtimes = {}
    for cid in CASES:
        with tempfile.TemporaryDirectory() as td_in, tempfile.TemporaryDirectory() as td_out:
            import shutil
            shutil.copy(os.path.join(KIT_INPUT, cid + ".in"), os.path.join(td_in, cid + ".in"))
            env = dict(os.environ)
            env["MAKEFUN_INPUT_DIR"] = td_in
            env["MAKEFUN_OUTPUT_DIR"] = td_out
            t0 = time.perf_counter()
            proc = subprocess.run(
                [sys.executable, os.path.join(HERE, "main.py")],
                env=env, capture_output=True, text=True, timeout=30)
            runtimes[cid] = (time.perf_counter() - t0) * 1000
            assert proc.returncode == 0, proc.stderr

    print(f"{'case':>5s} {'checkpoint':>12s} {'guess':>12s} {'actual':>12s} "
          f"{'err_cents':>11s} {'persist_cents':>13s}")
    errs, perrs = [], []
    for cid in CASES[:5]:
        e = abs(guesses[cid] - actual[cid]) * 100
        pe = abs(checkpoint[cid] - actual[cid]) * 100
        errs.append(e)
        perrs.append(pe)
        print(f"{cid:>5s} {checkpoint[cid]:12.5f} {guesses[cid]:12.5f} {actual[cid]:12.5f} "
              f"{e:11.2f} {pe:13.2f}")
    print(f"{'p05':>5s} {checkpoint['p05']:12.5f} {guesses['p05']:12.5f} "
          f"{'???':>12s} {'???':>11s} {abs(checkpoint['p05'] - P05_CANDIDATES[0]) * 100:13.2f} "
          f"(cand. actual {P05_CANDIDATES[0]} / {P05_CANDIDATES[1]})")
    print()
    print(f"exact 5-case mean error:  {statistics.mean(errs):.2f} cents "
          f"(persistence {statistics.mean(perrs):.2f})")
    for a in P05_CANDIDATES:
        e5 = abs(guesses["p05"] - a) * 100
        print(f"6-case mean if p05 actual = {a}: "
              f"{(sum(errs) + e5) / 6:.2f} cents "
              f"(persistence baseline official: {BASELINE_6CASE:.2f})")
    print(f"determinism (two full runs byte-identical): {deterministic}")
    print("per-case runtime ms (incl. interpreter start): "
          + ", ".join(f"{c}={v:.0f}" for c, v in runtimes.items())
          + f" | max {max(runtimes.values()):.0f} ms (cap 8000 ms)")
    print(f"full 6-case run wall time (2nd run): {dt2:.2f} s")


if __name__ == "__main__":
    main()
