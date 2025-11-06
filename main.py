import streamlit as st
import os
import re
from openai import OpenAI

# -----------------------
# 기본 설정
# -----------------------
st.set_page_config(page_title="유란시아 주제 연구 – Korean", layout="wide")
st.title("📘 유란시아 주제 연구 – Korean Edition")
st.caption("한글 유란시아서 본문에서 주제를 찾아 AI가 보고서와 슬라이드를 생성합니다.")

# -----------------------
# API Key (Render 환경 변수)
# -----------------------
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ OpenAI API 키가 없습니다. Render 환경 변수에 OPENAI_API_KEY를 설정하세요.")
    st.stop()

# -----------------------
# 파일 경로 설정
# -----------------------
DATA_DIR = "data"
CANDIDATE_FILES = ["urantia_ko.txt", "urantia_kr.txt", "urantia.txt"]

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
    encodings = ["utf-8", "utf-8-sig", "cp949", "euc-kr", "latin-1"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                lines = f.readlines()
                cleaned = [l.replace("\ufeff", "").rstrip("\r\n") for l in lines if l.strip()]
                return cleaned
        except Exception:
            continue
    return []

@st.cache_data
def load_urantia_kr():
    if not KR_PATH:
        return []
    return safe_read_text(KR_PATH)

urantia_lines = load_urantia_kr()

# -----------------------
# 검색 함수
# -----------------------
def search_passages(keyword: str, lines: list[str], limit: int = 200):
    if not keyword:
        return []
    key = keyword.strip()
    try:
        pattern = re.compile(re.escape(key))
    except re.error:
        pattern = re.compile(key)

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
    client = OpenAI(api_key=api_key)
    joined_passages = "\n".join(passages) or "관련 구절을 찾지 못했습니다."

    # 삼중 따옴표 제거한 안전한 문자열 (Render 호환)
    prompt = (
        "당신은 유란시아서를 연구하는 신학자입니다.\n\n"
        f"주제: {term}\n\n"
        "아래는 이 주제와 관련 있다고 판단되는 유란시아서 본문입니다.\n\n"
        "---\n\n"
        "1부. 신학적 보고서 (700~1000자)\n"
        "- 이 주제의 유란시아적 의미\n"
        "- 신성/우주론적 중요성\n"
        "- 아버지, 최극존재, 생각조율자와의 관계\n"
        "- 인간 상승 체험과의 연결\n"
        "- 오늘의 신앙과 삶에 주는 교훈\n\n"
        "2부. 5장 슬라이드 개요\n"
        "각 슬라이드는 다음 요소를 포함합니다:\n"
        "- 제목 1줄\n"
        "- 핵심 포인트 3~5개\n"
        "- 발표자 노트 (300~500자)\n\n"
        "형식 예시:\n"
        "# 슬라이드 1: ...\n"
        "- ...\n"
        "발표자 노트: ...\n\n"
        f"---\n\n참고 본문:\n{joined_passages}"
    )

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
st.subheader("1️⃣ 주제 입력")
term = st.text_input("예: 신성, 최극자, 조율자, 미가엘, 상승, 신앙", "", key="term_input")

st.subheader("2️⃣ 관련 구절 검색 결과")

if not KR_PATH:
    st.error("📂 data 폴더에 urantia_ko.txt (또는 urantia_kr.txt)가 없습니다.")
else:
    if not urantia_lines:
        st.error("⚠️ 파일은 있지만 내용이 비어 있습니다. 인코딩(UTF-8) 확인이 필요합니다.")
    else:
        passages = search_passages(term, urantia_lines) if term else []
        if term and passages:
            for p in passages:
                st.markdown(p)
        elif term:
            st.info("관련 구절이 없습니다. 다른 단어나 주제를 입력해보세요.")

st.subheader("3️⃣ AI 보고서 + 슬라이드 생성")

if st.button("✨ AI 보고서 및 슬라이드 생성"):
    with st.spinner("AI가 보고서를 작성 중입니다..."):
        passages = search_passages(term, urantia_lines)
        result = generate_gpt_report_and_slides(term, passages)
    st.markdown(result)
else:
    st.caption("주제를 입력하고 버튼을 누르면 AI가 분석 결과를 생성합니다.")

