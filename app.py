import streamlit as st
import pandas as pd
from thefuzz import fuzz

# --- Til sozlamalari ---
langs = {
    "uz": {
        "title": "📊 Ma'lumotlarni Taqqoslash Platformasi (Demo)",
        "upload_db": "1️⃣ Ma'lumotlar bazasini yuklang (.xlsx yoki .csv)",
        "upload_check": "2️⃣ Tekshiriladigan ma'lumotlarni yuklang yoki kiriting",
        "file_upload": "Fayl yuklash",
        "manual_input": "Qo'lda kiritish",
        "choose_column_db": "Bazadagi taqqoslanadigan ustunni tanlang",
        "choose_column_input": "Tekshiriladigan fayldagi ustunni tanlang",
        "extra_columns": "Natijada ko'rsatish uchun qo'shimcha ustunlar",
        "compare_button": "Taqqoslash",
        "results": "Natijalar",
        "download_csv": "📥 Natijani yuklab olish (.csv)",
        "existing": "Mavjud",
        "not_existing": "Yo'q",
        "similar": "O'xshashlar",
        "mode_label": "Rejimni tanlang",
        "lang_label": "Tilni tanlang",
        "tooltip_db_col": "Taqqoslash uchun bazadagi ustunni tanlang",
        "tooltip_input_col": "Tekshiriladigan fayldagi ustunni tanlang",
        "tooltip_extra_cols": "Natijada ko'rsatmoqchi bo'lgan qo'shimcha ustunlarni tanlang",
    },
    "ru": {
        "title": "📊 Платформа для сравнения данных (Демо)",
        "upload_db": "1️⃣ Загрузите базу данных (.xlsx или .csv)",
        "upload_check": "2️⃣ Загрузите или введите проверяемые данные",
        "file_upload": "Загрузить файл",
        "manual_input": "Ввести вручную",
        "choose_column_db": "Выберите столбец базы для сравнения",
        "choose_column_input": "Выберите столбец проверяемого файла",
        "extra_columns": "Дополнительные столбцы для отображения",
        "compare_button": "Сравнить",
        "results": "Результаты",
        "download_csv": "📥 Скачать результат (.csv)",
        "existing": "Есть",
        "not_existing": "Нет",
        "similar": "Похожие",
        "mode_label": "Выберите режим",
        "lang_label": "Выберите язык",
        "tooltip_db_col": "Выберите столбец базы для сравнения",
        "tooltip_input_col": "Выберите столбец проверяемого файла",
        "tooltip_extra_cols": "Выберите дополнительные столбцы для отображения",
    },
    "en": {
        "title": "📊 Data Comparison Platform (Demo)",
        "upload_db": "1️⃣ Upload database (.xlsx or .csv)",
        "upload_check": "2️⃣ Upload or input data to check",
        "file_upload": "File upload",
        "manual_input": "Manual input",
        "choose_column_db": "Select database column to compare",
        "choose_column_input": "Select input file column",
        "extra_columns": "Additional columns to display",
        "compare_button": "Compare",
        "results": "Results",
        "download_csv": "📥 Download result (.csv)",
        "existing": "Exists",
        "not_existing": "Not exists",
        "similar": "Similar",
        "mode_label": "Choose mode",
        "lang_label": "Choose language",
        "tooltip_db_col": "Select the database column to compare",
        "tooltip_input_col": "Select the input file column",
        "tooltip_extra_cols": "Select additional columns to display",
    }
}

# --- Matnni tozalash ---
def normalize_text(s):
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = s.replace("’", "'").replace("‘", "'").replace("`", "'")
    s = s.replace("o'", "o‘").replace("g'", "g‘")
    s = " ".join(s.split())
    return s

# --- Kunduz / Tungi rejim CSS ---
def set_mode_css(mode, lang):
    night_vals = {
        "uz": "Tungi",
        "ru": "Тёмная",
        "en": "Dark"
    }
    if mode == night_vals[lang]:
        st.markdown("""
            <style>
            body, .css-18e3th9, .css-1d391kg, .st-bb {
                background-color: #121212 !important;
                color: white !important;
            }
            .css-18e3th9 * , .css-1d391kg * {
                color: white !important;
            }
            .css-1d391kg, .st-bb {
                background-color: #121212 !important;
            }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            body, .css-18e3th9, .css-1d391kg, .st-bb {
                background-color: white !important;
                color: black !important;
            }
            .css-18e3th9 * , .css-1d391kg * {
                color: black !important;
            }
            .css-1d391kg, .st-bb {
                background-color: white !important;
            }
            </style>
        """, unsafe_allow_html=True)

# --- Dastur boshlanishi ---

# Session state uchun tilni boshqarish
if "lang" not in st.session_state:
    st.session_state.lang = "uz"

lang = st.selectbox("🌐 " + "Choose language / Tilni tanlang / Выберите язык",
                    options=["uz", "ru", "en"],
                    index=["uz", "ru", "en"].index(st.session_state.lang))

if lang != st.session_state.lang:
    st.session_state.lang = lang

text = langs[lang]

# Kunduz/tungi rejim tanlovi
mode_options = {
    "uz": ["Kunduzgi", "Tungi"],
    "ru": ["Светлая", "Тёмная"],
    "en": ["Light", "Dark"]
}

if "mode" not in st.session_state:
    st.session_state.mode = mode_options[lang][0]  # Default kunduzgi

mode = st.radio(text["mode_label"], mode_options[lang], index=mode_options[lang].index(st.session_state.mode))
if mode != st.session_state.mode:
    st.session_state.mode = mode

set_mode_css(st.session_state.mode, lang)

st.title(text["title"])

# 1️⃣ Ma'lumotlar bazasini yuklash
st.subheader(text["upload_db"])
uploaded_db = st.file_uploader(text["upload_db"], type=["xlsx", "csv"])

# 2️⃣ Tekshiriladigan ma'lumotlarni yuklash yoki kiritish
st.subheader(text["upload_check"])
input_type = st.radio("", [text["file_upload"], text["manual_input"]])

input_data = None
if input_type == text["file_upload"]:
    uploaded_check = st.file_uploader(text["upload_check"], type=["xlsx", "csv"])
    if uploaded_check is not None:
        if uploaded_check.name.endswith(".xlsx"):
            input_data = pd.read_excel(uploaded_check)
        else:
            input_data = pd.read_csv(uploaded_check)
elif input_type == text["manual_input"]:
    raw_text = st.text_area(text["upload_check"])
    if raw_text.strip():
        items = [x.strip() for x in raw_text.replace("\n", ",").split(",") if x.strip()]
        input_data = pd.DataFrame(items, columns=["InputData"])

if uploaded_db is not None:
    if uploaded_db.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_db)
    else:
        df = pd.read_csv(uploaded_db)

    st.write(f"**{text['upload_db']}**")
    st.dataframe(df)

    if input_data is not None:
        st.write(f"**{text['upload_check']}**")
        st.dataframe(input_data)

        # Ustun tanlashlar va caption tooltiplar
        st.write(text["choose_column_db"])
        col1 = st.selectbox("", df.columns)
        st.caption(text["tooltip_db_col"])

        st.write(text["choose_column_input"])
        col2 = st.selectbox("", input_data.columns)
        st.caption(text["tooltip_input_col"])

        st.write(text["extra_columns"])
        extra_cols = st.multiselect("", [col for col in df.columns if col != col1])
        st.caption(text["tooltip_extra_cols"])

        if st.button(text["compare_button"]):
            df["__norm_col__"] = df[col1].apply(normalize_text)
            input_data["__norm_input__"] = input_data[col2].apply(normalize_text)

            results = []
            for item in input_data["__norm_input__"]:
                exact_match = item in df["__norm_col__"].values
                similar_items = []
                for val in df["__norm_col__"].unique():
                    if fuzz.ratio(item, val) >= 80 and val != item:
                        similar_items.append(val)

                match_rows = df[df["__norm_col__"] == item] if exact_match else pd.DataFrame()

                extra_data = {}
                for col in extra_cols:
                    if not match_rows.empty:
                        extra_data[col] = ", ".join(match_rows[col].astype(str).unique())
                    else:
                        extra_data[col] = ""

                results.append({
                    text["choose_column_db"]: item,
                    text["existing"]: text["existing"] if exact_match else text["not_existing"],
                    text["similar"]: ", ".join(similar_items) if similar_items else "-",
                    **extra_data
                })

            result_df = pd.DataFrame(results)
            st.subheader(text["results"])
            st.dataframe(result_df)

            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button(text["download_csv"], csv, "natijalar.csv", "text/csv")
