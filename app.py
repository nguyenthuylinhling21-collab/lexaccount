import streamlit as st
import fitz
from docx import Document
import requests
import io
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import google.generativeai as genai

GEMINI_API_KEY = "AIzaSyCQHA63fqSMYox74A8b5QGwZfMVslIvj_Q"
DRIVE_FOLDER_ID = st.secrets["DRIVE_FOLDER_ID"]
GOOGLE_CREDS = st.secrets["GOOGLE_CREDENTIALS"]

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

st.set_page_config(page_title="LexAccount", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
* { font-family: 'Open Sans', sans-serif; }
[data-testid="stAppViewContainer"] { background-color: #f5f5f5; }
[data-testid="stSidebar"] { background-color: #000000; }
[data-testid="stSidebar"] * { color: white !important; }
.stButton > button { background-color: #86BC25; color: white; border-radius: 0px; border: none; padding: 10px 28px; font-weight: 700; text-transform: uppercase; font-size: 13px; }
.stButton > button:hover { background-color: #6a9a1e; }
.stTabs [data-baseweb="tab-list"] { gap: 0px; border-bottom: 3px solid #86BC25; }
.stTabs [data-baseweb="tab"] { background-color: white; border-radius: 0px; padding: 10px 24px; font-weight: 600; color: #000000; border: 1px solid #ddd; }
.stTabs [aria-selected="true"] { background-color: #86BC25 !important; color: white !important; border: none !important; }
.stTextInput input { border-radius: 0px; border: 1px solid #cccccc; border-bottom: 2px solid #86BC25; padding: 10px; }
.answer-box { background-color: white; border-left: 4px solid #86BC25; padding: 24px; margin-top: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); line-height: 1.8; }
.stat-box { background: white; border-top: 3px solid #86BC25; padding: 20px 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
.stat-num { font-size: 2.2rem; font-weight: 700; color: #000000; }
.stat-label { font-size: 0.82rem; color: #666; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
.section-title { font-size: 1.1rem; font-weight: 700; color: #000000; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; border-bottom: 2px solid #86BC25; padding-bottom: 6px; }
</style>
""", unsafe_allow_html=True)

if "last_question" not in st.session_state:
    st.session_state.last_question = ""

@st.cache_resource
def get_creds():
    creds = service_account.Credentials.from_service_account_info(
        dict(GOOGLE_CREDS),
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return creds

@st.cache_resource
def get_drive_service():
    creds = get_creds()
    return build("drive", "v3", credentials=creds)

@st.cache_data(ttl=300)
def list_drive_files():
    service = get_drive_service()
    results = service.files().list(
        q=f"'{DRIVE_FOLDER_ID}' in parents and trashed=false",
        fields="files(id, name, mimeType)"
    ).execute()
    return results.get("files", [])

def download_file(file_id):
    creds = get_creds()
    if not creds.valid:
        creds.refresh(Request())
    headers = {"Authorization": f"Bearer {creds.token}"}
    response = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
        headers=headers
    )
    return io.BytesIO(response.content)

def file_to_text(buf, filename):
    if filename.endswith(".pdf"):
        doc = fitz.open(stream=buf.read(), filetype="pdf")
        return "\n".join([doc[i].get_text() for i in range(len(doc))])
    elif filename.endswith(".docx"):
        doc = Document(buf)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    return ""

def ask_ai(prompt):
    response = model.generate_content(prompt)
    return response.text

def search_in_docs(keyword, files):
    results = []
    for f in files:
        buf = download_file(f["id"])
        text = file_to_text(buf, f["name"])
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if keyword.lower() in line.lower() and line.strip():
                results.append({"file": f["name"], "dong": i + 1, "noi_dung": line.strip()})
    return results

with st.sidebar:
    st.markdown("## ⚖️ LexAccount")
    st.markdown("*Thư viện Pháp luật Kế toán & Tài chính*")
    st.divider()
    st.markdown("**📚 VĂN BẢN TRONG THƯ VIỆN**")
    try:
        files = list_drive_files()
        if files:
            for f in files:
                st.markdown(f"📄 {f['name'][:25]}...")
        else:
            st.info("Chưa có văn bản nào")
    except Exception as e:
        st.error(f"Lỗi kết nối Drive: {str(e)}")
        files = []

st.markdown("""
<div style="background:#000;padding:18px 28px;margin:-1rem -1rem 0 -1rem;display:flex;align-items:center;gap:8px">
<span style="color:white;font-size:1.6rem;font-weight:700">LexAccount</span>
<span style="color:#86BC25;font-size:2rem;font-weight:900">.</span>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<p style="color:#555;font-size:0.9rem;border-left:3px solid #86BC25;padding-left:12px;margin-bottom:24px">Thư viện Pháp luật Kế toán & Tài chính Doanh nghiệp — Tra cứu thông minh, trích dẫn chính xác</p>', unsafe_allow_html=True)

try:
    files = list_drive_files()
except:
    files = []

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="stat-box"><div class="stat-num">{len(files)}</div><div class="stat-label">Văn bản trong thư viện</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="stat-box"><div class="stat-num">Cloud</div><div class="stat-label">Lưu trữ Google Drive</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="stat-box"><div class="stat-num">AI</div><div class="stat-label">Trích dẫn tự động</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🤖  Hỏi đáp AI", "🔍  Tìm kiếm nhanh", "📖  Xem văn bản"])

with tab1:
    st.markdown('<p class="section-title">Hỏi đáp pháp luật có trích dẫn</p>', unsafe_allow_html=True)
    if not files:
        st.warning("Chưa có văn bản trong thư viện.")
    else:
        file_names = [f["name"] for f in files]
        selected_names = st.multiselect("Chọn văn bản để hỏi:", file_names, default=file_names)
        selected_files = [f for f in files if f["name"] in selected_names]
        question = st.text_input("Nhập câu hỏi (nhấn Enter để hỏi):", placeholder="Ví dụ: Thông tư 99 quy định gì về kế toán?", key="question_input")
        auto_submit = question.strip() != "" and question != st.session_state.last_question
        st.session_state.last_question = question
        if (st.button("🔎 HỎI AI") or auto_submit) and question.strip() and selected_files:
            with st.spinner("Đang phân tích tài liệu..."):
                all_text = ""
                for f in selected_files:
                    buf = download_file(f["id"])
                    text = file_to_text(buf, f["name"])
                    all_text += f"\n\n=== TÀI LIỆU: {f['name']} ===\n{text[:5000]}"
                prompt = f"""Bạn là chuyên gia pháp luật kế toán tài chính Việt Nam.
Dựa vào các tài liệu pháp luật dưới đây, hãy trả lời câu hỏi.
Yêu cầu: Nêu rõ trích dẫn từ tài liệu nào, điều khoản nào cụ thể.
Trả lời bằng tiếng Việt đầy đủ dấu.

TÀI LIỆU:
{all_text}

CÂU HỎI: {question}

Trả lời chi tiết, nêu rõ nguồn trích dẫn."""
                try:
                    answer = ask_ai(prompt)
                    st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Lỗi: {str(e)}")

with tab2:
    st.markdown('<p class="section-title">Tìm kiếm nhanh trong văn bản</p>', unsafe_allow_html=True)
    if not files:
        st.warning("Chưa có văn bản trong thư viện.")
    else:
        keyword = st.text_input("Nhập từ khóa tìm kiếm:", placeholder="Ví dụ: điều 5, kế toán trưởng, hóa đơn...")
        if st.button("🔍 TÌM KIẾM") and keyword:
            with st.spinner("Đang tìm kiếm..."):
                results = search_in_docs(keyword, files)
            if results:
                st.success(f"Tìm thấy **{len(results)}** kết quả cho từ khóa: *{keyword}*")
                for r in results[:20]:
                    with st.expander(f"📄 {r['file']} — Dòng {r['dong']}"):
                        st.markdown(r['noi_dung'])
            else:
                st.info(f"Không tìm thấy kết quả nào cho: *{keyword}*")

with tab3:
    st.markdown('<p class="section-title">Xem nội dung văn bản</p>', unsafe_allow_html=True)
    if not files:
        st.warning("Chưa có văn bản trong thư viện.")
    else:
        file_names = [f["name"] for f in files]
        selected_name = st.selectbox("Chọn văn bản để xem:", file_names)
        selected_file = next((f for f in files if f["name"] == selected_name), None)
        if selected_file:
            with st.spinner("Đang tải văn bản..."):
                buf = download_file(selected_file["id"])
                if selected_name.endswith(".pdf"):
                    doc = fitz.open(stream=buf.read(), filetype="pdf")
                    st.info(f"Tổng số trang: **{len(doc)}**")
                    page_num = st.slider("Chọn trang:", 1, len(doc), 1)
                    page = doc[page_num - 1]
                    text = page.get_text()
                    st.text_area("Nội dung:", text, height=400)
                elif selected_name.endswith(".docx"):
                    doc = Document(buf)
                    full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                    st.text_area("Nội dung:", full_text, height=400)
