import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import os
from datetime import date
import io
import time

st.set_page_config(page_title="שמיכת תמיכה", layout="wide")

# פונקציה להשמעת צליל גונג
def play_gong():
    audio_html = """
        <audio autoplay>
            <source src="https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3" type="audio/mpeg">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

# אתחול רשימת יושבי ראש בזיכרון
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

def draw_blanket(data_dict, chair_name="", v_date=None, student_name="", size=(5.4, 5.4)):
    bg_path = os.path.join(os.path.dirname(__file__), "blanket_base.png")
    if not os.path.exists(bg_path): return None
    
    img = Image.open(bg_path)
    w, h = img.size
    fig, ax = plt.subplots(figsize=size)
    ax.imshow(img)
    ax.axis('off')

    formatted_date = v_date.strftime("%d/%m/%Y") if v_date else ""
    rev_chair = chair_name[::-1]
    rev_student = student_name[::-1]
    title_text = f"{formatted_date}  |  {rev_chair}  :\"ר'וי"
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
with st.expander("📖 מדריך מקוצר למשתמש"):
    st.markdown("""
    ### ברוכים הבאים למערכת 'שמיכת תמיכה'
    המערכת מאפשרת בנייה משותפת של פרופיל התלמיד בזמן אמת.
    
    **איך זה עובד?**
    1. **בחירת יו"ר:** בראש ובראשונה, כולם (גם הצופה וגם המזינים) צריכים לבחור את **אותו שם יו"ר** מהרשימה. זה ה"חדר" המשותף שלכם.
    2. **צופה:** המחשב המחובר למקרן צריך להיות במצב "צופה". הוא יציג את התמונה המשולבת של כולם.
    3. **חברי וועדה:** נכנסים מהסמארטפון, בוחרים את תפקידם ומזינים את הערכים.
    4. **עדכון:** לחיצה על 'עדכן בלוח המשותף' תשמיע גונג ותשלח את הנתונים למסך הראשי.
    5. **שמירה:** בסיום הדיון, ניתן להוריד את התמונה הסופית למחשב לצורך תיעוד.
    """)

col_role, col_info = st.columns([1, 2])
with col_info:
    c1, c2 = st.columns(2)
    chair_name_input = c1.selectbox("שם היו\"ר:", options=st.session_state.chair_list)
    v_date_input = c2.date_input("תאריך הוועדה:", value=date.today(), format="DD/MM/YYYY")

with col_role:
    role = st.selectbox("תפקיד נוכחי:", ["צופה", "יו\"ר", "נ. פיקוח", "נ. רשות", "נציג שפ\"ח", "נ. הורים"])

# אפשרות להוספת יו"ר חדש
with st.expander("➕ הוספת יו\"ר חדש לרשימה"):
    new_name = st.text_input("הקלד שם מלא:")
    if st.button("הוסף לרשימה"):
        if new_name and new_name not in st.session_state.chair_list:
            st.session_state.chair_list.append(new_name)
            st.success(f"השם {new_name} נוסף! בחר אותו כעת מהרשימה למעלה.")
            st.rerun()

if chair_name_input == "בחר שם מהרשימה":
    st.warning("⚠️ אנא בחר את שם היו\"ר כדי להמשיך.")
    st.stop()

if chair_name_input not in st.session_state.db:
    st.session_state.db[chair_name_input] = {}

current_committee_db = st.session_state.db[chair_name_input]

st.divider()

with st.sidebar:
    st.markdown(f"### 📋 וועדה של: \n**{chair_name_input}**")
    st.write("---")
    st.markdown("### 🎨 מקרא צבעים")
    for member, color in VOTER_CONFIGS.items():
        st.markdown(f"<span style='color:{color}; font-weight:bold;'>■</span> {member}", unsafe_allow_html=True)
    if role == "יו\"ר":
        st.write("---")
        if st.button("🗑️ איפוס לוח לוועדה זו"):
            st.session_state.db[chair_name_input] = {}
            st.rerun()

if role != "צופה":
    col_input, col_preview = st.columns([1.2, 2])
    with col_input:
        st.markdown(f"### ✍️ הזנה: {role}")
        current_values = []
        for name, params in CLUSTERS.items():
            with st.expander(name):
                for p in params:
                    val = st.select_slider(f"{p}:", options=[1, 2, 3, 4], key=f"{role}_{chair_name_input}_{p}")
                    current_values.append(val)
        
        if st.button("🔄 עדכן בלוח המשותף", use_container_width=True):
            st.session_state.db[chair_name_input][role] = current_values
            play_gong()
            st.toast(f"הנתונים נשלחו ללוח של {chair_name_input}!", icon="✅")
            time.sleep(1.5)
            st.rerun()

    with col_preview:
        st.markdown("<center>🔍 תצוגה מקדימה אישית</center>", unsafe_allow_html=True)
        preview_fig = draw_blanket({role: current_values}, chair_name_input, v_date_input)
        if preview_fig: st.pyplot(preview_fig)

else: # מצב צופה
    if not current_committee_db:
        st.info(f"💡 ממתין לעדכון נתונים עבור הוועדה של **{chair_name_input}**...")
    else:
        _, center_col, _ = st.columns([1, 2, 1])
        with center_col:
            st.markdown(f"<center><h2>📊 לוח משותף: {chair_name_input}</h2></center>", unsafe_allow_html=True)
            main_fig = draw_blanket(current_committee_db, chair_name_input, v_date_input)
            if main_fig: st.pyplot(main_fig)

if role != "צופה" and current_committee_db:
    st.divider()
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        main_fig = draw_blanket(current_committee_db, chair_name_input, v_date_input)
        if main_fig: st.pyplot(main_fig)

if current_committee_db:
    st.write("---")
    st.subheader("💾 שמירה למחשב האישי")
    student_name_input = st.text_input("הזן שם תלמיד (לשמירה מקומית בלבד):")
    if student_name_input:
        final_fig = draw_blanket(current_committee_db, chair_name_input, v_date_input, student_name_input)
        buf = io.BytesIO()
        final_fig.savefig(buf, format="png", bbox_inches='tight')
        st.download_button(label="📥 הורד תמונת וועדה", data=buf.getvalue(), 
                         file_name=f"committee_{student_name_input}_{v_date_input.strftime('%d_%m_%Y')}.png", mime="image/png")
