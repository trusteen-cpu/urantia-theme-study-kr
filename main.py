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
입력한 주제를 유란시아서 본문에서 찾아서  
AI가 **신학적 보고서**와 **5장짜리 슬라이드 개요**를 만들어 줍니다.
""")

# -----------------------
# 🔑 API 키
# -----------------------
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ OpenAI API 키가 없습니다. Render 환경 변수에 OPENAI_API_KEY를 넣어주세요.")
    st.stop()

# -----------------------
# 데이터 경로 (ko → kr → 기본)
# -----------------------
DATA_DIR = "data"
CANDIDATE_FILES = [
    "urantia_ko.txt",
    "urantia_kr.txt",
    "urantia.txt",
]

def find_existing_path():
    for name in CANDIDATE_FILES:
        path = os.path.join(DATA_DIR, name)
        if os.path.exists(path):
            return path
    return None

KR_PATH = find_existing_path()

# -----------------------
# 파일 읽기
# -----------------------
def safe_read_text(path: str) -> list[str]:
    """여러 인코딩 시도해서 줄 단위로 읽기"""
    encodings = ["utf-8", "utf-8-sig", "cp949", "euc-kr", "latin-1"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                # 줄마다 BOM 제거 + 공백 제거
                return [line.replace("\ufeff", "").rstrip("\n") for line in f.readlines()]
        except:
            continue
    return []

@st.cache_data
def load_urantia_kr():
    if not KR_PATH:
        return []
    return safe_read_text(KR_PATH)

urantia_lines = load_urantia_kr()

# -----------------------
# 검색 함수 (절번호 붙이기)
# -----------------------
def search_passages(keyword: str, lines: list[str], limit: int = 200):
    if not keyword:
        return []
    key = keyword.strip().replace("\ufeff", "")
    try:
        pattern = re.compile(key)
    except re.error:
        pattern = re.compile(re.escape(key))

    results = []
    for i, line in enumerate(lines, 1):
        clean_line = line.replace("\ufeff", "")
        if re.search(pattern, clean_line):
            results.append(f"{i}: {clean_line}")
    return results[:limit]

# -----------------------
# GPT 보고서 생성
# -----------------------
def generate_gpt_report_and_slides(term: str, passages: list[str]):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except Exception as e:
        return f"⚠️ OpenAI 라이브러리 로드 오류: {e}"

    joined_passages = "\n".join(passages) or "관련 구절을 찾지 못했습니다."

    prompt = f"""
당신은 유란시아서를 연구하는 신학자입니다.

주제: "{term}"

아래는 이 주제와 관련 있다고 판단되는 유란시아서 본문입니다.

---

## 1부. 신학적 보고서 (700~1000자)
- 이 주제의 유란시아적 의미
- 신성/우주론적 중요성
- 아버지, 최극존재, 생각조율자와의 관계
- 인간 상승 체험과의 연결
- 오늘의 신앙과 삶에 주는 교훈

## 2부. 5장 슬라이드 개요
각 슬라이드는
- 제목 1줄
- 핵심 포인트 3~5개
- `발표자 노트:` 300~500자

아래 형식으로 출력하세요:

# 슬라이드 1: ...
- ...
발표자 노트: ...

# 슬라이드 2: ...
...

---

### 참고 본문:
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
term = st.text_input("예: 신성, 최극자, 조율자, 미가엘, 상승, 신앙", "", key="kr_theme_input")

st.header("2️⃣ 관련 유란시아서 구절")

if not KR_PATH:
    st.error("📂 data 폴더에 urantia_ko.txt 또는 urantia_kr.txt 파일이 없습니다. 하나를 올려주세요.")
else:
    if not urantia_lines:
        st.error(f"⚠️ {KR_PATH} 파일을 읽었지만 내용이 비어 있습니다. 인코딩(utf-8, euc-kr) 확인이 필요합니다.")
    else:
        passages = search_passages(term, urantia_lines) if term else []
        if term and passages:
            for p in passages:
                st.markdown(p)
        elif term:
            st.info("관련 구절이 없습니다. 다른 단어나 주제를 입력해보세요.")

        # 디버그용 미리보기
        st.divider()
        st.write("📄 파일 미리보기 (처음 5줄):")
        for line in urantia_lines[:5]:
            st.text(line)

st.header("3️⃣ AI 보고서 + 슬라이드 생성")
if st.button("✨ 보고서 및 슬라이드 생성", key="generate_btn_kr"):
    with st.spinner("AI가 보고서와 슬라이드를 생성 중입니다..."):
        passages = search_passages(term, urantia_lines) if term else []
        result = generate_gpt_report_and_slides(term, passages)
    st.markdown(result)
else:
    st.info("주제를 입력하고 버튼을 누르면 AI가 내용을 만들어 줍니다.")

