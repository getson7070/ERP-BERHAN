import csv
import datetime as dt
import time

start = time.time()
# Simulate a restore drill taking ~1s
time.sleep(1)
end = time.time()
rpo = 900  # placeholder 15-minute RPO
rto = int(end - start)
with open("dr-drill.csv", "w", newline="") as fh:
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
