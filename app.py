import streamlit as st
import pandas as pd
from io import BytesIO
from thefuzz import fuzz
from docx import Document

# Ma'lumotlarni tozalash funksiyasi
def normalize_text(s):
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = s.replace("’", "'").replace("‘", "'").replace("`", "'")
    s = s.replace("o'", "o‘").replace("g'", "g‘")
    s = "".join(s.split())
    return s

st.title("📊 Ma'lumotlarni Taqqoslash Platformasi (Yangi versiya)")

# 1️⃣ Ma'lumotlar bazasini yuklash
st.subheader("1️⃣ Ma'lumotlar bazasini yuklang (.xlsx yoki .csv)")
uploaded_db = st.file_uploader("Bazani yuklash", type=["xlsx", "csv"])

# 2️⃣ Tekshiriladigan ma'lumotlarni kiritish
st.subheader("2️⃣ Tekshiriladigan ma'lumotlarni yuklang yoki kiriting")
input_type = st.radio("Kiritish usuli", ["Fayl yuklash", "Qo'lda kiritish"])

input_data = None
if input_type == "Fayl yuklash":
    uploaded_check = st.file_uploader("Tekshiriladigan ma'lumotlar", type=["xlsx", "csv"])
    if uploaded_check is not None:
        if uploaded_check.name.endswith(".xlsx"):
            input_data = pd.read_excel(uploaded_check)
        else:
            input_data = pd.read_csv(uploaded_check)
elif input_type == "Qo'lda kiritish":
    raw_text = st.text_area("Ma'lumotlarni kiriting (vergul yoki yangi qatordan ajratib)")
    if raw_text.strip():
        # Faqat vergul va yangi qator bo‘yicha bo‘lish
        items = [x.strip() for x in raw_text.replace("\n", ",").split(",") if x.strip()]
        input_data = pd.DataFrame(items, columns=["InputData"])

# 3️⃣ Agar baza yuklangan bo‘lsa
if uploaded_db is not None:
    if uploaded_db.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_db)
    else:
        df = pd.read_csv(uploaded_db)

    st.write("**Yuklangan ma'lumotlar bazasi:**")
    st.dataframe(df)

    if input_data is not None:
        st.write("**Tekshiriladigan ma'lumotlar:**")
        st.dataframe(input_data)

        # Taqqoslash uchun ustun tanlash
        column_to_check = st.selectbox("Taqqoslash uchun ustun tanlang", df.columns)

        # Qo'shimcha ustunlar tanlash
        extra_columns = st.multiselect("Natijada ko'rsatish uchun qo'shimcha ustunlar", [col for col in df.columns if col != column_to_check])

        if st.button("Taqqoslash"):
            # Ma'lumotlarni normallashtirish
            df["__norm_col__"] = df[column_to_check].apply(normalize_text)
            input_data["__norm_input__"] = input_data[input_data.columns[0]].apply(normalize_text)

            results = []
            for item in input_data["__norm_input__"]:
                exact_match = item in df["__norm_col__"].values
                similar_items = []
                for val in df["__norm_col__"].unique():
                    if fuzz.ratio(item, val) >= 80 and val != item:
                        similar_items.append(val)  # foizsiz

                match_row = df[df["__norm_col__"] == item].iloc[0] if exact_match else None
                extra_data = {col: match_row[col] if match_row is not None else "" for col in extra_columns}

                results.append({
                    "Kiritilgan": item,
                    "Mavjud": "Ha" if exact_match else "Yo'q",
                    "O'xshashlar": ", ".join(similar_items) if similar_items else "-",
                    **extra_data
                })

            result_df = pd.DataFrame(results)

            # Filtrlash
            filter_choice = st.selectbox("Filtr:", ["Barchasi", "Faqat mavjudlar", "Faqat mavjud bo'lmaganlar"])
            if filter_choice == "Faqat mavjudlar":
                result_df = result_df[result_df["Mavjud"] == "Ha"]
            elif filter_choice == "Faqat mavjud bo'lmaganlar":
                result_df = result_df[result_df["Mavjud"] == "Yo'q"]

            st.subheader("Natijalar")
            st.dataframe(result_df)

            # 📥 CSV yuklab olish
            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Yuklab olish (.csv)", csv, "natijalar.csv", "text/csv")

            # 📥 Excel yuklab olish
            excel_buffer = BytesIO()
            result_df.to_excel(excel_buffer, index=False)
            st.download_button("📥 Yuklab olish (.xlsx)", excel_buffer.getvalue(), "natijalar.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # 📥 Word yuklab olish
            doc = Document()
            table = doc.add_table(rows=1, cols=len(result_df.columns))
            table.style = 'Table Grid'
            hdr_cells = table.rows[0].cells
            for i, col_name in enumerate(result_df.columns):
                hdr_cells[i].text = col_name
            for _, row in result_df.iterrows():
                row_cells = table.add_row().cells
                for i, value in enumerate(row):
                    row_cells[i].text = str(value)
            word_buffer = BytesIO()
            doc.save(word_buffer)
            st.download_button("📥 Yuklab olish (.docx)", word_buffer.getvalue(), "natijalar.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
