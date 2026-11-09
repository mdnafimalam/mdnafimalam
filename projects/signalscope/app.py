"""SignalScope — metadata-based, explainable communication activity explorer."""
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from analysis import parse_events,overview,daily_counts,hourly_counts,source_summary
from generate_demo import generate

st.set_page_config(page_title="SignalScope | Pattern Intelligence",page_icon="📡",layout="wide")
st.markdown("""<style>
.stApp{background:#090a0e;color:#f5f3f4}.block-container{padding-top:2rem;max-width:1260px}
[data-testid="stMetric"]{background:#161219;border:1px solid #4e2731;border-radius:13px;padding:16px}
h1,h2,h3{letter-spacing:-.04em}
</style>""",unsafe_allow_html=True)
st.caption("SIGNALSCOPE / PRIVACY-FIRST PATTERN INTELLIGENCE")
st.title("Signals in the noise.")
st.write("Explore repeated-contact behavior using metadata only. Scores are descriptive heuristics, not fraud predictions or legal conclusions.")

with st.sidebar:
    st.header("Data source")
    choice=st.radio("Choose dataset",["Synthetic demo","Upload CSV"])
    upload=st.file_uploader("Upload UTF-8 CSV",type="csv",disabled=choice!="Upload CSV")
    st.caption("Required columns: timestamp, source_id, channel, outcome")
    st.caption("Use pseudonyms. Never upload real names, phone numbers, or message contents.")
if choice=="Upload CSV":
    if upload is None:
        st.info("Choose a CSV or switch to the synthetic demo.")
        st.stop()
    if upload.size>2_000_000:
        st.error("Maximum upload size is 2 MB")
        st.stop()
    try: data=upload.getvalue().decode("utf-8-sig")
    except UnicodeError:
        st.error("Please upload a UTF-8 CSV file.")
        st.stop()
else:
    path=Path(__file__).parent/"demo_events.csv"
    if not path.exists(): generate(path)
    data=path.read_text(encoding="utf-8")
try: events=parse_events(data)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

sources=sorted({e["source_id"] for e in events})
selected=st.multiselect("Explore sources",sources,default=sources)
filtered=[e for e in events if e["source_id"] in selected]
if not filtered:
    st.info("Select at least one source.")
    st.stop()
k=overview(filtered)
for col,label,value in zip(st.columns(4),
    ["Total events","Unique sources","Active days","Unanswered / blocked"],
    [k["events"],k["sources"],k["active_days"],str(k["unanswered_pct"])+"%"]):
    col.metric(label,value)
left,right=st.columns(2)
with left:
    st.subheader("Activity over time")
    values=daily_counts(filtered)
    fig=px.line(x=list(values),y=list(values.values()),markers=True,
                labels={"x":"Date","y":"Events"},template="plotly_dark")
    fig.update_traces(line_color="#c74c5b")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig,use_container_width=True)
with right:
    st.subheader("Hour-of-day distribution")
    values=hourly_counts(filtered)
    fig=px.bar(x=list(values),y=list(values.values()),
               labels={"x":"Hour of day (dataset-local)","y":"Events"},template="plotly_dark")
    fig.update_traces(marker_color="#9e3947")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig,use_container_width=True)

st.subheader("Explainable source ranking")
table=pd.DataFrame(source_summary(filtered))
st.dataframe(table,hide_index=True,use_container_width=True,
    column_config={"score":st.column_config.ProgressColumn(
        "Activity score",min_value=0,max_value=100,format="%.1f")})
st.download_button("Export summary CSV",table.to_csv(index=False),
    "signalscope_summary.csv","text/csv")
with st.expander("Interpretation and scoring"):
    st.write("Score = min(100, 22 × ln(1 + event count) + 22 × off-hours share + 18 × blocked share + 18 × unanswered share + 20 × share of total events). Off-hours are before 08:00 or at/after 21:00. This is not a trained risk model.")
with st.expander("Privacy and data limitations"):
    st.write("Uploads are processed in the app, not intentionally saved to disk, but the hosting provider processes the upload. Use synthetic or pseudonymized data only. Data cannot prove identity, intent, wrongdoing, or consent. Normalize time zones before analysis.")
st.caption("Md Nafim Alam · Python · Streamlit · Plotly · Explainable analytics")
