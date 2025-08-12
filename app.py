import streamlit as st
import pandas as pd
import re
from io import BytesIO
from thefuzz import process

# --- Matnni normallashtirish funksiyasi ---
def normalize_text(s):
    if not isinstance(s, str):
        return s
    # Ortiqcha probellarni olib tashlash
    s = re.sub(r"\s+", "", s)
    # Katta-kichik harflarni birxillashtirish
    s = s.lower()
    # O‘ = O’, G‘ = G’ birxillashtirish
    s = s.replace("o’", "o'").replace("o‘", "o'") \
         .replace("g’", "g'").replace("g‘", "g'")
    return s

# --- Streamlit sarlavha ---
st.title("📊 Ma'lumotlarni taqqoslash platformasi")

# --- Ma'lumotlar bazasini yuklash ---
uploaded_file = st.file_uploader("Ma'lumotlar bazasini yuklang (Excel yoki CSV)", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)

    st.write("📄 Yuklangan ma'lumotlar bazasi:")
    st.dataframe(df)

    # --- Taqqoslash ustunini tanlash ---
    compare_column = st.selectbox("Taqqoslash uchun ustunni tanlang", df.columns)

    # --- Tekshiriladigan ma'lumotlarni kiritish ---
    input_data = st.text_area(
        "Tekshiriladigan ma'lumotlarni kiriting (vergul bilan yoki qatorma-qator)",
        placeholder="Misol: Lola, Anvar, Dilshod yoki\nLola\nAnvar\nDilshod"
    )

    if st.button("🔍 Taqqoslash"):
        if input_data.strip():
            # --- Kirilgan ma'lumotlarni ajratish ---
            check_values = re.split(r",|\n", input_data)
            check_values = [normalize_text(v) for v in check_values if v.strip()]

            # --- Bazani normallashtirish ---
            df[compare_column + "_norm"] = df[compare_column].apply(normalize_text)

            # --- Aniqlik bo'yicha tekshirish ---
            df["Mavjud"] = df[compare_column + "_norm"].isin(check_values)

            # --- O'xshashlik bo'yicha tekshirish ---
            norm_values_list = df[compare_column + "_norm"].dropna().unique().tolist()

            closest_matches = []
            match_scores = []
            for val in check_values:
                match, score = process.extractOne(val, norm_values_list)
                closest_matches.append(match)
                match_scores.append(score)

            # --- Natija jadvali ---
            result_df = pd.DataFrame({
                "Kiritilgan ma'lumot": check_values,
                "O'xshash topildi": closest_matches,
                "O'xshashlik foizi": match_scores
            })

            st.write("📊 Taqqoslash natijasi:")
            st.dataframe(result_df)

            # --- CSV yuklab olish ---
            output = BytesIO()
            result_df.to_csv(output, index=False)
            st.download_button("📥 Natijani yuklab olish (CSV)", data=output.getvalue(), file_name="natija.csv", mime="text/csv")

        else:
            st.warning("Iltimos, tekshiriladigan ma'lumotlarni kiriting.")
