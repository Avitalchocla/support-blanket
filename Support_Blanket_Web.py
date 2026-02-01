import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import os
from datetime import date
import io
import time

# הגדרות תצוגה
st.set_page_config(
    page_title="מערכת שמיכת תמיכה - וועדות זכאות ואפיון",
    page_icon="🛡️",
    layout="wide"
)

# --- פונקציות עזר ---

def calculate_clean_average(values):
    """חישוב ממוצע רק למספרים הגדולים מ-0"""
    relevant_vals = [v for v in values if v > 0]
    if not relevant_vals:
        return 0
    return round(sum(relevant_vals) / len(relevant_vals), 2)

@st.cache_data
def load_base_image(path):
    if os.path.exists(path):
        return Image.open(path)
    return None

# --- אתחול Session State ---
if 'chair_list' not in st.session_state:
    st.session_state.chair_list = ["בחר שם מהרשימה", "אינה גמרמן ברון", "אליה טל", "גלית לוי"]

if 'db' not in st.session_state: 
    st.session_state.db = {}

# משתנה לשליטה האם להציג ממוצעים לצופה
if 'show_averages_to_viewer' not in st.session_state:
    st.session_state.show_averages_to_viewer = {}

# --- נתונים קבועים ---
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

# --- פונקציית הציור ---
def draw_blanket(data_dict, chair_name="", v_date=None, student_name="", size=(5.4, 5.4)):
    bg_path = os.path.join(os.path.dirname(__file__), "blanket_base.png")
    img = load_base_image(bg_path)
    
    fig, ax = plt.subplots(figsize=size)
    if img:
        ax.imshow(img)
    ax.axis('off')

    def rev(s): return s[::-1]

    formatted_date = v_date.strftime("%d/%m/%Y") if v_date else ""
    title_text = f"{formatted_date}  |  {rev(chair_name)}  : ר\"וי"
    if student_name:
        title_text = f"{rev(student_name)}  :ה/דימלת  |  " + title_text
    
    ax.set_title(title_text, fontsize=10, pad=15, fontweight='bold')

    # קואורדינטות המרכז (לפי הקוד המקורי שלך)
    w, h = (1000, 1000) if not img else img.size
    center_x, center_y = (w / 2) - (w * 0.017), (h / 2) + (h * 0.010)
    max_r = h * 0.308
    
    def get_radius(val):
        # 0 נמצא במרכז (רדיוס 0), 1-4 נשארים במיקום המקורי שלהם
        mapping = {0: 0.0, 1: 0.52, 2: 0.69, 3: 0.84, 4: 1.0}
        return mapping.get(val, 0) * max_r

    num_vars = 18
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False) - np.pi/2 - (np.pi/9)

    for name, values in data_dict.items():
        radii = np.array([get_radius(v) for v in values])
        x = center_x + radii * np.cos(angles)
        y = center_y + radii * np.sin(angles)
        x = np.append(x, x[0]); y = np.append(y, y[0])
        ax.fill(x, y, color=VOTER_CONFIGS.get(name, "#333"), alpha=0.3, label=rev(name))
        ax.plot(x, y, color=VOTER_CONFIGS.get(name, "#333"), linewidth=2, marker='o', markersize=3)
    
    if data_dict:
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=3, fontsize=8)
    return fig

# --- ממשק משתמש ---

col_role, col_info = st.columns([1, 2])
with col_info:
    c1, c2 = st.columns(2)
    chair_name_input = c1.selectbox("שם היו\"ר:", options=st.session_state.chair_list)
    v_date_input = c2.date_input("תאריך הוועדה:", value=date.today())

with col_role:
    role = st.selectbox("תפקיד נוכחי:", ["צופה", "יו\"ר", "נ. פיקוח", "נ. רשות", "נציג שפ\"ח", "נ. הורים"])

if chair_name_input == "בחר שם מהרשימה":
    st.warning("⚠️ אנא בחר את שם היו\"ר כדי להמשיך.")
    st.stop()

# יצירת מסד נתונים לוועדה הספציפית
if chair_name_input not in st.session_state.db:
    st.session_state.db[chair_name_input] = {}
    st.session_state.show_averages_to_viewer[chair_name_input] = False

current_committee_db = st.session_state.db[chair_name_input]

st.divider()

# --- צד המזין (חברי וועדה ויו"ר) ---
if role != "צופה":
    col_input, col_preview = st.columns([1.2, 2])
    with col_input:
        st.markdown(f"### ✍️ הזנה: {role}")
        current_values = []
        for name, params in CLUSTERS.items():
            with st.expander(name):
                for p in params:
                    # ברירת מחדל היא 0
                    val = st.radio(f"**{p}:**", options=[0, 1, 2, 3, 4], index=0, horizontal=True, key=f"{role}_{chair_name_input}_{p}")
                    current_values.append(val)
        
        # חישוב ממוצע אישי
        my_avg = calculate_clean_average(current_values)
        st.info(f"📊 הממוצע האישי שלך (ללא אפסים): **{my_avg}**")
        
        if st.button("🔄 עדכן בלוח המשותף", use_container_width=True):
            st.session_state.db[chair_name_input][role] = current_values
            st.toast("עודכן!")
            time.sleep(0.5)
            st.rerun()

        # תפריט מיוחד ליו"ר
        if role == "יו\"ר":
            st.markdown("---")
            st.subheader("🛠️ ניהול יו\"ר")
            
            # הצגת ממוצעים ליו"ר
            st.write("**ממוצעי חברים:**")
            all_averages = []
            for member, vals in current_committee_db.items():
                m_avg = calculate_clean_average(vals)
                st.write(f"{member}: {m_avg}")
                all_averages.append(m_avg)
            
            if all_averages:
                total_avg = round(sum(all_averages) / len(all_averages), 2)
                st.write(f"**ממוצע כולל: {total_avg}**")
                
                # כפתור שליטה לצופה
                label = "הסתר ממוצעים מהצופה" if st.session_state.show_averages_to_viewer[chair_name_input] else "הצג ממוצעים לצופה"
                if st.button(label):
                    st.session_state.show_averages_to_viewer[chair_name_input] = not st.session_state.show_averages_to_viewer[chair_name_input]
                    st.rerun()

    with col_preview:
        st.pyplot(draw_blanket({role: current_values}, chair_name_input, v_date_input))

# --- צד הצופה (המקרן) ---
else:
    if not current_committee_db:
        st.info(f"ממתין לנתונים...")
    else:
        st.markdown(f"<center><h2>📊 לוח משותף: {chair_name_input}</h2></center>", unsafe_allow_html=True)
        fig = draw_blanket(current_committee_db, chair_name_input, v_date_input)
        st.pyplot(fig)
        
        # הצגת ממוצעים רק אם היו"ר אישר
        if st.session_state.show_averages_to_viewer.get(chair_name_input, False):
            st.divider()
            cols = st.columns(len(current_committee_db) + 1)
            all_avgs = []
            for i, (member, vals) in enumerate(current_committee_db.items()):
                m_avg = calculate_clean_average(vals)
                cols[i].metric(member, m_avg)
                all_avgs.append(m_avg)
            
            if all_avgs:
                gen_avg = round(sum(all_avgs) / len(all_avgs), 2)
                cols[-1].metric("ממוצע כולל", gen_avg, delta_color="off")

# אפשרות הוספת יו"ר חדש
with st.expander("➕ הוספת יו\"ר חדש"):
    new_name = st.text_input("שם מלא:")
    if st.button("הוסף"):
        if new_name and new_name not in st.session_state.chair_list:
            st.session_state.chair_list.append(new_name)
            st.rerun()
