
import streamlit as st
import pandas as pd
import docx
import io

st.set_page_config(page_title="Data Compare", layout="wide")

st.title("📊 Data Compare Platforma — 1-bosqich yangilanish")

st.markdown("**Yangi imkoniyatlar:** .doc, .docx, .txt, .xlsx, .csv fayllar; matnni vergul, qator yoki bo‘sh joy bilan ajratib kiritish.")

# Funksiya: turli fayllarni o'qish
def read_file(uploaded_file):
    file_type = uploaded_file.name.split('.')[-1].lower()

    if file_type in ['xlsx', 'xls']:
        df = pd.read_excel(uploaded_file)
    elif file_type == 'csv':
        df = pd.read_csv(uploaded_file)
    elif file_type in ['txt']:
        text = uploaded_file.read().decode("utf-8")
        df = pd.DataFrame(text.splitlines(), columns=["Data"])
    elif file_type in ['doc', 'docx']:
        doc = docx.Document(uploaded_file)
        data = []
        for table in doc.tables:
            for row in table.rows:
                data.append([cell.text for cell in row.cells])
        if data:
            df = pd.DataFrame(data)
        else:
            text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            df = pd.DataFrame(text.splitlines(), columns=["Data"])
    else:
        st.error("❌ Noto'g'ri format!")
        return None
    return df

# Ma'lumotlar bazasini yuklash
st.header("1️⃣ Ma'lumotlar bazasini yuklash")
db_file = st.file_uploader("Ma'lumotlar bazasini yuklang (.xlsx, .csv, .txt, .doc, .docx)", type=['xlsx','csv','txt','doc','docx'])

if db_file:
    db_df = read_file(db_file)
    if db_df is not None:
        st.dataframe(db_df.head())

        # Taqqoslash ma'lumotlarini kiritish
        st.header("2️⃣ Taqqoslash uchun ma'lumot kiriting yoki fayl yuklang")
        input_type = st.radio("Ma'lumot kiritish usuli:", ["Qo'lda kiritish", "Fayl yuklash"])

        compare_list = []

        if input_type == "Qo'lda kiritish":
            user_input = st.text_area("Ma'lumotlarni kiriting (vergul, qator yoki bo‘sh joy bilan ajratilgan)")
            if user_input.strip():
                # Ajratish: vergul, yangi qator va bo'sh joy
                for item in user_input.replace("\n", " ").replace(",", " ").split():
                    compare_list.append(item.strip())
        else:
            cmp_file = st.file_uploader("Tekshiriladigan ma'lumotlar faylini yuklang", type=['xlsx','csv','txt','doc','docx'])
            if cmp_file:
                cmp_df = read_file(cmp_file)
                if cmp_df is not None:
                    compare_list = cmp_df.iloc[:,0].dropna().astype(str).tolist()

        if compare_list:
            st.write("**Tekshiriladigan ma'lumotlar:**", compare_list)

            # Ustunni tanlash
            column_choice = st.selectbox("Taqqoslash uchun ustunni tanlang", db_df.columns)
            if column_choice:
                db_values = db_df[column_choice].dropna().astype(str).tolist()

                results = {"Topildi": [], "Topilmadi": []}
                for val in compare_list:
                    if val in db_values:
                        results["Topildi"].append(val)
                    else:
                        results["Topilmadi"].append(val)

                st.subheader("✅ Natijalar")
                st.write("**Topildi:**", results["Topildi"])
                st.write("**Topilmadi:**", results["Topilmadi"])

