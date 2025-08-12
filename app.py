import streamlit as st
import pandas as pd
from io import StringIO
from thefuzz import fuzz

# Ma'lumotlarni tozalash funksiyasi
def normalize_text(s):
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = s.replace("’", "'").replace("‘", "'").replace("`", "'")  # turli tutuq belgilarni bir xil qilish
    s = s.replace("o'", "o‘").replace("g'", "g‘")  # o' -> o‘, g' -> g‘
    s = "".join(s.split())  # barcha probellarni olib tashlash
    return s

st.title("📊 Ma'lumotlarni Taqqoslash Platformasi (Demo)")

# Foydalanuvchidan ma'lumotlar bazasini yuklash
st.subheader("1️⃣ Ma'lumotlar bazasini yuklang (.xlsx yoki .csv)")
uploaded_db = st.file_uploader("Bazani yuklash", type=["xlsx", "csv"])

# Foydalanuvchidan tekshiriladigan ma'lumotlarni kiritish
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
    raw_text = st.text_area("Ma'lumotlarni kiriting (vergul, yangi qatordan yoki bo‘sh joy bilan ajratib)")
    if raw_text.strip():
        # Vergul, yangi qator va probel orqali bo‘lish
        items = [x.strip() for x in raw_text.replace("\n", ",").replace(" ", ",").split(",") if x.strip()]
        input_data = pd.DataFrame(items, columns=["InputData"])

# Agar baza yuklangan bo‘lsa
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

        # Taqqoslash uchun ustunni tanlash
        column_to_check = st.selectbox("Taqqoslash uchun ustun tanlang", df.columns)

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
                        similar_items.append(val)
                results.append({
                    "Kiritilgan": item,
                    "Mavjud": "Ha" if exact_match else "Yo'q",
                    "O'xshashlar": ", ".join(similar_items) if similar_items else "-"
                })

            result_df = pd.DataFrame(results)
            st.subheader("Natijalar")
            st.dataframe(result_df)

            # CSV yuklab olish
            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Natijani yuklab olish (.csv)", csv, "natijalar.csv", "text/csv")
