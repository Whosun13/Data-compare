import streamlit as st
import pandas as pd
from io import StringIO
from thefuzz import fuzz

# Til so'rovi
lang = st.selectbox("Tilni tanlang / Выберите язык / Select Language", ['UZ', 'RU', 'EN'])

# Matnlar lug'ati
texts = {
    'UZ': {
        'title': "📊 Ma'lumotlarni Taqqoslash Platformasi (Demo)",
        'upload_db': "1️⃣ Ma'lumotlar bazasini yuklang (.xlsx yoki .csv)",
        'upload_check': "2️⃣ Tekshiriladigan ma'lumotlarni yuklang yoki kiriting",
        'input_method': "Kiritish usuli",
        'file_upload': "Fayl yuklash",
        'manual_input': "Qo'lda kiritish",
        'textarea_label': "Ma'lumotlarni kiriting (vergul yoki yangi qatordan ajratib)",
        'upload_db_file': "Bazani yuklash",
        'upload_check_file': "Tekshiriladigan ma'lumotlar",
        'select_column_db': "Bazadagi taqqoslanadigan ustunni tanlang",
        'select_column_check': "Tekshiriladigan fayldagi ustunni tanlang",
        'select_extra_columns': "Natijada ko'rsatish uchun qo'shimcha ustunlar",
        'compare_button': "Taqqoslash",
        'results': "Natijalar",
        'exists': "Ha",
        'not_exists': "Yo'q",
        'similar': "O'xshashlar",
        'download_csv': "📥 Natijani yuklab olish (.csv)",
    },
    'RU': {
        'title': "📊 Платформа для сравнения данных (Демо)",
        'upload_db': "1️⃣ Загрузите базу данных (.xlsx или .csv)",
        'upload_check': "2️⃣ Загрузите или введите данные для проверки",
        'input_method': "Способ ввода",
        'file_upload': "Загрузить файл",
        'manual_input': "Ввести вручную",
        'textarea_label': "Введите данные (разделяйте запятой или новой строкой)",
        'upload_db_file': "Загрузить базу",
        'upload_check_file': "Данные для проверки",
        'select_column_db': "Выберите столбец базы для сравнения",
        'select_column_check': "Выберите столбец данных для проверки",
        'select_extra_columns': "Дополнительные столбцы для отображения",
        'compare_button': "Сравнить",
        'results': "Результаты",
        'exists': "Да",
        'not_exists': "Нет",
        'similar': "Похожие",
        'download_csv': "📥 Скачать результат (.csv)",
    },
    'EN': {
        'title': "📊 Data Comparison Platform (Demo)",
        'upload_db': "1️⃣ Upload data base (.xlsx or .csv)",
        'upload_check': "2️⃣ Upload or enter data to check",
        'input_method': "Input method",
        'file_upload': "File upload",
        'manual_input': "Manual input",
        'textarea_label': "Enter data (separate by comma or newline)",
        'upload_db_file': "Upload base",
        'upload_check_file': "Data to check",
        'select_column_db': "Select base column to compare",
        'select_column_check': "Select check data column",
        'select_extra_columns': "Extra columns to display",
        'compare_button': "Compare",
        'results': "Results",
        'exists': "Yes",
        'not_exists': "No",
        'similar': "Similar",
        'download_csv': "📥 Download results (.csv)",
    }
}

# Matnlarni lug'atdan chaqirish uchun yordamchi funksiya
def t(key):
    return texts[lang].get(key, key)


# Quyidagi kodda har bir matn `t('key')` yordamida chaqiriladi:

st.title(t('title'))

st.subheader(t('upload_db'))
uploaded_db = st.file_uploader(t('upload_db_file'), type=["xlsx", "csv"])

st.subheader(t('upload_check'))
input_type = st.radio(t('input_method'), [t('file_upload'), t('manual_input')])

input_data = None
if input_type == t('file_upload'):
    uploaded_check = st.file_uploader(t('upload_check_file'), type=["xlsx", "csv"])
    if uploaded_check is not None:
        if uploaded_check.name.endswith(".xlsx"):
            input_data = pd.read_excel(uploaded_check)
        else:
            input_data = pd.read_csv(uploaded_check)
elif input_type == t('manual_input'):
    raw_text = st.text_area(t('textarea_label'))
    if raw_text.strip():
        items = [x.strip() for x in raw_text.replace("\n", ",").split(",") if x.strip()]
        input_data = pd.DataFrame(items, columns=["InputData"])

if uploaded_db is not None:
    if uploaded_db.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_db)
    else:
        df = pd.read_csv(uploaded_db)

    st.write(f"**{t('upload_db')}**")
    st.dataframe(df)

    if input_data is not None:
        st.write(f"**{t('upload_check')}**")
        st.dataframe(input_data)

        column_to_check = st.selectbox(t('select_column_db'), df.columns)
        input_column_to_check = st.selectbox(t('select_column_check'), input_data.columns)
        extra_columns = st.multiselect(t('select_extra_columns'),
                                       [col for col in df.columns if col != column_to_check])

        if st.button(t('compare_button')):
            df["__norm_col__"] = df[column_to_check].apply(normalize_text)
            input_data["__norm_input__"] = input_data[input_column_to_check].apply(normalize_text)

            results = []
            for item in input_data["__norm_input__"]:
                exact_match = item in df["__norm_col__"].values
                similar_items = []
                for val in df["__norm_col__"].unique():
                    if fuzz.ratio(item, val) >= 80 and val != item:
                        similar_items.append(val)

                match_rows = df[df["__norm_col__"] == item] if exact_match else pd.DataFrame()

                extra_data = {}
                for col in extra_columns:
                    if not match_rows.empty:
                        extra_data[col] = ", ".join(match_rows[col].astype(str).unique())
                    else:
                        extra_data[col] = ""

                results.append({
                    t('title'): item,
                    t('exists'): "Ha" if exact_match else "Yo'q",
                    t('similar'): ", ".join(similar_items) if similar_items else "-",
                    **extra_data
                })

            result_df = pd.DataFrame(results)
            st.subheader(t('results'))
            st.dataframe(result_df)

            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button(t('download_csv'), csv, "natijalar.csv", "text/csv")
