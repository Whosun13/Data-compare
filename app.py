import streamlit as st
import pandas as pd
from difflib import SequenceMatcher
from io import BytesIO
from docx import Document

# --- Funksiya: o'xshashlikni hisoblash ---
def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio() * 100

# --- DOCX yuklab olish ---
def to_docx(df):
    doc = Document()
    doc.add_table(df.shape[0]+1, df.shape[1])

    # ustun nomlari
    for j, col in enumerate(df.columns):
        doc.tables[0].cell(0, j).text = str(col)

    # qatorlar
    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            doc.tables[0].cell(i+1, j).text = str(df.iat[i, j])
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

st.set_page_config(page_title="Data Compare", layout="wide")

st.title("📊 Data Compare Platforma (V2.0)")
st.write("Ma'lumotlarni yuklang, ustunlarni tanlang va taqqoslang.")

# --- Bazani yuklash ---
db_file = st.file_uploader("Ma'lumotlar bazasini yuklang (.csv, .xlsx, .docx)", type=["csv", "xlsx", "docx"])
df_db = None
if db_file:
    if db_file.name.endswith(".csv"):
        df_db = pd.read_csv(db_file)
    elif db_file.name.endswith(".xlsx"):
        df_db = pd.read_excel(db_file)
    elif db_file.name.endswith(".docx"):
        doc = Document(db_file)
        data = [[cell.text for cell in row.cells] for table in doc.tables for row in table.rows]
        df_db = pd.DataFrame(data[1:], columns=data[0])

# --- Tekshiriladigan ma'lumotlarni yuklash yoki kiritish ---
check_input_method = st.radio("Tekshiriladigan ma'lumotlarni kiriting yoki yuklang:",
                               ["Qo'lda kiritish", "Fayl yuklash"])
df_check = None
check_data = None

if check_input_method == "Qo'lda kiritish":
    raw_text = st.text_area("Ma'lumotlarni kiriting (vergul, satr yoki bo'sh joy bilan ajratilgan)")
    if raw_text:
        parts = [x.strip() for x in raw_text.replace("\n", ",").replace(" ", ",").split(",") if x.strip()]
        df_check = pd.DataFrame(parts, columns=["Check_Data"])
else:
    check_file = st.file_uploader("Tekshiriladigan ma'lumotlarni yuklang (.csv, .xlsx, .docx)", type=["csv", "xlsx", "docx"])
    if check_file:
        if check_file.name.endswith(".csv"):
            df_check = pd.read_csv(check_file)
        elif check_file.name.endswith(".xlsx"):
            df_check = pd.read_excel(check_file)
        elif check_file.name.endswith(".docx"):
            doc = Document(check_file)
            data = [[cell.text for cell in row.cells] for table in doc.tables for row in table.rows]
            df_check = pd.DataFrame(data[1:], columns=data[0])

# --- Taqqoslash ---
if df_db is not None and df_check is not None:
    compare_column = st.selectbox("Taqqoslash uchun ustunni tanlang", df_db.columns)
    show_columns = st.multiselect("Natijada ko'rsatish uchun qo'shimcha ustunlar", df_db.columns)

    min_similarity = st.slider("Minimal o'xshashlik foizi", 0, 100, 80)

    results = []
    for item in df_check.iloc[:, 0].astype(str):
        best_match = None
        best_score = 0
        extra_data = {}
        for val in df_db[compare_column].astype(str):
            score = similarity(item.lower(), val.lower())
            if score > best_score:
                best_score = score
                best_match = val
        if best_score >= min_similarity:
            row_data = df_db[df_db[compare_column].astype(str) == best_match]
            if not row_data.empty:
                for col in show_columns:
                    extra_data[col] = row_data.iloc[0][col]
        results.append({
            "Input": item,
            "Best Match": best_match if best_score >= min_similarity else None,
            "Similarity %": round(best_score, 2),
            **extra_data
        })

    df_results = pd.DataFrame(results)

    # Filtr opsiyasi
    filter_sim = st.checkbox("Faqat mos kelganlarini ko'rsatish")
    if filter_sim:
        df_results = df_results[df_results["Best Match"].notna()]

    st.dataframe(df_results)

    # Yuklab olish
    csv_data = df_results.to_csv(index=False).encode("utf-8")
    xlsx_buffer = BytesIO()
    with pd.ExcelWriter(xlsx_buffer, engine="xlsxwriter") as writer:
        df_results.to_excel(writer, index=False)
    xlsx_buffer.seek(0)
    docx_buffer = to_docx(df_results)

    st.download_button("📥 CSV yuklab olish", csv_data, "results.csv", "text/csv")
    st.download_button("📥 XLSX yuklab olish", xlsx_buffer, "results.xlsx")
    st.download_button("📥 DOCX yuklab olish", docx_buffer, "results.docx")
