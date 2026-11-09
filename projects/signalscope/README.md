# SignalScope — Privacy-first Pattern Intelligence

An original portfolio project by **Md Nafim Alam**, exploring unusual or repeated contact activity through **non-identifying metadata**.

## Highlights

- Interactive Streamlit dashboard with a dark black / crimson interface
- Daily patterns and hour-of-day activity visualizations
- Source-level ranking with human-readable explanations
- CSV upload, validation, filters, and summary export
- Deterministic demo generator with fictional source IDs
- 12 unit tests for parser, aggregation, and ranking reliability

### Why this is different
Instead of a standard sales chart, SignalScope focuses on **interpretable event-pattern analytics**: a useful example of data validation, human-centered risk communication, and responsible product design.

## Quick start

```bash
cd projects/signalscope
python -m pip install -r requirements.txt
python generate_demo.py
python -m streamlit run app.py
```

On Windows, substitute `py` for `python` if needed.

Run the tests:

```bash
python -m unittest discover -s . -p 'test_*.py' -v
```

## Sample data format

```csv
timestamp,source_id,channel,outcome
2026-08-01T08:00:00,SRC-A,call,missed
2026-08-01T22:00:00,SRC-A,call,blocked
2026-08-02T11:00:00,SRC-B,call,answered
```

The input requires ISO 8601 timestamps; `source_id` must be pseudonymous, not a phone number or personal identity. Allowed outcomes: `answered`, `missed`, `blocked`, `voicemail`, `other`.

## Architecture

```text
Synthetic CSV or pseudonymized CSV
             |
      CSV parsing/validation (analysis.py)
             |
       KPI / temporal / source aggregations
             |
     Streamlit charts + explanations
             |
          CSV export
```

## Heuristic score

For each source: `min(100, 22×ln(1+n) + 22×off_hours_share + 18×blocked_share + 18×unanswered_share + 20×event_share)`.

An off-hour is before 08:00 or at/after 21:00 in the provided timestamp clock. Scores are **not** the probability of fraud, proof of unwanted contact, or evidence of unlawful behavior. High scores simply highlight activity patterns worth manual examination.

## Limitations and privacy

No message contents are required. Do not submit unredacted personal data or real contact details. Uploaded information is processed in the running app but hosting infrastructure may handle upload bytes. Cross-time-zone data should be normalized before analysis. The app cannot identify people, malicious intent, legal violations, or consent.

## Roadmap

- Weekly baseline comparisons
- Optional privacy-preserving network visualization
- Broader input validation and scenario-based tests
- Public Streamlit deployment with synthetic demo only

**Stack:** Python, Pandas, Plotly, Streamlit, unittest, CSV.
