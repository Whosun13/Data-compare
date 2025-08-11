import streamlit as st
import pandas as pd
from rapidfuzz import fuzz, process

st.set_page_config(page_title="Ma'lumotlar taqqoslash platformasi", layout="wide")

st.title("📊 Ma'lumotlar taqqoslash platformasi")

# Ma'lumotlar bazasi yuklash
st.sidebar.header("1. Ma'lumotlar bazasini yuklang")
db_file = st.sidebar.file_uploader("Excel fayl yuklang", type=["xlsx", "xls", "csv"])

if db_file:
    if db_file.name.endswith(".csv"):
        df_db = pd.read_csv(db_file)
    else:
        df_db = pd.read_excel(db_file)
    st.write("**📂 Yuklangan ma'lumotlar bazasi:**")
    st.dataframe(df_db)

    # Taqqoslash uchun ustun tanlash
    compare_column = st.selectbox("Taqqoslash uchun ustunni tanlang", df_db.columns)

    # Lookup ustunini tanlash (VLOOKUP o‘xshash)
    lookup_column = st.selectbox("Natijada ko‘rsatish uchun boshqa ustunni tanlang (ixtiyoriy)", ["Yo'q"] + list(df_db.columns))

    # Tekshiriladigan ma'lumotlarni yuklash
    st.sidebar.header("2. Tekshiriladigan ma'lumotlar")
    check_file = st.sidebar.file_uploader("Excel yoki CSV yuklang", type=["xlsx", "xls", "csv"])
    input_texts = []
    
    if check_file:
        if check_file.name.endswith(".csv"):
            df_check = pd.read_csv(check_file)
        else:
            df_check = pd.read_excel(check_file)
        st.write("**📂 Tekshiriladigan ma'lumotlar:**")
        st.dataframe(df_check)
        check_column = st.selectbox("Qaysi ustunni tekshiramiz?", df_check.columns)
        input_texts = df_check[check_column].astype(str).tolist()

    else:
        st.write("Yoki qo‘lda kiriting (vergul bilan ajrating):")
        text_input = st.text_area("Ma'lumotlarni kiriting")
        if text_input:
            input_texts = [x.strip() for x in text_input.split(",")]

    # Qidiruv turi
    search_type = st.radio("Qidiruv turi", ["Aniq moslik", "O‘xshash (fuzzy) moslik"])

    # Natija
    if st.button("Taqqoslash"):
        results = []
        for item in input_texts:
            if search_type == "Aniq moslik":
                match = df_db[df_db[compare_column].astype(str) == str(item)]
                if not match.empty:
                    found = True
                    extra = match[lookup_column].values[0] if lookup_column != "Yo'q" else ""
                else:
                    found = False
                    extra = ""
            else:
                matches = process.extract(str(item), df_db[compare_column].astype(str), scorer=fuzz.partial_ratio, limit=1)
                if matches and matches[0][1] > 70:
                    found = True
                    idx = df_db[df_db[compare_column] == matches[0][0]].index[0]
                    extra = df_db.loc[idx, lookup_column] if lookup_column != "Yo'q" else ""
                else:
                    found = False
                    extra = ""

            results.append({"Kiritilgan ma'lumot": item, "Topildimi?": "Ha" if found else "Yo‘q", "Qo‘shimcha": extra})

        df_result = pd.DataFrame(results)
        st.write("**🔍 Natija:**")
        st.dataframe(df_result)

        csv = df_result.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Natijani yuklab olish (CSV)", csv, "natija.csv", "text/csv")

else:
    st.info("Iltimos, avval ma'lumotlar bazasini yuklang.")
