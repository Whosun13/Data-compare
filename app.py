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

# Fayl yuklash va DataFrame ga o'qish funksiyasi
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
        st.error(texts["unsupported_format"][current_lang])
        return None

# Til uchun lug'at
texts = {
    "title": {
        "uz": "📊 Ma'lumotlarni Taqqoslash Platformasi (Demo)",
        "ru": "📊 Платформа сравнения данных (Демо)",
        "en": "📊 Data Comparison Platform (Demo)"
    },
    "upload_db": {
        "uz": "1️⃣ Ma'lumotlar bazasini yuklang (.xlsx, .csv, .doc, .docx, .txt)",
        "ru": "1️⃣ Загрузите базу данных (.xlsx, .csv, .doc, .docx, .txt)",
        "en": "1️⃣ Upload database (.xlsx, .csv, .doc, .docx, .txt)"
    },
    "upload_check": {
        "uz": "2️⃣ Tekshiriladigan ma'lumotlarni yuklang yoki kiriting",
        "ru": "2️⃣ Загрузите или введите проверяемые данные",
        "en": "2️⃣ Upload or enter data to check"
    },
    "input_method": {
        "uz": "Kiritish usuli",
        "ru": "Способ ввода",
        "en": "Input method"
    },
    "file_upload": {
        "uz": "Fayl yuklash",
        "ru": "Загрузка файла",
        "en": "File upload"
    },
    "manual_input": {
        "uz": "Qo'lda kiritish",
        "ru": "Ручной ввод",
        "en": "Manual input"
    },
    "input_placeholder": {
        "uz": "Ma'lumotlarni kiriting (vergul yoki yangi qatordan ajratib)",
        "ru": "Введите данные (через запятую или с новой строки)",
        "en": "Enter data (comma or newline separated)"
    },
    "choose_db_column": {
        "uz": "Bazadagi taqqoslanadigan ustunni tanlang",
        "ru": "Выберите столбец для сравнения в базе",
        "en": "Select database column to compare"
    },
    "choose_input_column": {
        "uz": "Tekshiriladigan fayldagi ustunni tanlang",
        "ru": "Выберите столбец из проверяемого файла",
        "en": "Select input file column"
    },
    "extra_columns": {
        "uz": "Natijada ko'rsatish uchun qo'shimcha ustunlar",
        "ru": "Дополнительные столбцы для отображения",
        "en": "Additional columns to show in results"
    },
    "similarity_threshold": {
        "uz": "O'xshashlik minimal balli",
        "ru": "Минимальный порог похожести",
        "en": "Similarity threshold"
    },
    "compare_button": {
        "uz": "Taqqoslash",
        "ru": "Сравнить",
        "en": "Compare"
    },
    "results_title": {
        "uz": "Natijalar",
        "ru": "Результаты",
        "en": "Results"
    },
    "download_csv": {
        "uz": "📥 Natijani yuklab olish (.csv)",
        "ru": "📥 Скачать результат (.csv)",
        "en": "📥 Download results (.csv)"
    },
    "match_yes": {
        "uz": "Ha",
        "ru": "Да",
        "en": "Yes"
    },
    "match_no": {
        "uz": "Yo'q",
        "ru": "Нет",
        "en": "No"
    },
    "unsupported_format": {
        "uz": "Qo'llab-quvvatlanmaydigan format",
        "ru": "Неподдерживаемый формат",
        "en": "Unsupported format"
    }
}

# Tilni tanlash
lang_options = {"O‘zbekcha": "uz", "Русский": "ru", "English": "en"}
selected_lang = st.selectbox("Tilni tanlang / Select language / Выберите язык", list(lang_options.keys()))
current_lang = lang_options[selected_lang]

# Streamlit interfeysini tanlangan tilga mos chiqarish
st.title(texts["title"][current_lang])

st.subheader(texts["upload_db"][current_lang])
uploaded_db = st.file_uploader("", type=["xlsx", "csv", "doc", "docx", "txt"])

st.subheader(texts["upload_check"][current_lang])
input_type = st.radio(texts["input_method"][current_lang], [texts["file_upload"][current_lang], texts["manual_input"][current_lang]])

input_data = None
if input_type == texts["file_upload"][current_lang]:
    uploaded_check = st.file_uploader("", type=["xlsx", "csv", "doc", "docx", "txt"])
    if uploaded_check is not None:
        input_data = load_file(uploaded_check)
elif input_type == texts["manual_input"][current_lang]:
    raw_text = st.text_area(texts["input_placeholder"][current_lang])
    if raw_text.strip():
        items = [x.strip() for x in raw_text.replace("\n", ",").split(",") if x.strip()]
        input_data = pd.DataFrame(items, columns=["InputData"])

similarity_threshold = st.slider(texts["similarity_threshold"][current_lang], min_value=50, max_value=100, value=80, step=1)

if uploaded_db is not None:
    df = load_file(uploaded_db)

    if df is not None:
        st.write(f"**{texts['upload_db'][current_lang]}**")
        st.dataframe(df)

        if input_data is not None:
            st.write(f"**{texts['upload_check'][current_lang]}**")
            st.dataframe(input_data)

            column_to_check = st.selectbox(texts["choose_db_column"][current_lang], df.columns)
            input_column_to_check = st.selectbox(texts["choose_input_column"][current_lang], input_data.columns)

            extra_columns = st.multiselect(texts["extra_columns"][current_lang],
                                           [col for col in df.columns if col != column_to_check])

            if st.button(texts["compare_button"][current_lang]):
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
                        "Mavjud": texts["match_yes"][current_lang] if exact_match else texts["match_no"][current_lang],
                        "O'xshashlar": ", ".join(similar_items) if similar_items else "-",
                        **extra_data
                    })

                result_df = pd.DataFrame(results)
                st.subheader(texts["results_title"][current_lang])
                st.dataframe(result_df)

                csv = result_df.to_csv(index=False).encode('utf-8')
                st.download_button(texts["download_csv"][current_lang], csv, "natijalar.csv", "text/csv")
