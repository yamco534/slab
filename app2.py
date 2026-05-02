import math
import streamlit as st
import pandas as pd

# --- Structural Data ---
CONCRETE_DATA = {
    'B30': {'fcd': 13.0, 'fctm': 2.4}, 
    'B40': {'fcd': 17.4, 'fctm': 2.8}, 
    'B50': {'fcd': 21.7, 'fctm': 3.3}  
}

STEEL_TABLE_CM2 = [
    {'phi': 8, 'spacing': 20, 'As': 2.51}, {'phi': 8, 'spacing': 15, 'As': 3.35}, {'phi': 8, 'spacing': 10, 'As': 5.03},
    {'phi': 10, 'spacing': 20, 'As': 3.93}, {'phi': 10, 'spacing': 15, 'As': 5.24}, {'phi': 10, 'spacing': 10, 'As': 7.85},
    {'phi': 12, 'spacing': 20, 'As': 5.65}, {'phi': 12, 'spacing': 15, 'As': 7.54}, {'phi': 12, 'spacing': 10, 'As': 11.31},
    {'phi': 14, 'spacing': 20, 'As': 7.70}, {'phi': 14, 'spacing': 15, 'As': 10.26}, {'phi': 14, 'spacing': 10, 'As': 15.39},
]

st.set_page_config(page_title="מחשבון זיון תקרות משופר", layout="wide")
st.title("Yamco's calculator")

col1, col2 = st.columns(2)

with col1:
    st.subheader("נתוני חתך ובטון")
    b_cm = st.number_input("רוחב b [ס״מ]:", value=100.0)
    h_cm = st.number_input("עובי התקרה h [ס״מ]:", value=20.0)
    ds_cm = st.number_input("כיסוי ds [ס״מ]:", value=3.0)
    c_type = st.selectbox("סוג בטון:", options=['B30', 'B40', 'B50'])

with col2:
    st.subheader("מומנטי תכן")
    md_input = st.text_input("הזן מומנטים (Md) מופרדים בפסיקים:", value="15, 25, 35")

if st.button("חשב והצג תוצאות", type="primary"):
    try:
        md_list = [float(m.strip()) for m in md_input.split(",") if m.strip()]
        fcd, fctm = CONCRETE_DATA[c_type]['fcd'], CONCRETE_DATA[c_type]['fctm']
        fsd, fsk = 435, 500
        b_mm, d_mm = b_cm * 10, (h_cm - ds_cm) * 10
        as_min = max(0.28 * (fctm / fsk) * b_mm * d_mm, 0.0013 * b_mm * d_mm)
        
        final_data = []
        all_as = []

        for md in md_list:
            md_nmm = md * 10**6
            check_val = 1 - (2 * md_nmm) / (b_mm * d_mm**2 * fcd)
            
            if check_val < 0:
                final_data.append({"Md": md, "סטטוס": "שגיאה: נדרש זיון לחוץ", "w": "-", "z [mm]": "-"})
                continue
            
            omega = 1 - math.sqrt(check_val)
            z_mm = min(d_mm * (1 - omega / 2), 0.95 * d_mm)
            
            if omega > 0.4:
                final_data.append({"Md": md, "סטטוס": "שגיאה: אומגה > 0.4", "w": round(omega, 3), "z [mm]": round(z_mm, 1)})
                continue

            as_calc = md_nmm / (z_mm * fsd)
            as_final = max(as_calc, as_min)
            all_as.append(as_final)

            # בחירת ברזל (לפי הקוטר המוביל הפשוט ביותר לצורך הדוגמה)
            chosen = min([row for row in STEEL_TABLE_CM2 if (row['As'] * 100) >= as_final], key=lambda x: x['As'])
            # ... (בתוך הלופ של ה-md)
            final_data.append({
                "Md [kNm/m]": float(md),
                "w (אומגה)": round(omega, 4),
                "z [mm] (זרוע)": round(z_mm, 4),
                "As_calc [mm²/m]": round(as_final, 4),
                "סידור מוצע": f"Φ{chosen['phi']}@{chosen['spacing']}",
                "As_act [mm²/m]": round(chosen['As'] * 100, 4),
                "סטטוס": "תקין"
            })

        # יצירת ה-Dataframe
        df = pd.DataFrame(final_data)
        
        st.subheader("טבלת תוצאות מפורטת ")
        
        # תצוגה מעוצבת עם 4 ספרות אחרי הנקודה
        columns_to_format = ["w (אומגה)", "z [mm] (זרוע)", "As דרוש [mm²/m]", "As מסופק [mm²/m]"]
        st.dataframe(df.style.format({col: "{:.4f}" for col in columns_to_format if col in df.columns}), use_container_width=True)

        # ייצוא לאקסל ישמור כעת את הערכים כפי שהם ב-Dataframe (עם הדיוק של ה-round)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 הורד תוצאות לאקסל (CSV)",
            data=csv,
            file_name='slab_design_4_decimals.csv',
            mime='text/csv',
        )

    except Exception as e:
        st.error(f"שגיאה בחישוב: {e}")