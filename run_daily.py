"""
Run once per day (via GitHub Actions cron) to append a fresh snapshot to
data/history.csv. The commit + push happens in the workflow file, not here.
"""

import csv
import os

from fetchers import fetch_all

HISTORY_PATH = os.path.join(os.path.dirname(__file__), "data", "history.csv")

FIELDS = [
    "date",
    "breadth_pct_above_200dma", "breadth_tickers_counted",
    "put_volume_proxy", "expirations_used",
    "fear_greed_score", "fear_greed_rating",
    "tech_basket_avg_forward_pe", "tech_basket_forward_eps_sum", "tech_basket_size",
]


def main():
    snapshot = fetch_all()
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    file_exists = os.path.isfile(HISTORY_PATH)
    with open(HISTORY_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerow(snapshot)
    print("Snapshot written:", snapshot)


if __name__ == "__main__":
    main()
