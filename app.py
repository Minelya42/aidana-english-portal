from groq import Groq
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import re
import json
from datetime import datetime

# --- API SETUP ---
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    # Это для локального запуска, если нет файла secrets.toml
    api_key = "" 

client = Groq(api_key=api_key)
def get_ai_recommendation(student_name, stats, history_df):
    h_text = history_df.to_string(index=False) if history_df is not None and not history_df.empty else "No previous data available."

    prompt = f"""
    You are an expert English Language Mentor with a PhD in Linguistics. 
    Analyze the performance of student: {student_name}.
    
    Current Performance Data:
    - Speaking: {stats['leadership']}/100
    - Listening: {stats['discipline']}/100
    - Grammar: {stats['knowledge']}/100
    
    Student History (Past results):
    {h_text}
    
    Task: Write a detailed, professional, and deep pedagogical analysis. 
    Language: English.
    
    Structure your JSON response strictly with these 3 keys:
    1. "pros": Write a detailed paragraph (4-6 sentences). Compare current stats with history. Mention specific improvements in their skills and congratulate them on their dedication.
    2. "growth": Provide a comprehensive learning strategy. Recommend exactly 2 specific YouTube channels and 1 book/article title. Explain WHY these resources will help based on their current scores. (5-7 sentences).
    3. "errors": Identify the biggest technical gaps. Be specific (e.g., "Mixed Conditionals" or "Active Listening phoneme recognition"). Provide a 3-step exercise they can do today to fix it. (5-7 sentences).

    Requirement: Avoid generic advice. Be deep, academic, yet encouraging.
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return None
    
# --- DATABASE ---
DB_NAME = "baysard_final.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (id INTEGER PRIMARY KEY, name TEXT UNIQUE, xp INTEGER, level INTEGER,
                  leadership INTEGER, discipline INTEGER, knowledge INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY, date TEXT, name TEXT, xp INTEGER, type TEXT, month TEXT)''')
    conn.commit()
    conn.close()

def run_query(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()

def get_df(query, params=None):
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query(query, conn, params=params if params is not None else ())

init_db()

# --- STYLES ---
st.markdown("""
    <style>
    .stApp { background-color: #EDE9DF; }

    /* Премиум стили для AI карточек */
    .ai-card {
        padding: 24px;
        border-radius: 20px;
        margin-bottom: 5px;
        color: #1a1c19 !important;
        border-left: 10px solid;
        background: #ffffff;
        box-shadow: 0 8px 20px rgba(0,0,0,0.06);
        /* Фиксированная высота для превью */
        height: 220px; 
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }

    .card-title {
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 12px;
        font-size: 1rem;
        display: flex;
        align-items: center;
        color: #283123;
    }

    .card-green { background-color: #f0fdf4; border-color: #22c55e; }
    .card-yellow { background-color: #fffbeb; border-color: #f59e0b; }
    .card-red { background-color: #fef2f2; border-color: #ef4444; }

    /* Стилизация экспандера (кнопки подробнее) */
    .stExpander {
        border: none !important;
        background: white !important;
        border-radius: 0 0 20px 20px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03) !important;
        margin-bottom: 20px !important;
    }

    /* Вкладки и метрики */
    .stTabs [data-baseweb="tab"] {
        flex: 1; height: 60px;
        background: linear-gradient(135deg, #883322 0%, #283123 100%);
        color: #EDE9DF; font-weight: 600; text-transform: uppercase;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #F0944D 0%, #EACFA3 100%) !important;
        color: #283123 !important;
    }
    div[data-testid="stMetric"] {
        background-color: #883322; border: 2px solid #283123; border-radius: 15px; padding: 15px;
    }
    div[data-testid="stMetricValue"] { color: #EACFA3 !important; }
    .rank-card {
        background: linear-gradient(135deg, #883322 0%, #F0944D 100%);
        padding: 25px; border-radius: 20px; color: #EDE9DF; text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- AUTH ---
if 'role' not in st.session_state: st.session_state.role = None
if st.session_state.role is None:
    st.markdown("<h1 style='text-align: center; color: #883322;'>🛡️ ENGLISH PROFICIENCY PORTAL</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 STUDENT ACCESS", use_container_width=True):
            st.session_state.role = "student"; st.rerun()
    with col2:
        pwd = st.text_input("Teacher Password", type="password")
        if st.button("🔓 TEACHER LOGIN", use_container_width=True):
            if pwd == "1234": st.session_state.role = "admin"; st.rerun()
            else: st.error("Access Denied")
    st.stop()

# --- APP ---
with st.sidebar:
    if st.session_state.role == "admin":
        st.markdown(f"""
            <div style="background-color: #283123; padding: 20px; border-radius: 15px; border: 1px solid #F0944D; margin-bottom: 20px;">
                <h3 style="color: #EDE9DF; margin: 0;">👋 Hello,Miss Aidana!</h3>
                <p style="color: #EACFA3; font-size: 0.8rem; margin-top: 5px;">Welcome to your Dashboard</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"### 👤 Student Mode")
        st.info(f"Viewing: **{st.session_state.get('last_selected_student', 'User')}**")
    
    if st.button("🚪 Logout", use_container_width=True): 
        st.session_state.role = None
        st.rerun()

tabs = st.tabs(["🏆 TOP CHART", "👤 MY SKILLS", "📈 HISTORY", "👨‍🏫 CONTROL", "⚙️ DB"] if st.session_state.role == "admin" else ["🏆 TOP CHART", "👤 MY SKILLS", "📈 HISTORY"])

with tabs[0]:
    st.markdown("<h2 style='color: #883322;'>🏆 World Ranking</h2>", unsafe_allow_html=True)
    df_ranking = get_df("SELECT name as 'Student Name', xp as 'EXP', level as 'LVL' FROM students ORDER BY xp DESC")
    st.dataframe(df_ranking, use_container_width=True)

with tabs[1]:
    fresh_sts = get_df("SELECT * FROM students")
    if not fresh_sts.empty:
        sel_name = st.selectbox("Choose Student Name", fresh_sts['name'].tolist())
        
        # --- СБРОС КЕША ПРИ СМЕНЕ СТУДЕНТА ---
        # Если выбрали другого студента, удаляем старый совет из памяти, чтобы он не висел
        if "last_selected_student" not in st.session_state:
            st.session_state.last_selected_student = sel_name
        
        if st.session_state.last_selected_student != sel_name:
            st.session_state.last_selected_student = sel_name
            if f"ai_advice_{sel_name}" in st.session_state:
                del st.session_state[f"ai_advice_{sel_name}"]

        u = fresh_sts[fresh_sts['name'] == sel_name].iloc[0]
        st.markdown(f"<h2 style='text-align: center;'>Status Report: {sel_name}</h2>", unsafe_allow_html=True)
        
        # --- RADAR & RANK ---
        c_radar, c_rank = st.columns([3, 2])
        with c_radar:
            fig = go.Figure(data=go.Scatterpolar(
                r=[u['leadership'], u['discipline'], u['knowledge']],
                theta=['Speaking', 'Listening', 'Grammar'],
                fill='toself', line=dict(color='#283123', width=3),
                fillcolor='rgba(40, 49, 35, 0.2)'
            ))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        
        with c_rank:
            xp_val = u['xp']
            rank_name = "A1: ELEMENTARY" if xp_val < 1000 else "A2: PRE-INTER" if xp_val < 2000 else "B1: INTERMEDIATE" if xp_val < 3000 else "B2: UPPER-INTER" if xp_val < 6000 else "C2: THE NATIVE"
            st.markdown(f'<div class="rank-card"><p style="font-size:10px; opacity:0.8;">OFFICIAL RANK</p><h1>{rank_name}</h1></div>', unsafe_allow_html=True)
            st.write("")
            m1, m2 = st.columns(2)
            m1.metric("**LVL**", u['level'])
            m2.metric("**Total XP**", xp_val)

        st.divider()
        st.subheader("🤖 Personal AI Tutor")
        
        cb1, cb2 = st.columns([1, 4])
        gen_btn = cb1.button("✨ Generate", key="ai_gen")
        
        if cb2.button("🔄 Refresh AI", key="ai_ref"):
            if f"ai_advice_{sel_name}" in st.session_state:
                del st.session_state[f"ai_advice_{sel_name}"]
            st.rerun()

        # --- ЛОГИКА ГЕНЕРАЦИИ ---
        if gen_btn:
            with st.spinner('AI is thinking...'):
                student_history = get_df("SELECT date, xp, type FROM history WHERE name=? ORDER BY date DESC LIMIT 5", (sel_name,))
                current_stats = {'leadership': u['leadership'], 'discipline': u['discipline'], 'knowledge': u['knowledge']}
                res = get_ai_recommendation(sel_name, current_stats, student_history)
                if res:
                    st.session_state[f"ai_advice_{sel_name}"] = res
                    st.rerun() # ПРИНУДИТЕЛЬНО ОБНОВЛЯЕМ, ЧТОБЫ УБРАТЬ "ANALYZING"

        # --- ВЫВОД КАРТОЧЕК ---
        advice = st.session_state.get(f"ai_advice_{sel_name}")

        if advice and isinstance(advice, dict):
            cols = st.columns(3)
            # Используем .get() с нормальным дефолтным текстом
            data = [
                ("✅ KEY STRENGTHS", advice.get('pros', 'No data yet.'), "card-green"),
                ("🚀 GROWTH PATH", advice.get('growth', 'No data yet.'), "card-yellow"),
                ("🎯 FOCUS AREA", advice.get('errors', 'No data yet.'), "card-red")
            ]           
    
            for i, col in enumerate(cols):
                with col:
                    st.markdown(f"""
                        <div class="ai-card {data[i][2]}">
                            <span class="card-title">{data[i][0]}</span>
                            <div style="font-size: 0.85rem; line-height: 1.4;">{data[i][1]}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    with st.expander("🔍 READ MORE"):
                        st.info(data[i][1])
        else:
            st.info("Click 'Generate' to get AI mentorship for this student.")
# --- 3. ANALYTICS ---
with tabs[2]:
    st.markdown("<h2 style='color: #883322;'>📒 Электронный Дневник</h2>", unsafe_allow_html=True)
    
    # Получаем данные конкретного студента (если выбран в Profile) или всех
    student_filter = st.selectbox("Фильтр по студенту", ["Все"] + get_df("SELECT name FROM students")['name'].tolist())
    
    query = "SELECT date as 'Дата', type as 'Предмет/Тип', xp as 'Оценка (XP)' FROM history"
    params = ()
    if student_filter != "Все":
        query += " WHERE name = ? ORDER BY date DESC"
        params = (student_filter,)
    else:
        query += " ORDER BY date DESC"

    diary_df = get_df(query, params)
    
    if not diary_df.empty:
        # Стилизуем таблицу под дневник
        st.dataframe(diary_df, use_container_width=True, hide_index=True)
        
        # График прогресса ниже
        st.divider()
        st.subheader("📊 График успеваемости")
        h_df = get_df("SELECT date, xp, name FROM history")
        h_df['date'] = pd.to_datetime(h_df['date'])
        fig_line = px.line(h_df, x='date', y='xp', color='name', markers=True)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Дневник пуст. Оценки еще не выставлялись.")
# --- 4. TEACHER CONTROL ---

with tabs[3]:
        # Красивое приветствие сверху
        st.markdown("""
            <div style="background: linear-gradient(90deg, #883322 0%, #283123 100%); padding: 30px; border-radius: 20px; margin-bottom: 25px;">
                <h1 style="color: #EDE9DF; margin: 0;">Hello, Miss Aidana! </h1>
                <p style="color: #EACFA3; opacity: 0.9;">Manage your students and sync progress here.</p>
            </div>
        """, unsafe_allow_html=True)
        
        col_m1, col_m2 = st.columns(2)
        # далее ваш существующий код...

       
        with col_m1:

            st.subheader("Manual Award")

            with st.form("award_form"):

                names = get_df("SELECT name FROM students")['name'].tolist()

                n_s = st.selectbox("Student", names)

                xp_s = st.number_input("XP", min_value=1, value=100)

                cat = st.selectbox("Skill Area", ["**Speaking**", "**Listening**", "**Grammar**"])

                if st.form_submit_button("Grant Points"):

                    l, d, k = (20,0,0) if cat=="Speaking" else (0,20,0) if cat=="Listening" else (0,0,20)

                    run_query("UPDATE students SET xp=xp+?, leadership=MIN(100,leadership+?), discipline=MIN(100,discipline+?), knowledge=MIN(100,knowledge+?), level=((xp+?)/100)+1 WHERE name=?", (xp_s, l, d, k, xp_s, n_s))

                    run_query("INSERT INTO history (date, name, xp, type, month) VALUES (?,?,?,?,?)", (datetime.now().strftime("%Y-%m-%d"), n_s, xp_s, cat, datetime.now().strftime("%B %Y")))

                    st.success("Points Granted!"); st.rerun()



        with col_m2:

            st.subheader("Kahoot Import")

            k_raw = st.text_area("Paste from PDF:", placeholder="Narbol 1 73% 1 8608...")

            if st.button("🚀 Sync Kahoot"):

                matches = re.findall(r'([А-Яа-яA-Za-z0-9._-]+)\s+\d+\s+\d+%\s+\d+\s+(\d+)', k_raw)

                if matches:

                    db_names = get_df("SELECT name FROM students")['name'].tolist()

                    count = 0

                    for nick, score in matches:

                        pts = int(score) // 10

                        for db_n in db_names:

                            if nick.lower() in db_n.lower() or db_n.lower() in nick.lower():

                                run_query("UPDATE students SET xp=xp+?, level=((xp+?)/100)+1 WHERE name=?", (pts, pts, db_n))

                                run_query("INSERT INTO history (date, name, xp, type, month) VALUES (?,?,?,?,?)", (datetime.now().strftime("%Y-%m-%d"), db_n, pts, "Exam", datetime.now().strftime("%B %Y")))

                                count += 1

                    st.success(f"Synced {count} students!"); st.balloons(); st.rerun()



# --- 5. SETTINGS ---

if st.session_state.role == "admin":

    with tabs[4]:

        st.subheader("⚙️ System Management")

        new_n = st.text_input("New Student Name")

        if st.button("Register Student"):

            run_query("INSERT OR IGNORE INTO students (name, xp, level, leadership, discipline, knowledge) VALUES (?,0,1,20,20,20)", (new_n,))

            st.rerun()

       

        st.divider()

        st.subheader("Danger Zone")

        confirm = st.checkbox("Confirm Full Wipe")

        if st.button("🔥 ERASE ALL DATA", type="primary", disabled=not confirm):

            run_query("DROP TABLE IF EXISTS students"); run_query("DROP TABLE IF EXISTS history"); init_db()

            st.rerun()