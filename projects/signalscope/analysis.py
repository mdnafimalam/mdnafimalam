"""Explainable activity-pattern analytics; no personal identifiers are required."""
import csv,io
from datetime import datetime
from math import log1p

HEADERS={"timestamp","source_id","channel","outcome"}
OUTCOMES={"answered","missed","blocked","voicemail","other"}

def parse_events(text):
    reader=csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or not HEADERS.issubset(reader.fieldnames):
        raise ValueError("CSV requires timestamp, source_id, channel, outcome")
    events=[]
    for lineno,row in enumerate(reader,2):
        try:
            stamp=datetime.fromisoformat((row["timestamp"] or "").strip().replace("Z","+00:00"))
            source=(row["source_id"] or "").strip()
            channel=(row["channel"] or "").strip().lower()
            outcome=(row["outcome"] or "").strip().lower()
        except (ValueError,TypeError,AttributeError) as exc:
            raise ValueError(f"Line {lineno}: invalid timestamp or row") from exc
        if not source or not channel or len(source)>100 or outcome not in OUTCOMES:
            raise ValueError(f"Line {lineno}: invalid source, channel, or outcome")
        events.append({"timestamp":stamp,"source_id":source,"channel":channel,"outcome":outcome})
    if not events: raise ValueError("No events found")
    if len({e["timestamp"].tzinfo is None for e in events})>1:
        raise ValueError("Use consistently timezone-aware or naive timestamps")
    return sorted(events,key=lambda x:x["timestamp"])

def daily_counts(events):
    result={}
    for e in events:
        key=e["timestamp"].date().isoformat()
        result[key]=result.get(key,0)+1
    return dict(sorted(result.items()))

def hourly_counts(events):
    result={hour:0 for hour in range(24)}
    for e in events: result[e["timestamp"].hour]+=1
    return result

def overview(events):
    total=len(events)
    if not total: raise ValueError("No events to analyze")
    return {"events":total,"sources":len({e["source_id"] for e in events}),
      "active_days":len({e["timestamp"].date() for e in events}),
      "unanswered_pct":round(100*sum(e["outcome"] in ("missed","blocked","voicemail") for e in events)/total,1)}

def source_summary(events):
    buckets={}
    for e in events: buckets.setdefault(e["source_id"],[]).append(e)
    total=sum(map(len,buckets.values())) or 1
    results=[]
    for source,rows in buckets.items():
        n=len(rows)
        off=sum(e["timestamp"].hour<8 or e["timestamp"].hour>=21 for e in rows)
        blocked=sum(e["outcome"]=="blocked" for e in rows)
        unanswered=sum(e["outcome"] in ("missed","blocked","voicemail") for e in rows)
        score=round(min(100,22*log1p(n)+22*off/n+18*blocked/n+18*unanswered/n+20*n/total),1)
        signals=[]
        if n>=5: signals.append("Repeated activity")
        if off/n>=.35: signals.append("Frequent off-hour contact")
        if blocked>=2: signals.append("Continued blocked contact")
        if unanswered/n>=.75: signals.append("Mostly unanswered")
        results.append({"source_id":source,"events":n,"active_days":len({e["timestamp"].date() for e in rows}),
            "off_hour_pct":round(100*off/n,1),"unanswered_pct":round(100*unanswered/n,1),
            "score":score,"signals":", ".join(signals) if signals else "No notable pattern"})
    return sorted(results,key=lambda r:(-r["score"],-r["events"],r["source_id"]))
