import streamlit as st
import pandas as pd
from io import BytesIO
from thefuzz import fuzz
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Til uchun lug'atlar
texts = {
    "uz": {
        "title": "📊 Ma'lumotlarni Taqqoslash Platformasi (Demo)",
        "upload_db": "1️⃣ Ma'lumotlar bazasini yuklang (.xlsx, .csv, .doc, .docx, .txt)",
        "upload_check": "2️⃣ Tekshiriladigan ma'lumotlarni yuklang yoki kiriting",
        "input_method": "Kiritish usuli",
        "file_upload": "Fayl yuklash",
        "manual_input": "Qo'lda kiritish",
        "load_db": "Bazani yuklash",
        "load_check": "Tekshiriladigan ma'lumotlar",
        "input_area": "Ma'lumotlarni kiriting (vergul yoki yangi qatordan ajratib)",
        "db_loaded": "**Yuklangan ma'lumotlar bazasi:**",
        "input_loaded": "**Tekshiriladigan ma'lumotlar:**",
        "select_column_db": "Bazadagi taqqoslanadigan ustunni tanlang",
        "select_column_input": "Tekshiriladigan fayldagi ustunni tanlang",
        "extra_columns": "Natijada ko'rsatish uchun qo'shimcha ustunlar",
        "similarity_slider": "O'xshashlik foizini tanlang (%)",
        "compare_btn": "Taqqoslash",
        "results": "Natijalar",
        "download_csv": "📥 Natijani yuklab olish (.csv)",
        "download_xlsx": "📥 Natijani yuklab olish (.xlsx)",
        "download_docx": "📥 Natijani yuklab olish (.docx)",
        "unsupported_format": "Qo'llab-quvvatlanmaydigan format"
    },
    "ru": {
        "title": "📊 Платформа сравнения данных (Демо)",
        "upload_db": "1️⃣ Загрузите базу данных (.xlsx, .csv, .doc, .docx, .txt)",
        "upload_check": "2️⃣ Загрузите или введите проверяемые данные",
        "input_method": "Способ ввода",
        "file_upload": "Загрузить файл",
        "manual_input": "Ввести вручную",
        "load_db": "Загрузить базу",
        "load_check": "Проверяемые данные",
        "input_area": "Введите данные (через запятую или новую строку)",
        "db_loaded": "**Загруженная база данных:**",
        "input_loaded": "**Проверяемые данные:**",
        "select_column_db": "Выберите столбец для сравнения в базе",
        "select_column_input": "Выберите столбец во входных данных",
        "extra_columns": "Дополнительные столбцы для отображения в результате",
        "similarity_slider": "Выберите процент сходства (%)",
        "compare_btn": "Сравнить",
        "results": "Результаты",
        "download_csv": "📥 Скачать результат (.csv)",
        "download_xlsx": "📥 Скачать результат (.xlsx)",
        "download_docx": "📥 Скачать результат (.docx)",
        "unsupported_format": "Неподдерживаемый формат"
    }
}

# Matnni normallashtirish funksiyasi (o'zgarmaydi)
def normalize_text(s):
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = s.replace("’", "'").replace("‘", "'").replace("`", "'")
    s = s.replace("o'", "o‘").replace("g'", "g‘")
    s = " ".join(s.split())
    return s

# Word faylini o'qish va boshqalar ... (oldingi kabi)

# Faylni o'qish funksiyasi (oldingi kabi)

# Natijani Word faylga aylantirish funksiyasi (oldingi kabi)

# --- Streamlit interfeysi ---

lang = st.selectbox("Til / Язык", options=["O'zbekcha", "Русский"])

if lang == "O'zbekcha":
    t = texts["uz"]
else:
    t = texts["ru"]

st.title(t["title"])

st.subheader(t["upload_db"])
uploaded_db = st.file_uploader(t["load_db"], type=["xlsx", "csv", "doc", "docx", "txt"])

st.subheader(t["upload_check"])
input_type = st.radio(t["input_method"], [t["file_upload"], t["manual_input"]])

input_data = None
if input_type == t["file_upload"]:
    uploaded_check = st.file_uploader(t["load_check"], type=["xlsx", "csv", "doc", "docx", "txt"])
    if uploaded_check is not None:
        input_data = load_file(uploaded_check)

elif input_type == t["manual_input"]:
    raw_text = st.text_area(t["input_area"])
    if raw_text.strip():
        items = [x.strip() for x in raw_text.replace("\n", ",").split(",") if x.strip()]
        input_data = pd.DataFrame(items, columns=["InputData"])

if uploaded_db is not None:
    df = load_file(uploaded_db)

    if df is not None:
        st.write(t["db_loaded"])
        st.dataframe(df)

        if input_data is not None:
            st.write(t["input_loaded"])
            st.dataframe(input_data)

            column_to_check = st.selectbox(t["select_column_db"], df.columns)
            input_column_to_check = st.selectbox(t["select_column_input"], input_data.columns)
            extra_columns = st.multiselect(t["extra_columns"], [col for col in df.columns if col != column_to_check])

            similarity_threshold = st.slider(t["similarity_slider"], min_value=50, max_value=100, value=80, step=1)

            if st.button(t["compare_btn"]):
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
                        t.get("Kiritilgan", "Kiritilgan"): item,
                        t.get("Mavjud", "Mavjud"): "Ha" if exact_match else "Yo'q",
                        t.get("O'xshashlar", "O'xshashlar"): ", ".join(similar_items) if similar_items else "-",
                        **extra_data
                    })

                result_df = pd.DataFrame(results)
                st.subheader(t["results"])
                st.dataframe(result_df)

                # Yuklab olish tugmalari
                csv = result_df.to_csv(index=False).encode('utf-8')
                st.download_button(t["download_csv"], csv, "natijalar.csv", "text/csv")

                towrite = BytesIO()
                result_df.to_excel(towrite, index=False, engine='openpyxl')
                towrite.seek(0)
                st.download_button(t["download_xlsx"], towrite, "natijalar.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                word_file = df_to_word(result_df)
                st.download_button(t["download_docx"], word_file, "natijalar.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
