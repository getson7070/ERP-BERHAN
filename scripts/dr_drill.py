import csv
import datetime as dt
from pathlib import Path
import time

start = time.time()
# Simulate a restore drill taking ~1s
time.sleep(1)
end = time.time()
rpo = 900  # placeholder 15-minute RPO
rto = int(end - start)
log_path = Path("logs")
log_path.mkdir(exist_ok=True)
with open(log_path / "restore_drill.log", "a", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["start_iso", "end_iso", "rpo_seconds", "rto_seconds"])
    writer.writerow(
        [
            dt.datetime.utcfromtimestamp(start).isoformat(),
            dt.datetime.utcfromtimestamp(end).isoformat(),
            rpo,
            rto,
        ]
    )
