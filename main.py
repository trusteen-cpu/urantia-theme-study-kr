import streamlit as st
import os
import re
from openai import OpenAI

# -----------------------
# 기본 설정
# -----------------------
st.set_page_config(page_title="유란시아 주제 연구 – Korean Plus", layout="wide")
st.title("📘 유란시아 주제 연구 – Korean Plus Edition")
st.caption("한글 유란시아서 본문에서 주제를 찾아 AI가 보고서와 슬라이드를 생성합니다. (각주 포함 확장판)")

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
# 검색 함수 (하이라이트 + 절번호 감지)
# -----------------------
def search_passages(keyword: str, lines: list[str], limit: int = 2000):
    """검색어를 포함한 구절을 찾아 하이라이트 및 절번호 추출"""
    if not keyword:
        return []

    key = keyword.strip()
    try:
        pattern = re.compile(re.escape(key))
    except re.error:
        pattern = re.compile(key)

    results = []
    for line in lines:
        clean_line = line.replace("\ufeff", "")
        if re.search(pattern, clean_line):
            # 절번호 추출 (예: 5:6.7 형태)
            match = re.search(r"\d+:\d+\.\d+", clean_line)
            verse_ref = f"({match.group(0)})" if match else ""
            # 검색어 하이라이트
            highlighted = re.sub(
                pattern,
                lambda m: f"<mark style='background-color:#fffd75'>{m.group(0)}</mark>",
                clean_line,
            )
            results.append(f"{highlighted} {verse_ref}")
    return results[:limit]

# -----------------------
# GPT 보고서 + 슬라이드 생성
# -----------------------
def generate_gpt_report_and_slides(term: str, passages: list[str]):
    client = OpenAI(api_key=api_key)
    joined_passages = "\n".join(passages) or "관련 구절을 찾지 못했습니다."

    # AI에게 각주 포함 보고서 지시
    prompt = (
        "당신은 유란시아서를 연구하는 신학자이자 교육자입니다.\n\n"
        f"주제: {term}\n\n"
        "아래는 이 주제와 관련 있는 유란시아서의 구절들입니다.\n\n"
        "이 구절의 절 번호를 보고서 본문에서 각주처럼 인용해 주세요. "
        "예: 생각조절자는 인간 내면의 신성한 단편이다 (107:0.1).\n\n"
        "---\n\n"
        "1부. 신학적 보고서 (2000~2500자)\n"
        "- 이 주제의 유란시아적 의미\n"
        "- 신성/우주론적 중요성\n"
        "- 아버지, 최극존재, 생각조율자와의 관계\n"
        "- 인간 상승 체험과의 연결\n"
        "- 오늘의 신앙과 삶에 주는 교훈\n"
        "※ 각주 예시: (123:4.5) 형태로 절 번호 삽입\n\n"
        "2부. 5장 슬라이드 개요\n"
        "각 슬라이드는 다음 요소를 포함합니다:\n"
        "- 제목 1줄\n"
        "- 핵심 포인트 3~5개\n"
        "- 발표자 노트 (300~500자)\n\n"
        "형식 예시:\n"
        "# 슬라이드 1: ...\n"
        "- ...\n"
        "발표자 노트: ...\n\n"
        f"---\n\n참고 구절들:\n{joined_passages}"
    )

    try:
        resp = client.chat.completions.create(
            model="gpt-4o
