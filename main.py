import streamlit as st
import os
import re
from html import escape

# -----------------------
# 기본 설정
# -----------------------
st.set_page_config(page_title="유란시아 주제 연구 – 한국어판", layout="wide")

st.markdown("""
# 📘 유란시아 주제 연구 (Urantia Theme Study – Korean Edition)
입력한 주제와 관련된 유란시아서 구절을 찾아서,  
AI가 **주제 보고서**와 **5장짜리 슬라이드 개요**를 생성합니다.
""")

# -----------------------
# 🔑 환경 변수에서 API Key 불러오기
# -----------------------
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("⚠️ OpenAI API 키가 설정되어 있지 않습니다. Render 또는 GitHub Secrets에 등록해주세요.")
    st.stop()

# -----------------------
# 데이터 로드
# -----------------------
DATA_DIR = "data"
KR_PATH = os.path.join(DATA_DIR, "urantia_kr.txt")

import chardet  # ← 맨 위 import 목록에 추가!

def safe_read_text(path: str) -> list[str]:
    """파일 인코딩을 자동 감지하여 올바르게 읽기"""
    try:
        with open(path, "rb") as f:
            raw = f.read()
            enc = chardet.detect(raw)["encoding"] or "utf-8"
            text = raw.decode(enc, errors="ignore")
            # 줄 단위 분리, BOM 제거
            lines = [l.replace("\ufeff", "").strip() for l in text.splitlines() if l.strip()]
            return lines
    except Exception as e:
        print("파일 읽기 오류:", e)
        return []

@st.cache_data
def load_urantia_kr():
    if not os.path.exists(KR_PATH):
        return []
    return safe_read_text(KR_PATH)

urantia_lines = load_urantia_kr()

# -----------------------
# 검색 및 하이라이트
# -----------------------
def highlight_term(text: str, term: str) -> str:
    """검색된 용어를 형광색으로 강조"""
    if not term:
        return escape(text)
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    highlighted = pattern.sub(lambda m: f"<mark style='background-color:#fffd75'>{escape(m.group(0))}</mark>", text)
    return highlighted

def search_passages(keyword: str, lines: list[str], limit: int = 200):
    if not keyword:
        return []

    # 검색어 정리 (공백, BOM 제거)
    key = keyword.strip().replace("\ufeff", "")

    # 정규식 패턴: 키워드가 단어 내부에 포함되어도 매칭
    try:
        pattern = re.compile(key)
    except re.error:
        pattern = re.compile(re.escape(key))

    results = []
    for i, l in enumerate(lines, 1):
        clean_line = l.strip().replace("\ufeff", "")  # BOM 제거
        if re.search(pattern, clean_line):
            # 절 번호 + 본문 표시
            results.append(f"{i}: {clean_line}")

    return results[:limit]


# -----------------------
# GPT 보고서 및 슬라이드 생성
# -----------------------
def generate_gpt_report_and_slides(term: str, passages: list[str]):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except Exception as e:
        return f"⚠️ OpenAI 라이브러리 로드 오류: {e}"

    joined_passages = "\n".join(passages) or "관련 구절을 찾지 못했습니다."

    prompt = f"""
당신은 유란시아서의 내용을 해석하고 가르치는 신학자입니다.

주제: "{term}"

아래는 유란시아서에서 이 주제와 관련된 구절들입니다.

---

## 1부. 신학적 보고서 (700~1000자)
- 이 주제의 유란시아적 의미와 기원  
- 신성, 우주론적 관점에서의 중요성  
- 아버지, 최상 존재, 조절자와의 관계  
- 인간의 상승 체험과 철학적 함의  
- 인간 신앙과 삶에 주는 교훈

---

## 2부. 슬라이드 5장 개요
다음 형식으로 **정확히 5장의 슬라이드**를 만드세요.

각 슬라이드는:
- 제목 1줄  
- 핵심 요점 3~5개  
- `발표자 노트:` (300~500자) — 설명용 요약문

형식 예시:

# 슬라이드 1: <제목>
- 핵심 포인트
- 핵심 포인트
발표자 노트: ...

# 슬라이드 2: ...
...

---

### 참고 구절:
{joined_passages}
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "너는 유란시아서 신학과 교육에 능통한 학자이다."},
                {"role": "user", "content": prompt}
            ]
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"⚠️ GPT 오류 발생: {e}"

# -----------------------
# UI
# -----------------------
st.header("1️⃣ 주제 입력")
term = st.text_input("예: 최상 존재, 신성, 생각 조절자, 신앙, 상승, 미가엘", "", key="kr_theme_input")

passages = search_passages(term, urantia_lines) if term else []

st.header("2️⃣ 관련 유란시아서 구절")
if not urantia_lines:
    st.error("📂 data/urantia_kr.txt 파일이 없습니다. data 폴더에 파일을 추가하세요.")
elif term and passages:
    for i, line in enumerate(passages, 1):
        st.markdown(f"<b>{i}.</b> {highlight_term(line, term)}", unsafe_allow_html=True)
elif term:
    st.info("관련 구절이 없습니다. 다른 단어나 주제를 입력해보세요.")

st.header("3️⃣ AI 보고서 + 슬라이드 생성")
if st.button("✨ 보고서 및 슬라이드 생성", key="generate_btn_kr"):
    with st.spinner("AI가 보고서와 슬라이드를 생성 중입니다..."):
        result = generate_gpt_report_and_slides(term, passages)
    st.markdown(result)
else:
    st.info("주제를 입력하고 버튼을 눌러 보고서를 생성하세요.")
st.divider()
st.write("📄 파일 미리보기 (처음 5줄):")
for line in urantia_lines[:5]:
    st.text(line)
