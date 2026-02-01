import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import os
from datetime import date
import io
import time

# הגדרות תצוגה מקדימה ואיקון קבוע
st.set_page_config(
    page_title="מערכת שמיכת תמיכה - וועדות זכאות ואפיון",
    page_icon="https://raw.githubusercontent.com/Avitalchocla/support-blanket/main/favicon.png",
    layout="wide"
)

# פונקציה לחישוב ממוצע (מתעלמת מ-0)
def calculate_clean_average(values):
    relevant_vals = [v for v in values if v > 0]
    if not relevant_vals:
        return 0
    return round(sum(relevant_vals) / len(relevant_vals), 2)

# פונקציה להשמעת צליל עדכון
def play_success_chime():
    audio_url = "https://assets.mixkit.co/active_storage/sfx/2358/2358-preview.mp3"
    audio_html = f"""<audio autoplay><source src="{audio_url}" type="audio/mpeg"></audio>"""
    st.markdown(audio_html, unsafe_allow_html=True)

# אתחול רשימת יושבי ראש המלאה
if 'chair_list' not in st.session_state:
    st.session_state.chair_list = [
        "בחר שם מהרשימה", "אינה גמרמן ברון", "אליה טל", "אלעזר קצברוג", "ברכה גברא", 
        "גלית לוי", "דיאנה ג'קסון", "הילה ברון", "חני קיסוס", "טלי בארי מאיר", 
        "יעל איילון", "יעל פרידמן", "יפית שמואלי", "ליטל דגול", "לימור זרחיה", 
        "לילך ביטי", "מורן שחם", "מיכל זינגבויים", "מיכל ליפקין", "מיכל פרנקל", 
        "מירב אליה", "נטלי היקושלייר", "נסיה יוספי", "ענבל פרקש", "צביה טרוטנר", 
        "קרינה רבלין", "רולה עתילי", "שביט איוון בנעים", "שלומית שגיא", "שרית הראל כהן"
    ]

CLUSTERS = {
    "קוגניטיבי לימודי שפתי": ["הישגים לימודיים", "יכולת מילולית הבעה והפשטה", "הבנה וחשיבה"],
    "עצמאות והתארגנות": ["למידה עצמאית", "תלמידאות ציוד התארגנות", "ניהול עצמי"],
    "תקשורתי": ["צורך בתיווך", "קשר עם הורים אחים", "קשר עם הסביבה"],
    "סנסו מוטורי": ["רגישות חושית", "מוטוריקה גסה ועדינה", "גרפו מוטורי"],
    "תפקוד חברתי": ["יוזמה חברתית ומקובלות", "הבנת סיטואציות חברתיות", "פיתרון דילמות חברתיות"],
    "תפקוד רגשי": ["ויסות רגשי", "לשתף ולהעזר באחר", "הכלת תסכול"]
}

VOTER_CONFIGS = {
    "יו\"ר": "#2c3e50", "נ. פיקוח": "#FF0000", "נ. רשות": "#8e44ad", "נציג שפ\"ח": "#27ae60", "נ. הורים": "#FF00FF"
}

if 'db' not in st.session_state: 
    st.session_state.db = {}

if 'show_averages_to_viewer' not in st.session_state:
    st.session_state.show_averages_to_viewer = {}

def draw_blanket(data_dict, chair_name="", v_date=None, student_name="", size=(5.4, 5.4)):
    bg_path = os.path.join(os.path.dirname(__file__), "blanket_base.png")
    if not os.path.exists(bg_path): return None
    img = Image.open(bg_path)
    w, h = img.size
    fig, ax = plt.subplots(figsize=size)
    ax.imshow(img)
    ax.axis('off')

    formatted_date = v_date.strftime("%d/%m/%Y") if v_date else ""
    title_text = f"{formatted_date}  |  {chair_name[::-1]}  : ר\"וי"
    if student_name:
        title_text = f"{student_name[::-1]}  :ה/דימלת  |  " + title_text
    
    ax.set_title(title_text, fontsize=10, pad=15, loc='center', fontweight='bold')

    center_x, center_y = (w / 2) - (w * 0.017), (h / 2) + (h * 0.010)
    max_r = h * 0.308
    
    def get_radius(val):
        mapping = {0: 0.0, 1: 0.52, 2: 0.69, 3: 0.84, 4: 1.0}
        return mapping.get(val, 0) * max_r

    num_vars = 18
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False) - np.pi/2 - (np.pi/9)

    for name, values in data_dict.items():
        radii = np.array([get_radius(v) for v in values])
        x = center_x + radii * np.cos(angles)
        y = center_y + radii * np.sin(angles)
        x = np.append(x, x[0]); y = np.append(y, y[0])
        ax.fill(x, y, color=VOTER_CONFIGS.get(name, "#333"), alpha=0.3, label=name[::-1])
        ax.plot(x, y, color=VOTER_CONFIGS.get(name, "#333"), linewidth=2, marker='o', markersize=3)
    
    if data_dict:
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=3, fontsize=8)
    return fig

# --- ממשק משתמש ---
col_role, col_info = st.columns([1, 2])
with col_info:
    c1, c2 = st.columns(2)
    chair_name_input = c1.selectbox("שם היו\"ר:", options=st.session_state.chair_list)
    v_date_input = c2.date_input("תאריך הוועדה:", value=date.today(), format="DD/MM/YYYY")

with col_role:
    role = st.selectbox("תפקיד נוכחי:", ["צופה", "יו\"ר", "נ. פיקוח", "נ. רשות", "נציג שפ\"ח", "נ. הורים"])

if chair_name_input == "בחר שם מהרשימה":
    st.warning("⚠️ אנא בחר את שם היו\"ר כדי להמשיך.")
    st.stop()

if chair_name_input not in st.session_state.db:
    st.session_state.db[chair_name_input] = {}
    st.session_state.show_averages_to_viewer[chair_name_input] = False

current_committee_db = st.session_state.db[chair_name_input]

st.divider()

if role != "צופה":
    col_input, col_preview = st.columns([1.2, 2])
    with col_input:
        st.markdown(f"### ✍️ הזנה: {role}")
        current_values = []
        for name, params in CLUSTERS.items():
            with st.expander(name):
                for p in params:
                    val = st.radio(f"**{p}:**", options=[0, 1, 2, 3, 4], index=0, horizontal=True, key=f"{role}_{chair_name_input}_{p}")
                    current_values.append(val)
        
        my_avg = calculate_clean_average(current_values)
        st.info(f"📊 הממוצע שלך: **{my_avg}**")
        
        if st.button("🔄 עדכן בלוח המשותף", use_container_width=True):
            st.session_state.db[chair_name_input][role] = current_values
            play_success_chime()
            st.rerun()

        if role == "יו\"ר":
            st.markdown("---")
            st.subheader("📊 סיכום ממוצעים (ליו\"ר)")
            all_avgs = []
            for member, vals in current_committee_db.items():
                m_avg = calculate_clean_average(vals)
                st.write(f"**{member}:** {m_avg}")
                all_avgs.append(m_avg)
            
            if all_avgs:
                total_weighted_avg = round(sum(all_avgs)/len(all_avgs), 2)
                st.markdown(f"### 🎯 ממוצע משוקלל של כולם: `{total_weighted_avg}`")
                
                label = "הסתר ממוצעים מהצופה" if st.session_state.show_averages_to_viewer[chair_name_input] else "הצג ממוצעים לצופה"
                if st.button(label):
                    st.session_state.show_averages_to_viewer[chair_name_input] = not st.session_state.show_averages_to_viewer[chair_name_input]
                    st.rerun()

    with col_preview:
        preview_fig = draw_blanket({role: current_values}, chair_name_input, v_date_input)
        if preview_fig: st.pyplot(preview_fig)

else: # מצב צופה
    st.markdown(f"<center><h2>📊 לוח משותף: {chair_name_input}</h2></center>", unsafe_allow_html=True)
    _, center_col, _ = st.columns([1, 3, 1])
    with center_col:
        main_fig = draw_blanket(current_committee_db, chair_name_input, v_date_input)
        if main_fig: st.pyplot(main_fig)
        
        # תצוגת ממוצעים לצופה (רק באישור יו"ר)
        if st.session_state.show_averages_to_viewer.get(chair_name_input, False) and current_committee_db:
            st.write("---")
            all_voter_avgs = [calculate_clean_average(v) for v in current_committee_db.values()]
            
            # יצירת שורת מטריקות
            m_cols = st.columns(len(current_committee_db) + 1)
            for i, (member, vals) in enumerate(current_committee_db.items()):
                m_cols[i].metric(member, calculate_clean_average(vals))
            
            # הממוצע המשוקלל בסוף השורה
            if all_voter_avgs:
                final_avg = round(sum(all_voter_avgs)/len(all_voter_avgs), 2)
                m_cols[-1].metric("🌟 ממוצע משוקלל", final_avg)

# שמירה
if current_committee_db:
    st.write("---")
    student_name_input = st.text_input("הזן שם תלמיד לשמירה:")
    if student_name_input:
        final_fig = draw_blanket(current_committee_db, chair_name_input, v_date_input, student_name_input)
        buf = io.BytesIO()
        final_fig.savefig(buf, format="png", bbox_inches='tight')
        st.download_button(label="📥 הורד תמונת וועדה", data=buf.getvalue(), file_name=f"{student_name_input}.png", mime="image/png")
