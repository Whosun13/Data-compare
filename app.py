import streamlit as st
import pandas as pd
from io import BytesIO
from thefuzz import fuzz
from docx import Document

# Matnni normallashtirish funksiyasi
def normalize_text(s):
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = s.replace("’", "'").replace("‘", "'").replace("`", "'")
    s = s.replace("o'", "o‘").replace("g'", "g‘")
    s = " ".join(s.split())
    return s

# Word faylini o'qish (matn yoki jadval)
def read_doc_or_docx(file):
    file_bytes = file.read()
    file.seek(0)
    doc = Document(BytesIO(file_bytes))

    if doc.tables:
        tables_data = []
        for table in doc.tables:
            for row in table.rows:
                row_data = [cell.text.strip() for cell in row.cells]
                tables_data.append(row_data)
        df = pd.DataFrame(tables_data)
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)
        return df

    full_text = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    return pd.DataFrame(full_text, columns=["Data"])

# Faylni o'qish funksiyasi
def load_file(file):
    if file.name.endswith(".xlsx"):
        return pd.read_excel(file)
    elif file.name.endswith(".csv"):
        return pd.read_csv(file)
    elif file.name.endswith(".doc") or file.name.endswith(".docx"):
        return read_doc_or_docx(file)
    elif file.name.endswith(".txt"):
        text = file.read().decode("utf-8")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return pd.DataFrame(lines, columns=["Data"])
    else:
        st.error("Qo'llab-quvvatlanmaydigan format")
        return None

# --- Streamlit interfeysi ---

st.title("📊 Ma'lumotlarni Taqqoslash Platformasi (Demo)")

st.subheader("1️⃣ Ma'lumotlar bazasini yuklang (.xlsx, .csv, .doc, .docx, .txt)")
uploaded_db = st.file_uploader("Bazani yuklash", type=["xlsx", "csv", "doc", "docx", "txt"])

st.subheader("2️⃣ Tekshiriladigan ma'lumotlarni yuklang yoki kiriting")
input_type = st.radio("Kiritish usuli", ["Fayl yuklash", "Qo'lda kiritish"])

input_data = None
if input_type == "Fayl yuklash":
    uploaded_check = st.file_uploader("Tekshiriladigan ma'lumotlar", type=["xlsx", "csv", "doc", "docx", "txt"])
    if uploaded_check is not None:
        input_data = load_file(uploaded_check)

elif input_type == "Qo'lda kiritish":
    raw_text = st.text_area("Ma'lumotlarni kiriting (vergul yoki yangi qatordan ajratib)")
    if raw_text.strip():
        items = [x.strip() for x in raw_text.replace("\n", ",").split(",") if x.strip()]
        input_data = pd.DataFrame(items, columns=["InputData"])

if uploaded_db is not None:
    df = load_file(uploaded_db)

    if df is not None:
        st.write("**Yuklangan ma'lumotlar bazasi:**")
        st.dataframe(df)

        if input_data is not None:
            st.write("**Tekshiriladigan ma'lumotlar:**")
            st.dataframe(input_data)

            column_to_check = st.selectbox("Bazadagi taqqoslanadigan ustunni tanlang", df.columns)
            input_column_to_check = st.selectbox("Tekshiriladigan fayldagi ustunni tanlang", input_data.columns)
            extra_columns = st.multiselect("Natijada ko'rsatish uchun qo'shimcha ustunlar",
                                           [col for col in df.columns if col != column_to_check])

            # O'xshashlik foizini tanlash uchun slider
            similarity_threshold = st.slider("O'xshashlik foizini tanlang (%)", min_value=50, max_value=100, value=80, step=1)

            if st.button("Taqqoslash"):
                df["__norm_col__"] = df[column_to_check].apply(normalize_text)
                input_data["__norm_input__"] = input_data[input_column_to_check].apply(normalize_text)

                results = []
                for item in input_data["__norm_input__"]:
                    exact_match = item in df["__norm_col__"].values

                    match_rows = df[df["__norm_col__"] == item] if exact_match else pd.DataFrame()

                    similar_items = []
                    for val in df["__norm_col__"].unique():
                        if fuzz.ratio(item, val) >= similarity_threshold and val != item:
                            similar_items.append(val)

                    extra_data = {}
                    for col in extra_columns:
                        if not match_rows.empty:
                            extra_data[col] = ", ".join(match_rows[col].astype(str).unique())
                        else:
                            extra_data[col] = ""

                    results.append({
                        "Kiritilgan": item,
                        "Mavjud": "Ha" if exact_match else "Yo'q",
                        "O'xshashlar": ", ".join(similar_items) if similar_items else "-",
                        **extra_data
                    })

                result_df = pd.DataFrame(results)
                st.subheader("Natijalar")
                st.dataframe(result_df)

                csv = result_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Natijani yuklab olish (.csv)", csv, "natijalar.csv", "text/csv")
