import math
import streamlit as st
import pandas as pd

# --- Structural Data (Standard SI Units: MPa, mm, N) ---
CONCRETE_DATA = {
    'B30': {'fcd': 13.0, 'fctm': 2.4}, 
    'B40': {'fcd': 17.4, 'fctm': 2.8}, 
    'B50': {'fcd': 21.7, 'fctm': 3.3}  
}

# Full Steel Table (As in cm2/m) - Diameters 8 to 20
STEEL_TABLE_CM2 = [
    # Phi 8
    {'phi': 8, 'spacing': 20, 'As': 2.51}, {'phi': 8, 'spacing': 17.5, 'As': 2.87},
    {'phi': 8, 'spacing': 15, 'As': 3.35}, {'phi': 8, 'spacing': 12.5, 'As': 4.02},
    {'phi': 8, 'spacing': 10, 'As': 5.03},
    # Phi 10
    {'phi': 10, 'spacing': 20, 'As': 3.93}, {'phi': 10, 'spacing': 17.5, 'As': 4.49},
    {'phi': 10, 'spacing': 15, 'As': 5.24}, {'phi': 10, 'spacing': 12.5, 'As': 6.28},
    {'phi': 10, 'spacing': 10, 'As': 7.85},
    # Phi 12
    {'phi': 12, 'spacing': 20, 'As': 5.65}, {'phi': 12, 'spacing': 17.5, 'As': 6.46},
    {'phi': 12, 'spacing': 15, 'As': 7.54}, {'phi': 12, 'spacing': 12.5, 'As': 9.05},
    {'phi': 12, 'spacing': 10, 'As': 11.31},
    # Phi 14
    {'phi': 14, 'spacing': 20, 'As': 7.70}, {'phi': 14, 'spacing': 17.5, 'As': 8.80},
    {'phi': 14, 'spacing': 15, 'As': 10.26}, {'phi': 14, 'spacing': 12.5, 'As': 12.32},
    {'phi': 14, 'spacing': 10, 'As': 15.39},
    # Phi 16
    {'phi': 16, 'spacing': 20, 'As': 10.05}, {'phi': 16, 'spacing': 17.5, 'As': 11.49},
    {'phi': 16, 'spacing': 15, 'As': 13.40}, {'phi': 16, 'spacing': 12.5, 'As': 16.08},
    {'phi': 16, 'spacing': 10, 'As': 20.11},
    # Phi 18
    {'phi': 18, 'spacing': 20, 'As': 12.72}, {'phi': 18, 'spacing': 17.5, 'As': 14.54},
    {'phi': 18, 'spacing': 15, 'As': 16.96}, {'phi': 18, 'spacing': 12.5, 'As': 20.36},
    {'phi': 18, 'spacing': 10, 'As': 25.45},
    # Phi 20
    {'phi': 20, 'spacing': 20, 'As': 15.71}, {'phi': 20, 'spacing': 17.5, 'As': 17.95},
    {'phi': 20, 'spacing': 15, 'As': 20.94}, {'phi': 20, 'spacing': 12.5, 'As': 25.13},
    {'phi': 20, 'spacing': 10, 'As': 31.42}
]

st.set_page_config(page_title="מחשבון זיון תקרות", layout="wide")
st.title("מחשבון שטח זיון לתקרה (SI Units)")

# יצירת עמודות לממשק משתמש נקי
col1, col2 = st.columns(2)

with col1:
    st.subheader("נתוני חתך ובטון")
    b_cm = st.number_input("רוחב b [ס״מ] (בדר״כ 100):", min_value=10.0, value=100.0, step=10.0)
    h_cm = st.number_input("עובי התקרה h [ס״מ]:", min_value=10.0, value=20.0, step=1.0)
    ds_cm = st.number_input("כיסוי בטון ds [ס״מ]:", min_value=1.0, value=3.0, step=0.5)
    c_type = st.selectbox("סוג בטון:", options=['B30', 'B40', 'B50'])

with col2:
    st.subheader("מומנטי תכן")
    md_input = st.text_input("הזן מומנטי תכן (Md) מופרדים בפסיקים [kNm/m]:", value="10, 15, 25")

st.markdown("---")

if st.button("חשב זיון", type="primary"):
    try:
        # עיבוד קלט המומנטים
        md_list = [float(m.strip()) for m in md_input.split(",") if m.strip()]
        
        if not md_list:
            st.warning("אנא הזן לפחות מומנט אחד.")
            st.stop()

        # קבועי החומרים
        fcd = CONCRETE_DATA[c_type]['fcd']
        fctm = CONCRETE_DATA[c_type]['fctm']
        fsd = 435  # עבור פלדה S500
        fsk = 500
        
        b_mm = b_cm * 10
        d_mm = (h_cm - ds_cm) * 10
        
        # חישוב זיון מינימלי
        as_min = max(0.28 * (fctm / fsk) * b_mm * d_mm, 0.0013 * b_mm * d_mm)
        
        st.info(f"**As_min (שטח זיון מינימלי):** {as_min:.1f} מ״מ²/מטר")
        
        results = []
        all_as_required = []
        errors = []

        # מעבר ראשון: חישוב שטח דרוש לכל מומנט
        for md in md_list:
            md_nmm = md * 10**6
            
            # בדיקת אזור לחוץ (אומגה)
            check_val = 1 - (2 * md_nmm) / (b_mm * d_mm**2 * fcd)
            if check_val < 0:
                errors.append(f"Md = {md}: המומנט גבוה מדי! נדרש זיון לחוץ.")
                continue
                
            omega = 1 - math.sqrt(check_val)
            if omega > 0.4:
                errors.append(f"Md = {md}: אומגה > 0.4! החתך מזוין יתר על המידה.")
                continue
                
            z = min(d_mm * (1 - omega / 2), 0.95 * d_mm)
            as_calc = md_nmm / (z * fsd)
            as_final = max(as_calc, as_min)
            
            results.append({'md': md, 'as_req': as_final})
            all_as_required.append(as_final)

        # הצגת שגיאות במידה ויש
        for err in errors:
            st.error(err)

        if not all_as_required:
            st.warning("לא חושבו נתונים תקינים. בדוק את הערכים שהזנת.")
            st.stop()

        # אופטימיזציה: מציאת "קוטר מוביל" למומנט המקסימלי
        max_as = max(all_as_required)
        lead_options = [row for row in STEEL_TABLE_CM2 if (row['As'] * 100) >= max_as]
        
        if not lead_options:
            st.error(f"שגיאה קריטית: שטח הזיון המקסימלי הנדרש ({max_as:.1f} mm²) חורג מגבולות הטבלה.")
            st.stop()

        lead_phi = min(lead_options, key=lambda x: x['As'])['phi']
        st.success(f"**קוטר מוביל שנבחר:** Φ{lead_phi}")

        # מעבר שני: בחירת ברזל מעשית
        final_table = []
        
        for res in results:
            matches = [row for row in STEEL_TABLE_CM2 if row['phi'] == lead_phi and (row['As'] * 100) >= res['as_req']]
            
            if matches:
                chosen = min(matches, key=lambda x: x['As'])
            else:
                chosen = min([row for row in STEEL_TABLE_CM2 if (row['As'] * 100) >= res['as_req']], key=lambda x: x['As'])
            
            final_table.append({
                "מומנט Md [kNm/m]": res['md'],
                "As דרוש [mm²/m]": round(res['as_req'], 1),
                "ברזל נבחר": f"Φ{chosen['phi']} @ {chosen['spacing']}",
                "As מסופק [mm²/m]": round(chosen['As'] * 100, 0)
            })

        # הצגת התוצאות בטבלה
        st.subheader("תוצאות סידור ברזל")
        df_results = pd.DataFrame(final_table)
        st.dataframe(df_results, use_container_width=True)

    except ValueError:
        st.error("שגיאת קלט: אנא ודא שהזנת מספרים תקינים בלבד בשדה המומנטים (מופרדים בפסיקים).")