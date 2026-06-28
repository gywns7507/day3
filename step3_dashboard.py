import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import glob

st.set_page_config(page_title="카페 피드백 대시보드", layout="wide")

base = os.path.dirname(os.path.abspath(__file__))
files = glob.glob(os.path.join(base, "feedback_classified.csv"))
if not files:
    st.error("feedback_classified.csv 없음 — step2_classify.py 먼저 실행하세요.")
    st.stop()

df = pd.read_csv(files[0], encoding="utf-8-sig")
df["별점"] = pd.to_numeric(df["별점"], errors="coerce")
df["받은날짜"] = pd.to_datetime(df["받은날짜"], errors="coerce")

# ── 긴급도 계산 ───────────────────────────────────────
def urgency(row):
    score = 0
    if row["유형"] == "불만":
        score += 2
    if row["감성"] == "부정":
        score += 1
    score += (5 - (row["별점"] if pd.notna(row["별점"]) else 2.5))
    return round(score, 1)

df["긴급도"] = df.apply(urgency, axis=1)

# ── 헤더 ─────────────────────────────────────────────
st.title("☕ 카페 고객 피드백 대시보드")
st.caption(f"분석 기간: {df['받은날짜'].min().strftime('%Y-%m-%d')} ~ {df['받은날짜'].max().strftime('%Y-%m-%d')}  |  총 {len(df)}건")

st.divider()

# ── 지표 카드 ─────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("전체 피드백", len(df))
c2.metric("불만", int((df["유형"] == "불만").sum()), delta=None)
c3.metric("칭찬", int((df["유형"] == "칭찬").sum()), delta=None)
c4.metric("요청", int((df["유형"] == "요청").sum()), delta=None)
avg = df["별점"].mean()
c5.metric("평균 별점", f"{avg:.1f} ★" if pd.notna(avg) else "-")

st.divider()

# ── 차트 영역 ─────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("피드백 유형 분포")
    type_order = ["불만", "요청", "칭찬", "문의"]
    type_colors = {"불만": "#ef4444", "요청": "#f59e0b", "칭찬": "#22c55e", "문의": "#3b82f6"}
    type_counts = df["유형"].value_counts().reindex(type_order, fill_value=0).reset_index()
    type_counts.columns = ["유형", "건수"]
    fig_type = px.bar(
        type_counts, x="유형", y="건수", text="건수",
        color="유형", color_discrete_map=type_colors,
        height=320
    )
    fig_type.update_traces(textposition="outside")
    fig_type.update_layout(showlegend=False, margin=dict(t=20, b=0))
    st.plotly_chart(fig_type, use_container_width=True)

with col_right:
    st.subheader("감성 분포")
    sent_colors = {"긍정": "#22c55e", "부정": "#ef4444", "중립": "#94a3b8"}
    sent_counts = df["감성"].value_counts().reset_index()
    sent_counts.columns = ["감성", "건수"]
    fig_sent = px.pie(
        sent_counts, names="감성", values="건수",
        color="감성", color_discrete_map=sent_colors,
        height=320, hole=0.4
    )
    fig_sent.update_traces(textinfo="label+percent")
    fig_sent.update_layout(margin=dict(t=20, b=0))
    st.plotly_chart(fig_sent, use_container_width=True)

st.divider()

# ── 긴급 불만 Top 3 ───────────────────────────────────
st.subheader("🚨 긴급 불만 Top 3")
top3 = df[df["유형"] == "불만"].sort_values("긴급도", ascending=False).head(3)

if top3.empty:
    st.info("불만 유형 피드백이 없습니다.")
else:
    for rank, (_, row) in enumerate(top3.iterrows(), 1):
        star = f"★ {row['별점']:.0f}" if pd.notna(row["별점"]) else "★ -"
        date = row["받은날짜"].strftime("%Y-%m-%d") if pd.notna(row["받은날짜"]) else "-"
        badge = ["🥇", "🥈", "🥉"][rank - 1]
        with st.container(border=True):
            cols = st.columns([0.05, 0.7, 0.25])
            cols[0].markdown(f"### {badge}")
            cols[1].markdown(f"**{row['내용']}**")
            cols[2].markdown(f"`{date}` &nbsp; {star}<br>경로: {row['경로']}<br>긴급도: **{row['긴급도']}점**", unsafe_allow_html=True)

st.divider()

# ── 날짜별 피드백 추이 ────────────────────────────────
st.subheader("경로별 피드백 현황")
channel = df.groupby(["경로", "유형"]).size().reset_index(name="건수")
channel_total = df["경로"].value_counts().reset_index()
channel_total.columns = ["경로", "합계"]
channel_order = channel_total.sort_values("합계", ascending=False)["경로"].tolist()

fig_channel = px.bar(
    channel, x="경로", y="건수", color="유형",
    color_discrete_map=type_colors,
    barmode="stack", height=320,
    text="건수",
    category_orders={"경로": channel_order}
)
fig_channel.update_traces(textposition="inside", textfont_size=12)
fig_channel.update_layout(
    margin=dict(t=10, b=0),
    xaxis_title="유입 경로",
    yaxis_title="피드백 수",
    legend_title="유형"
)
st.plotly_chart(fig_channel, use_container_width=True)

st.divider()

# ── 전체 데이터 테이블 ────────────────────────────────
with st.expander("전체 피드백 데이터 보기"):
    st.dataframe(
        df[["id", "받은날짜", "경로", "별점", "유형", "감성", "긴급도", "내용"]],
        use_container_width=True,
        column_config={"받은날짜": st.column_config.DateColumn()}
    )
