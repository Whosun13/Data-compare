import streamlit as st
import pandas as pd
from io import StringIO
from thefuzz import fuzz
from docx import Document

# DOC/DOCX fayldan matn olish funksiyasi
def read_docx(file):
    doc = Document(file)
    full_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text.strip())
    return pd.DataFrame(full_text, columns=["Data"])

# Ma'lumotlarni tozalash funksiyasi
def normalize_text(s):
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = s.replace("’", "'").replace("‘", "'").replace("`", "'")  
    s = s.replace("o'", "o‘").replace("g'", "g‘")  
    s = "".join(s.split())  
    return s

st.title("📊 Ma'lumotlarni Taqqoslash Platformasi (Demo)")

# 1️⃣ Ma'lumotlar bazasini yuklash
st.subheader("1️⃣ Ma'lumotlar bazasini yuklang (.xlsx, .csv, .doc, .docx)")
uploaded_db = st.file_uploader("Bazani yuklash", type=["xlsx", "csv", "doc", "docx"])

# 2️⃣ Tekshiriladigan ma'lumotlar
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
        elif uploaded_check.name.endswith((".doc", ".docx")):
            input_data = read_docx(uploaded_check)
elif input_type == "Qo'lda kiritish":
    raw_text = st.text_area("Ma'lumotlarni kiriting (vergul, yangi qatordan yoki bo‘sh joy bilan ajratib)")
    if raw_text.strip():
        items = [x.strip() for x in raw_text.replace("\n", ",").split(",") if x.strip()]
        input_data = pd.DataFrame(items, columns=["InputData"])

# Agar baza yuklangan bo‘lsa
if uploaded_db is not None:
    if uploaded_db.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_db)
    elif uploaded_db.name.endswith(".csv"):
        df = pd.read_csv(uploaded_db)
    elif uploaded_db.name.endswith((".doc", ".docx")):
        df = read_docx(uploaded_db)

    st.write("**Yuklangan ma'lumotlar bazasi:**")
    st.dataframe(df)

    if input_data is not None:
        st.write("**Tekshiriladigan ma'lumotlar:**")
        st.dataframe(input_data)

        # Taqqoslash uchun ustunni tanlash
        column_to_check = st.selectbox("Bazadagi taqqoslanadigan ustun", df.columns)
        input_column_to_check = st.selectbox("Tekshiriladigan ustun", input_data.columns)

        # Qo'shimcha ustunlarni tanlash
        extra_columns = st.multiselect("Natijada ko'rsatish uchun qo'shimcha ustunlar", [col for col in df.columns if col != column_to_check])

        if st.button("Taqqoslash"):
            df["__norm_col__"] = df[column_to_check].apply(normalize_text)
            input_data["__norm_input__"] = input_data[input_column_to_check].apply(normalize_text)

            results = []
            for item in input_data["__norm_input__"]:
                exact_match_rows = df[df["__norm_col__"] == item]
                exact_match = not exact_match_rows.empty

                similar_items = []
                for val in df["__norm_col__"].unique():
                    if fuzz.ratio(item, val) >= 80 and val != item:
                        similar_items.append(val)

                row_result = {
                    "Kiritilgan": item,
                    "Mavjud": "Ha" if exact_match else "Yo'q",
                    "O'xshashlar": ", ".join(similar_items) if similar_items else "-"
                }

                if extra_columns and exact_match:
                    for col in extra_columns:
                        row_result[col] = ", ".join(exact_match_rows[col].astype(str).unique())

                results.append(row_result)

            result_df = pd.DataFrame(results)
            st.subheader("Natijalar")
            st.dataframe(result_df)

            # CSV yuklab olish
            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Natijani yuklab olish (.csv)", csv, "natijalar.csv", "text/csv")
