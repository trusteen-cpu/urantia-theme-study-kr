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
    """파일 인코딩 문제를 방지하며 안전하게 읽기"""
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

    prompt = f"""
당신은 유란시아서를 연구하는 신학자입니다.

주제: "{term}"

아래는 이 주제와 관련 있다고 판단되는 유란시아서 본문입니다.

---

## 1부. 신학적 보고서 (700~1000자)
- 이 주제의 유란시아적 의미
- 신성/우주론적 중요성
- 아버지, 최극존
