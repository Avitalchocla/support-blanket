import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import os
from datetime import date
import io

# הגדרת דף רחב
st.set_page_config(page_title="שמיכת תמיכה", layout="wide")

# נתוני קטגוריות
CLUSTERS = {
    "קוגניטיבי לימודי שפתי": ["הישגים לימודיים", "יכולת מילולית הבעה והפשטה", "הבנה וחשיבה"],
    "עצמאות והתארגנות": ["למידה עצמאית", "תלמידאות ציוד התארגנות", "ניהול עצמי"],
    "תקשורתי": ["צורך בתיווך", "קשר עם הורים אחים", "קשר עם הסביבה"],
    "סנסו מוטורי": ["רגישות חושית", "מוטוריקה גסה ועדינה", "גרפו מוטורי"],
    "תפקוד חברתי": ["יוזמה חברתית ומקובלות", "הבנת סיטואציות חברתיות", "פיתרון דילמות חברתיות"],
    "תפקוד רגשי": ["ויסות רגשי", "לשתף ולהעזר באחר", "הכלת תסכול"]
}

# הגדרת תפקידים וצבעים (עם גרשיים לממשק)
VOTER_CONFIGS = {
    "יו\"ר": "#2c3e50", 
    "נ. פיקוח": "#FF0000", 
    "נ. רשות": "#8e44ad", 
    "נציג שפ\"ח": "#27ae60", 
    "נ. הורים": "#FF00FF"
}

if 'db' not in st.session_state: 
    st.session_state.db = {}

def draw_blanket(data_dict, chair_name="", v_date=None, student_name="", size=(5.4, 5.4)):
    bg_path = os.path.join(os.path.dirname(__name__), "blanket_base.png")
    if not os.path.exists(bg_path): return None
    
    img = Image.open(bg_path)
    w, h = img.size
    fig, ax = plt.subplots(figsize=size)
    ax.imshow(img)
    ax.axis('off')

    # פורמט תאריך ישראלי
    formatted_date = v_date.strftime("%d/%m/%Y") if v_date else ""
    
    # היפוך טקסט ותיקון גרשיים ורווחים
    rev_chair = chair_name[::-1]
    rev_student = student_name[::-1]
    
    # כותרת עם "יו"ר" מתוקן, רווח לפני הנקודתיים ותאריך
    title_text = f"{formatted_date}  |  {rev_chair}  \u200f: יו\"ר"
    if student_name:
        title_text = f"{rev_student}  :ה/דימלת  |  " + title_text
    
    ax.set_title(title_text, fontsize=10, pad=15, loc='center', fontweight='bold')

    center_x, center_y = (w / 2) - (w * 0.017), (h / 2) + (h * 0.010)
    max_r = h * 0.308
    
    def get_radius(val):
        mapping = {1: 0.52, 2: 0.69, 3: 0.84, 4: 1.0}
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

# --- ממשק משתמש עליון ---
col_role, col_info = st.columns([1, 2])
with col_info:
    c1, c2 = st.columns(2)
    chair_name_input = c1.text_input("שם היו\"ר:", value="אלעזר")
    v_date_input = c2.date_input("תאריך הוועדה:", value=date.today(), format="DD/MM/YYYY")

with col_role:
    role = st.selectbox("תפקיד נוכחי:", ["צופה", "יו\"ר", "נ. פיקוח", "נ. רשות", "נציג שפ\"ח", "נ. הורים"])

st.divider()

# סרגל צד עם מקרא וכפתור איפוס
with st.sidebar:
    st.markdown("### 🎨 מקרא צבעי הוועדה")
    for member, color in VOTER_CONFIGS.items():
        st.markdown(f"<span style='color:{color}; font-weight:bold;'>■</span> {member}", unsafe_allow_html=True)
    
    if role == "יו\"ר":
        st.write("---")
        if st.button("🗑️ איפוס לוח (לכל המשתתפים)"):
            st.session_state.db = {}
            st.rerun()

# --- לוגיקת הזנה ---
if role != "צופה":
    col_input, col_preview = st.columns([1.2, 2])
    with col_input:
        st.markdown(f"### ✍️ הזנה: {role}")
        current_values = []
        for name, params in CLUSTERS.items():
            with st.expander(name):
                for p in params:
                    val = st.select_slider(f"{p}:", options=[1, 2, 3, 4], key=f"{role}_{p}")
                    current_values.append(val)
        if st.button("🔄 עדכן בלוח המשותף", use_container_width=True):
            st.session_state.db[role] = current_values
            st.rerun()

    with col_preview:
        st.markdown("<center>🔍 תצוגה מקדימה אישית</center>", unsafe_allow_html=True)
        preview_fig = draw_blanket({role: current_values}, chair_name_input, v_date_input)
        if preview_fig: st.pyplot(preview_fig)

else: # מצב צופה
    if not st.session_state.db:
        st.info("💡 ממתין לעדכון נתונים מחברי הוועדה...")
    else:
        _, center_col, _ = st.columns([1, 2, 1])
        with center_col:
            st.markdown("<center><h2>📊 לוח הוועדה המשותף</h2></center>", unsafe_allow_html=True)
            main_fig = draw_blanket(st.session_state.db, chair_name_input, v_date_input)
            if main_fig: st.pyplot(main_fig)

# הצגת הלוח המשותף בתחתית למזינים
if role != "צופה" and st.session_state.db:
    st.divider()
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.markdown("<center><h3>📊 מבט על הלוח המשותף</h3></center>", unsafe_allow_html=True)
        main_fig = draw_blanket(st.session_state.db, chair_name_input, v_date_input)
        if main_fig: st.pyplot(main_fig)

# שמירה למחשב
if st.session_state.db:
    st.write("---")
    st.subheader("💾 שמירה למחשב האישי")
    student_name_input = st.text_input("הזן שם תלמיד (לשמירה מקומית בלבד):")
    if student_name_input:
        final_fig = draw_blanket(st.session_state.db, chair_name_input, v_date_input, student_name_input)
        buf = io.BytesIO()
        final_fig.savefig(buf, format="png", bbox_inches='tight')
        st.download_button(label="📥 הורד תמונת וועדה", data=buf.getvalue(), 
                         file_name=f"committee_{student_name_input}_{v_date_input.strftime('%d_%m_%Y')}.png", mime="image/png")
