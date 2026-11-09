"""Deterministic, fully synthetic communication event generator."""
import csv,random
from datetime import datetime,timedelta
from pathlib import Path

def generate(path="demo_events.csv",seed=42,days=45):
    rng=random.Random(seed)
    rows=[]
    start=datetime(2026,8,1,9,0)
    for day in range(days):
        for source,qty,outcome in [
            ("SRC-A12",rng.randint(2,5),"missed"),
            ("SRC-B07",rng.randint(0,2),"answered"),
            ("SRC-C91",rng.randint(0,3),"blocked"),
            ("SRC-D04",rng.randint(0,1),"answered")]:
            for _ in range(qty):
                stamp=(start+timedelta(days=day)).replace(
                    hour=rng.choice([7,8,10,12,14,17,21,22]),minute=rng.randrange(60))
                result=outcome if rng.random()<.77 else rng.choice(["answered","voicemail","missed"])
                rows.append((stamp.isoformat(timespec="minutes"),source,"call",result))
    rows.sort()
    path=Path(path)
    with path.open("w",newline="",encoding="utf-8") as stream:
        writer=csv.writer(stream)
        writer.writerow(["timestamp","source_id","channel","outcome"])
        writer.writerows(rows)
    return path

if __name__=="__main__":
    print(generate())
