from groq import Groq
import pandas as pd
import os
import glob
import json
import re
import time

base = os.path.dirname(os.path.abspath(__file__))
csv_files = glob.glob(os.path.join(base, "feedback_cleaned.csv"))
if not csv_files:
    raise FileNotFoundError("feedback_cleaned.csv 없음 — 먼저 step1_clean.py 실행")

df = pd.read_csv(csv_files[0], encoding="utf-8-sig")
print(f"행 수: {len(df)}")

client = Groq(api_key=os.environ["GROQ_API_KEY"])

SYSTEM = """당신은 카페 고객 피드백 분류 전문가입니다.
피드백을 아래 두 가지 기준으로 분류하세요.

유형(type):
- 불만: 부정적 경험, 개선 요구, 실망
- 요청: 새로운 기능·메뉴 추가 등 제안
- 칭찬: 긍정적 경험, 만족, 감사
- 문의: 정보 요청, 질문

감성(sentiment):
- 긍정: 전반적으로 좋은 감정
- 부정: 전반적으로 나쁜 감정
- 중립: 중립적이거나 혼합

반드시 JSON만 반환하세요. 다른 설명 없이 JSON만.
예시: {"type": "칭찬", "sentiment": "긍정"}"""

def classify(text: str, debug: bool = False) -> dict:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        max_tokens=100,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": str(text)}
        ]
    )
    raw = response.choices[0].message.content.strip()
    if debug:
        print(f"  [RAW] {raw}")
    m = re.search(r'\{[^}]+\}', raw, re.DOTALL)
    if not m:
        print(f"  [WARN] JSON 없음: {raw}")
        return {"type": "문의", "sentiment": "중립"}
    try:
        return json.loads(m.group())
    except json.JSONDecodeError:
        print(f"  [WARN] 파싱 실패: {m.group()}")
        return {"type": "문의", "sentiment": "중립"}

types = []
sentiments = []

for i, row in df.iterrows():
    feedback = row["내용"]
    print(f"[{i+1:02d}/{len(df)}] 분류 중: {str(feedback)[:30]}...")
    debug = (i == 0)  # 첫 번째 행만 raw 응답 출력
    result = classify(feedback, debug=debug)
    print(f"  → 유형: {result.get('type')} | 감성: {result.get('sentiment')}")
    types.append(result.get("type", "문의"))
    sentiments.append(result.get("sentiment", "중립"))
    time.sleep(0.3)

df["유형"] = types
df["감성"] = sentiments

out = os.path.join(base, "feedback_classified.csv")
df.to_csv(out, index=False, encoding="utf-8-sig")
print(f"\n분류 완료 → {out}")
print(df[["id", "받은날짜", "별점", "유형", "감성", "내용"]].to_string(index=False))
