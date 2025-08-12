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
    s = " ".join(s.split())  # ortiqcha probellarni bitta qilish
    return s

st.title("📊 Ma'lumotlarni Taqqoslash Platformasi (Demo)")

# 1️⃣ Ma'lumotlar bazasini yuklash
st.subheader("1️⃣ Ma'lumotlar bazasini yuklang (.xlsx yoki .csv)")
uploaded_db = st.file_uploader("Bazani yuklash", type=["xlsx", "csv"])

# 2️⃣ Tekshiriladigan ma'lumotlarni yuklash yoki kiritish
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
        # Vergul va yangi qator orqali ajratish
        items = [x.strip() for x in raw_text.replace("\n", ",").split(",") if x.strip()]
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

        # Taqqoslash uchun ustun tanlash (asosiy ustun)
        column_to_check = st.selectbox("Bazadagi taqqoslanadigan ustunni tanlang", df.columns)

        # Tekshiriladigan fayldan ustun tanlash
        input_column_to_check = st.selectbox("Tekshiriladigan fayldagi ustunni tanlang", input_data.columns)

        # Qo'shimcha ustunlarni tanlash
        extra_columns = st.multiselect("Natijada ko'rsatish uchun qo'shimcha ustunlar", 
                                       [col for col in df.columns if col != column_to_check])

        if st.button("Taqqoslash"):
            # Normallashtirish
            df["__norm_col__"] = df[column_to_check].apply(normalize_text)
            input_data["__norm_input__"] = input_data[input_column_to_check].apply(normalize_text)

            results = []
            for item in input_data["__norm_input__"]:
                exact_match = item in df["__norm_col__"].values
                similar_items = []
                for val in df["__norm_col__"].unique():
                    if fuzz.ratio(item, val) >= 80 and val != item:
                        similar_items.append(val)

                # ✅ Barcha mos kelgan qatorlarni olish
                match_rows = df[df["__norm_col__"] == item] if exact_match else pd.DataFrame()

                # Har bir qo'shimcha ustun uchun barcha qiymatlarni vergul bilan birlashtirish
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

            # CSV yuklab olish
            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Natijani yuklab olish (.csv)", csv, "natijalar.csv", "text/csv")
