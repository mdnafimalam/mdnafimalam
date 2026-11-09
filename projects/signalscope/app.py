"""SignalScope — privacy-first, explainable communication activity intelligence."""
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analysis import (
    parse_events, filter_events, overview, daily_counts, hourly_counts,
    outcome_counts, channel_counts, weekday_hour_matrix, source_summary,
    quality_summary, WEEKDAYS
)
from generate_demo import generate

st.set_page_config(
    page_title="SignalScope | Pattern Intelligence",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Visual system ----------
st.markdown("""
<style>
:root{
  --bg:#09090b; --panel:#111014; --panel2:#171217; --border:#34252b;
  --text:#f7f4f5; --muted:#aaa0a4; --red:#b53545; --red2:#d85c6a;
}
.stApp{
  background:
    radial-gradient(circle at 88% 4%,rgba(154,36,55,.18),transparent 26%),
    radial-gradient(circle at 8% 30%,rgba(90,20,33,.08),transparent 24%),
    var(--bg);
  color:var(--text);
}
.block-container{max-width:1380px;padding-top:1.6rem;padding-bottom:4rem}
[data-testid="stSidebar"]{background:#0d0c0f;border-right:1px solid #ffffff10}
[data-testid="stSidebar"] .block-container{padding-top:1.3rem}
h1,h2,h3{letter-spacing:-.045em}
h1{font-size:clamp(2.8rem,5vw,5rem)!important;line-height:1!important;margin-bottom:.45rem!important}
p,small{color:var(--muted)}
[data-testid="stMetric"]{
  background:linear-gradient(145deg,#151216,#0f0e11);
  border:1px solid #ffffff14;border-radius:16px;padding:18px 18px 15px;
  box-shadow:0 12px 35px rgba(0,0,0,.16);
}
[data-testid="stMetricLabel"]{color:#bdb2b6}
[data-testid="stMetricValue"]{font-weight:850;letter-spacing:-.04em}
.stTabs [data-baseweb="tab-list"]{gap:8px;border-bottom:1px solid #ffffff12}
.stTabs [data-baseweb="tab"]{
  height:46px;border-radius:10px 10px 0 0;padding:0 16px;color:#a99ca1
}
.stTabs [aria-selected="true"]{background:#231319!important;color:#fff!important}
div[data-testid="stDataFrame"]{border:1px solid #ffffff12;border-radius:14px;overflow:hidden}
div[data-testid="stPlotlyChart"]{border:1px solid #ffffff10;border-radius:16px;padding:8px;background:#0f0e11}
.stButton>button,.stDownloadButton>button{
  border:1px solid #713641!important;border-radius:10px!important;
  background:linear-gradient(135deg,#2b171d,#151014)!important;color:white!important;
  font-weight:750!important
}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:#c34a59!important}
.hero-kicker{font-size:.73rem;letter-spacing:.18em;text-transform:uppercase;font-weight:850;color:#e08a94;margin-bottom:8px}
.hero-sub{font-size:1.05rem;color:#b6aaae;max-width:900px;line-height:1.75;margin-bottom:18px}
.badges{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0 22px}
.badge{padding:6px 10px;border-radius:999px;border:1px solid #61313a;background:#211318;color:#e9b9bf;font-size:.72rem;font-weight:800}
.notice{border:1px solid #5d343c;background:linear-gradient(135deg,#1c1216,#100e11);border-radius:14px;padding:14px 16px;color:#cdbfc3;font-size:.87rem}
.section-card{border:1px solid #ffffff12;background:linear-gradient(145deg,#141115,#0e0d10);border-radius:18px;padding:20px}
.insight-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:10px 0 18px}
.insight{border:1px solid #ffffff10;border-radius:14px;background:#100f11;padding:16px}
.insight b{display:block;color:#fff;margin-bottom:4px}.insight span{font-size:.82rem;color:#a99ea2}
.rule{height:1px;background:#ffffff10;margin:18px 0}
@media(max-width:800px){.insight-grid{grid-template-columns:1fr}}
</style>
""", unsafe_allow_html=True)

PLOT_LAYOUT=dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#bdb3b7"),
    margin=dict(l=10,r=10,t=45,b=10),
    hoverlabel=dict(bgcolor="#171217"),
)

# ---------- Data loading ----------
with st.sidebar:
    st.markdown("### 📡 SignalScope")
    st.caption("Privacy-first pattern intelligence")
    st.markdown("---")
    source_mode=st.radio("Dataset",["Synthetic demo","Upload CSV"],index=0)
    upload=st.file_uploader(
        "Upload UTF-8 CSV",
        type="csv",
        disabled=source_mode!="Upload CSV",
        help="Required: timestamp, source_id, channel, outcome"
    )

if source_mode=="Upload CSV":
    if upload is None:
        st.info("Upload a CSV file or switch to Synthetic demo.")
        st.stop()
    if upload.size>2_000_000:
        st.error("Maximum upload size is 2 MB.")
        st.stop()
    try:
        raw=upload.getvalue().decode("utf-8-sig")
    except UnicodeError:
        st.error("Please upload a UTF-8 CSV file.")
        st.stop()
else:
    demo_path=Path(__file__).parent/"demo_events.csv"
    if not demo_path.exists():
        generate(demo_path)
    raw=demo_path.read_text(encoding="utf-8")

try:
    events=parse_events(raw)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

all_sources=sorted({e["source_id"] for e in events})
all_channels=sorted({e["channel"] for e in events})
all_outcomes=sorted({e["outcome"] for e in events})
min_date=min(e["timestamp"].date() for e in events)
max_date=max(e["timestamp"].date() for e in events)

# ---------- Sidebar controls ----------
with st.sidebar:
    st.markdown("### Filters")
    date_window=st.date_input(
        "Date range",
        value=(min_date,max_date),
        min_value=min_date,max_value=max_date
    )
    selected_sources=st.multiselect("Sources",all_sources,default=all_sources)
    selected_channels=st.multiselect("Channels",all_channels,default=all_channels)
    selected_outcomes=st.multiselect("Outcomes",all_outcomes,default=all_outcomes)

    st.markdown("### Display")
    trend_style=st.selectbox("Trend chart",["Area","Line"],index=0)
    top_n=st.slider("Ranking rows",3,max(3,min(20,len(all_sources))),min(8,max(3,len(all_sources))))
    min_score=st.slider("Minimum activity score",0,100,0,5)
    show_raw=st.toggle("Show raw event table",value=False)
    st.caption("Activity score is a descriptive heuristic, not a fraud or legal-risk prediction.")

if isinstance(date_window,(tuple,list)) and len(date_window)==2:
    start_date,end_date=date_window
else:
    start_date=end_date=date_window

filtered=filter_events(
    events,
    sources=selected_sources,
    outcomes=selected_outcomes,
    channels=selected_channels,
    start_date=start_date,
    end_date=end_date,
)

# ---------- Hero ----------
st.markdown('<div class="hero-kicker">SignalScope / Explainable Pattern Intelligence</div>',unsafe_allow_html=True)
st.title("See patterns. Keep the context.")
st.markdown(
    '<div class="hero-sub">Explore repeated communication activity with pseudonymized metadata, '
    'temporal analysis, explainable scoring, source-level drilldowns, and exportable summaries — '
    'without reading message contents.</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="badges"><span class="badge">Python</span><span class="badge">Streamlit</span>'
    '<span class="badge">Plotly</span><span class="badge">Explainable heuristics</span>'
    '<span class="badge">Privacy-aware design</span></div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="notice">Responsible-use note: SignalScope highlights descriptive activity patterns. '
    'It does not identify people, prove intent, detect fraud, determine consent, or provide legal conclusions.</div>',
    unsafe_allow_html=True
)

if not filtered:
    st.warning("No events match the current filters. Adjust the sidebar selections.")
    st.stop()

df=pd.DataFrame(filtered)
df["timestamp"]=pd.to_datetime(df["timestamp"])
df["date"]=df["timestamp"].dt.date
df["hour"]=df["timestamp"].dt.hour
df["weekday"]=df["timestamp"].dt.day_name().str[:3]

k=overview(filtered)
summary=pd.DataFrame(source_summary(filtered))
summary_view=summary[summary["score"]>=min_score].head(top_n)

m1,m2,m3,m4,m5=st.columns(5)
m1.metric("Events",f'{k["events"]:,}')
m2.metric("Sources",k["sources"])
m3.metric("Active days",k["active_days"])
m4.metric("Unanswered",f'{k["unanswered_pct"]}%')
m5.metric("Peak hour",f'{k["peak_hour"]:02d}:00')

tabs=st.tabs(["Overview","Source Explorer","Temporal Patterns","Data Quality","Methodology"])

# ---------- Overview ----------
with tabs[0]:
    st.markdown("### Executive overview")
    left,right=st.columns([1.55,1])

    with left:
        daily=daily_counts(filtered)
        trend=pd.DataFrame({"date":list(daily.keys()),"events":list(daily.values())})
        if trend_style=="Area":
            fig=px.area(trend,x="date",y="events",markers=True,title="Activity over time")
            fig.update_traces(line_color="#d05664",fillcolor="rgba(176,47,64,.22)")
        else:
            fig=px.line(trend,x="date",y="events",markers=True,title="Activity over time")
            fig.update_traces(line_color="#d05664")
        fig.update_layout(**PLOT_LAYOUT)
        st.plotly_chart(fig,use_container_width=True)

    with right:
        outcomes=outcome_counts(filtered)
        odf=pd.DataFrame({"outcome":list(outcomes.keys()),"events":list(outcomes.values())})
        odf=odf[odf["events"]>0]
        fig=px.pie(
            odf,names="outcome",values="events",hole=.62,title="Outcome mix",
            color_discrete_sequence=["#c94b5a","#8d2c3a","#e17a86","#68434c","#b8a6ab"]
        )
        fig.update_layout(**PLOT_LAYOUT,showlegend=True)
        st.plotly_chart(fig,use_container_width=True)

    top=summary.iloc[0] if not summary.empty else None
    busiest=df.groupby("date").size().sort_values(ascending=False)
    busiest_day=str(busiest.index[0]) if len(busiest) else "—"
    busiest_count=int(busiest.iloc[0]) if len(busiest) else 0

    st.markdown(
        f'''<div class="insight-grid">
        <div class="insight"><b>Highest-ranked source</b><span>{top["source_id"] if top is not None else "—"} · score {top["score"] if top is not None else "—"}</span></div>
        <div class="insight"><b>Busiest day</b><span>{busiest_day} · {busiest_count} events</span></div>
        <div class="insight"><b>Coverage</b><span>{start_date} → {end_date}</span></div>
        </div>''',unsafe_allow_html=True
    )

    st.markdown("### Explainable source ranking")
    st.dataframe(
        summary_view,
        hide_index=True,
        use_container_width=True,
        column_config={
            "score":st.column_config.ProgressColumn("Activity score",min_value=0,max_value=100,format="%.1f"),
            "off_hour_pct":st.column_config.NumberColumn("Off-hours %",format="%.1f%%"),
            "unanswered_pct":st.column_config.NumberColumn("Unanswered %",format="%.1f%%"),
        },
    )
    st.download_button(
        "Download ranking CSV",
        summary.to_csv(index=False),
        "signalscope_source_ranking.csv",
        "text/csv",
        use_container_width=False,
    )

# ---------- Source Explorer ----------
with tabs[1]:
    st.markdown("### Source Explorer")
    st.caption("Drill into one pseudonymous source without changing the global dataset.")
    source_pick=st.selectbox("Choose a source",sorted(df["source_id"].unique()))
    source_events=[e for e in filtered if e["source_id"]==source_pick]
    source_df=pd.DataFrame(source_events)
    source_df["timestamp"]=pd.to_datetime(source_df["timestamp"])
    source_df["hour"]=source_df["timestamp"].dt.hour

    source_stats=source_summary(source_events)[0]
    s1,s2,s3,s4=st.columns(4)
    s1.metric("Events",source_stats["events"])
    s2.metric("Active days",source_stats["active_days"])
    s3.metric("Off-hours",f'{source_stats["off_hour_pct"]}%')
    s4.metric("Activity score",source_stats["score"])

    c1,c2=st.columns([1.4,1])
    with c1:
        by_day=source_df.assign(date=source_df["timestamp"].dt.date).groupby("date").size().reset_index(name="events")
        fig=px.bar(by_day,x="date",y="events",title=f"{source_pick} activity timeline")
        fig.update_traces(marker_color="#a93444")
        fig.update_layout(**PLOT_LAYOUT)
        st.plotly_chart(fig,use_container_width=True)
    with c2:
        mix=source_df.groupby("outcome").size().reset_index(name="events")
        fig=px.pie(mix,names="outcome",values="events",hole=.55,title="Source outcome mix",
                   color_discrete_sequence=["#d25967","#8e2b39","#6c424a","#baa7ac","#e18a93"])
        fig.update_layout(**PLOT_LAYOUT)
        st.plotly_chart(fig,use_container_width=True)

    st.markdown("#### Why this source is highlighted")
    st.markdown(f'<div class="notice">{source_stats["signals"]}</div>',unsafe_allow_html=True)
    st.dataframe(
        source_df[["timestamp","channel","outcome"]].sort_values("timestamp",ascending=False),
        hide_index=True,use_container_width=True
    )

# ---------- Temporal Patterns ----------
with tabs[2]:
    st.markdown("### Temporal patterns")
    heat=weekday_hour_matrix(filtered)
    z=[heat[day] for day in WEEKDAYS]
    heatmap=go.Figure(go.Heatmap(
        z=z,x=list(range(24)),y=WEEKDAYS,
        colorscale=[[0,"#100e11"],[.35,"#4e202a"],[.7,"#9e3141"],[1,"#e06371"]],
        colorbar=dict(title="Events"),
        hovertemplate="%{y} · %{x}:00<br>%{z} events<extra></extra>"
    ))
    heatmap.update_layout(title="Weekday × hour activity heatmap",**PLOT_LAYOUT)
    st.plotly_chart(heatmap,use_container_width=True)

    c1,c2=st.columns(2)
    with c1:
        hours=hourly_counts(filtered)
        hdf=pd.DataFrame({"hour":list(hours.keys()),"events":list(hours.values())})
        fig=px.bar(hdf,x="hour",y="events",title="Hour-of-day distribution")
        fig.update_traces(marker_color="#a93444")
        fig.update_layout(**PLOT_LAYOUT,xaxis=dict(dtick=2))
        st.plotly_chart(fig,use_container_width=True)
    with c2:
        weekday_counts=df.groupby("weekday").size().reindex(WEEKDAYS,fill_value=0).reset_index(name="events")
        fig=px.bar(weekday_counts,x="weekday",y="events",title="Weekday distribution")
        fig.update_traces(marker_color="#71303a")
        fig.update_layout(**PLOT_LAYOUT)
        st.plotly_chart(fig,use_container_width=True)

# ---------- Data Quality ----------
with tabs[3]:
    st.markdown("### Data quality & coverage")
    q=quality_summary(filtered)
    q1,q2,q3,q4=st.columns(4)
    q1.metric("Rows",q["rows"])
    q2.metric("Duplicates",q["duplicate_rows"])
    q3.metric("Unique sources",q["unique_sources"])
    q4.metric("Channels",q["channels"])

    st.markdown(
        f'''<div class="insight-grid">
        <div class="insight"><b>First event</b><span>{q["first_timestamp"]}</span></div>
        <div class="insight"><b>Last event</b><span>{q["last_timestamp"]}</span></div>
        <div class="insight"><b>Validation status</b><span>Required fields and allowed outcomes passed parser validation</span></div>
        </div>''',unsafe_allow_html=True
    )

    channels=channel_counts(filtered)
    cdf=pd.DataFrame({"channel":list(channels.keys()),"events":list(channels.values())})
    fig=px.bar(cdf,x="channel",y="events",title="Channel coverage")
    fig.update_traces(marker_color="#9f3543")
    fig.update_layout(**PLOT_LAYOUT)
    st.plotly_chart(fig,use_container_width=True)

    if show_raw:
        st.markdown("#### Filtered event preview")
        st.dataframe(df[["timestamp","source_id","channel","outcome"]],hide_index=True,use_container_width=True)

    export_df=df[["timestamp","source_id","channel","outcome"]].copy()
    st.download_button(
        "Export filtered events",
        export_df.to_csv(index=False),
        "signalscope_filtered_events.csv",
        "text/csv"
    )

# ---------- Methodology ----------
with tabs[4]:
    st.markdown("### Methodology")
    st.markdown("""
<div class="section-card">
<b>Activity score</b><br><br>
The source ranking uses an explainable heuristic:<br><br>
<code>min(100, 22×ln(1+n) + 22×off-hours share + 18×blocked share + 18×unanswered share + 20×event share)</code>
<br><br>
Off-hours are before 08:00 or at/after 21:00 in the timestamp's supplied clock. The score is intentionally descriptive and deterministic — it is not trained on fraud, harassment, or legal labels.
</div>
""",unsafe_allow_html=True)

    m1,m2=st.columns(2)
    with m1:
        st.markdown("#### What SignalScope can do")
        st.markdown("""
- Summarize event frequency and outcome mix
- Compare pseudonymous sources
- Show day/hour concentration patterns
- Surface repeated or off-hour activity
- Export filtered summaries for further analysis
""")
    with m2:
        st.markdown("#### What it cannot establish")
        st.markdown("""
- The real identity behind a source
- Intent, consent, wrongdoing, or fraud
- Whether contact violates any law or policy
- Whether two source IDs belong to the same entity
- Causation from timing patterns alone
""")

    st.markdown("#### Data format")
    st.code("""timestamp,source_id,channel,outcome
2026-08-01T08:00:00,SRC-A,call,missed
2026-08-01T22:00:00,SRC-A,call,blocked
2026-08-02T11:00:00,SRC-B,sms,answered""",language="csv")
    st.caption("Use synthetic or pseudonymized data only. Normalize time zones before comparing timestamps across regions.")

st.markdown("---")
st.caption("SignalScope · Built by Md Nafim Alam · Python · Streamlit · Plotly · Explainable analytics")
