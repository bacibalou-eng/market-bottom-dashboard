"""
Run once per day (via GitHub Actions cron) to append a fresh snapshot to
data/history.csv. The commit + push happens in the workflow file, not here.
"""

import csv
import os
import traceback

HISTORY_PATH = os.path.join(os.path.dirname(__file__), "data", "history.csv")
DEBUG_PATH = os.path.join(os.path.dirname(__file__), "data", "debug_error.txt")

FIELDS = [
    "date",
    "breadth_pct_above_200dma", "breadth_tickers_counted",
    "put_volume_proxy", "expirations_used",
    "fear_greed_score", "fear_greed_rating",
    "tech_basket_avg_forward_pe", "tech_basket_forward_eps_sum", "tech_basket_size",
]


def main():
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    try:
        from fetchers import fetch_all
        snapshot = fetch_all()
    except Exception:
        with open(DEBUG_PATH, "w") as f:
            f.write(traceback.format_exc())
        raise

    file_exists = os.path.isfile(HISTORY_PATH)
    with open(HISTORY_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerow(snapshot)
    print("Snapshot written:", snapshot)
    # clear any stale error log from a previous failed run
    if os.path.isfile(DEBUG_PATH):
        os.remove(DEBUG_PATH)


if __name__ == "__main__":
    main()
