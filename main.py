import streamlit as st
import os
import re
from html import escape

st.set_page_config(page_title="유란시아 주제 연구 – Korean (debug)", layout="wide")

st.markdown("## 📘 유란시아 주제 연구 – 한글판 (디버그 모드)")

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OPENAI_API_KEY 환경 변수가 없습니다.")
    st.stop()

DATA_DIR = "data"
CANDIDATE_FILES = ["urantia_ko.txt", "urantia_kr.txt", "urantia.txt"]

def find_existing_path():
    for name in CANDIDATE_FILES:
        path = os.path.join(DATA_DIR, name)
        if os.path.exists(path):
            return path
    return None

KR_PATH = find_existing_path()

def safe_read_text(path: str) -> list[str]:
    encodings = ["utf-8", "utf-8-sig", "cp949", "euc-kr", "latin-1"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                lines = f.readlines()
                # 각 줄에서 BOM, 개행 제거
                cleaned = [l.replace("\ufeff", "").rstrip("\r\n") for l in lines]
                return cleaned
        except:
            continue
    return []

if not KR_PATH:
    st.error("📂 data 폴더에 urantia_ko.txt / urantia_kr.txt / urantia.txt 가 없습니다.")
    st.stop()

urantia_lines = safe_read_text(KR_PATH)

# ---------- 여기서부터 디버그 출력 ----------
st.info(f"📄 읽어온 파일: **{KR_PATH}**")
st.info(f"📏 줄 개수: **{len(urantia_lines)}** 줄")

st.markdown("### 🔍 파일 앞부분(최대 20줄) 미리보기")
for i, line in enumerate(urantia_lines[:20], 1):
    # 줄에 보이지 않는 문자가 있는지 보기 위해 repr로도 보여줌
    st.text(f"{i:03d}: {line}")
    st.code(repr(line))

st.markdown("---")

# ---------- 검색 UI ----------
st.header("1️⃣ 주제(검색어) 입력")
keyword = st.text_input("검색어를 입력하세요 (예: 신, 신성, 미가엘, 조율자)", "")

def search_passages(keyword: str, lines: list[str], limit: int = 200):
    if not keyword:
        return []
    key = keyword.strip()
    # 정규식으로 부분일치
    try:
        pattern = re.compile(re.escape(key))
    except re.error:
        pattern = re.compile(key)

    results = []
    for idx, line in enumerate(lines, 1):
        # 눈에 안 보이는 문자 제거
        clean_line = line.replace("\ufeff", "")
        if re.search(pattern, clean_line):
            results.append(f"{idx}: {clean_line}")
    return results[:limit]

st.header("2️⃣ 검색 결과")
if keyword:
    found = search_passages(keyword, urantia_lines)
    if found:
        for row in found:
            st.markdown(row)
    else:
        st.error("❗이 파일에서는 이 검색어가 안 보입니다. (위에 미리보기 줄에서 실제 단어 형태를 확인해 주세요.)")
else:
    st.info("검색어를 입력하면 이 아래에 매칭되는 줄이 나옵니다.")

# ---------- AI 부분은 일단 빼도 되는데, 필요하면 다시 붙이세요 ----------


