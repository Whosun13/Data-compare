import streamlit as st
import pandas as pd
from io import StringIO, BytesIO
from thefuzz import fuzz
from docx import Document
import mammoth

# Ma'lumotlarni tozalash funksiyasi
def normalize_text(s):
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = s.replace("’", "'").replace("‘", "'").replace("", "'")
    s = s.replace("o'", "o‘").replace("g'", "g‘")
    s = "".join(s.split())
    return s

# Word faylini o'qish funksiyasi
def read_doc_or_docx(file):
    file_bytes = file.read()
    file.seek(0)  # o'qilgandan keyin qayta ishlash uchun kursorni qaytarish

    # Agar fayl .doc bo'lsa, mammoth orqali .docx ga aylantiramiz
    if file.name.endswith(".doc"):
        with BytesIO(file_bytes) as doc_buffer:
            result = mammoth.convert_to_bytes(doc_buffer)
            file_bytes = result.value

    # Endi faylni python-docx bilan ochamiz
    doc = Document(BytesIO(file_bytes))

    # Agar faylda jadval bo'lsa
    if doc.tables:
        tables_data = []
        for table in doc.tables:
            table_rows = []
            for row in table.rows:
                table_rows.append([cell.text.strip() for cell in row.cells])
            tables_data.extend(table_rows)

        df = pd.DataFrame(tables_data)
        df.columns = df.iloc[0]
        df = df[1:]
        return df.reset_index(drop=True)

    # Agar jadval bo'lmasa, oddiy matn sifatida
    full_text = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    return pd.DataFrame(full_text, columns=["Data"])


st.title("📊 Ma'lumotlarni Taqqoslash Platformasi (Demo)")

# 1️⃣ Ma'lumotlar bazasini yuklash
st.subheader("1️⃣ Ma'lumotlar bazasini yuklang (.xlsx, .csv, .doc, .docx)")
uploaded_db = st.file_uploader("Bazani yuklash", type=["xlsx", "csv", "doc", "docx"])

# 2️⃣ Tekshiriladigan ma'lumotlarni kiritish
st.subheader("2️⃣ Tekshiriladigan ma'lumotlarni yuklang yoki kiriting")
input_type = st.radio("Kiritish usuli", ["Fayl yuklash", "Qo'lda kiritish"])
input_data = None

if input_type == "Fayl yuklash":
    uploaded_check = st.file_uploader("Tekshiriladigan ma'lumotlar", type=["xlsx", "csv", "doc", "docx"])
    if uploaded_check is not None:
        if uploaded_check.name.endswith(".xlsx"):
            input_data = pd.read_excel(uploaded_check)
        elif uploaded_check.name.endswith(".csv"):
            input_data = pd.read_csv(uploaded_check)
        elif uploaded_check.name.endswith(".doc") or uploaded_check.name.endswith(".docx"):
            input_data = read_doc_or_docx(uploaded_check)

elif input_type == "Qo'lda kiritish":
    raw_text = st.text_area("Ma'lumotlarni kiriting (vergul bilan ajrating)")
    if raw_text.strip():
        items = [x.strip() for x in raw_text.split(",") if x.strip()]
        input_data = pd.DataFrame(items, columns=["InputData"])

# 🔍 Taqqoslash jarayoni
if uploaded_db is not None:
    if uploaded_db.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_db)
    elif uploaded_db.name.endswith(".csv"):
        df = pd.read_csv(uploaded_db)
    elif uploaded_db.name.endswith(".doc") or uploaded_db.name.endswith(".docx"):
        df = read_doc_or_docx(uploaded_db)

    st.write("**Yuklangan ma'lumotlar bazasi:**")
    st.dataframe(df)

    if input_data is not None:
        st.write("**Tekshiriladigan ma'lumotlar:**")
        st.dataframe(input_data)

        col1 = st.selectbox("Bazada qaysi ustunni tekshiramiz?", df.columns)
        col2 = st.selectbox("Tekshiriladigan faylda qaysi ustunni olamiz?", input_data.columns)

        extra_cols = st.multiselect("Natijada qo'shimcha ustunlar", df.columns)

        if st.button("Taqqoslash"):
            df["__norm_col__"] = df[col1].apply(normalize_text)
            input_data["__norm_input__"] = input_data[col2].apply(normalize_text)

            results = []
            for item in input_data["__norm_input__"]:
                exact_match_rows = df[df["__norm_col__"] == item]
                if not exact_match_rows.empty:
                    for _, row in exact_match_rows.iterrows():
                        res = {"Kiritilgan": row[col1], "Mavjud": "Ha"}
                        for c in extra_cols:
                            res[c] = row[c]
                        results.append(res)
                else:
                    results.append({"Kiritilgan": item, "Mavjud": "Yo'q"})

            result_df = pd.DataFrame(results)
            st.subheader("Natijalar")
            st.dataframe(result_df)

            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Natijani yuklab olish (.csv)", csv, "natijalar.csv", "text/csv")
