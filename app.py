from groq import Groq
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import re
import json
from datetime import datetime, timedelta 
import streamlit as st
if 'role' not in st.session_state:
    st.session_state.role = None

st.set_page_config(layout="wide") # Это растянет контент на весь экран
# Теперь пишем просто datetime.now(), а не datetime.datetime.now()
now = datetime.now() 
last_week_date = (now - timedelta(days=7)).strftime('%Y-%m-%d')
# --- ВСТАВИТЬ В НАЧАЛО ФАЙЛА ---
def get_titled_name(name, xp):
    if xp < 500:   rank = "🐣 Novice"
    elif xp < 1500: rank = "⚔️ Striker"
    elif xp < 3000: rank = "🛡️ Guardian"
    elif xp < 6000: rank = "📜 Archon"
    else:           rank = "👑 Legend"
    return f"{rank} {name}"
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

## --- 1. ОБНОВЛЕННЫЙ СТИЛЬ (Bright & Fun Kids Edition) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Comfortaa:wght@400;700&display=swap');

    /* Общий фон - светлый и радостный */
    .stApp {
        background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
        font-family: 'Comfortaa', cursive;
    }

    /* Карточка авторизации - как облако */
    .auth-container {
        background: white;
        border-radius: 40px;
        padding: 50px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.05);
        border: 4px solid #F0F9FF;
        margin-top: 5%;
        text-align: center;
    }

    /* Заголовки - крупные и дружелюбные */
    .main-title {
        color: #1E293B;
        font-weight: 700;
        font-size: 2.8rem !important;
        margin-bottom: 10px;
    }

    /* Инпуты - мягкие и понятные */
    .stTextInput>div>div>input {
        background-color: #F8FAFC !important;
        color: #1E293B !important;
        border: 2px solid #E2E8F0 !important;
        border-radius: 20px !important;
        padding: 15px !important;
        font-size: 1.1rem !important;
    }

    /* Кнопки - 3D стиль (как в играх) */
    .stButton>button {
        border-radius: 25px !important;
        padding: 15px 30px !important;
        font-weight: 700 !important;
        font-size: 1.2rem !important;
        border: none !important;
        transition: all 0.2s ease;
        box-shadow: 0 6px 0px #059669; /* Тень для объема */
        margin-bottom: 6px;
    }

    /* Кнопка Студента - Зеленая */
    div[data-testid="stVerticalBlock"] > div:nth-child(1) .stButton>button {
        background: #10B981 !important;
        color: white !important;
        box-shadow: 0 6px 0px #047857 !important;
    }

    /* Кнопка Учителя - Синяя */
    div[data-testid="stVerticalBlock"] > div:nth-child(2) .stButton>button {
        background: #3B82F6 !important;
        color: white !important;
        box-shadow: 0 6px 0px #1D4ED8 !important;
    }

    .stButton>button:active {
        transform: translateY(4px);
        box-shadow: 0 2px 0px #047857 !important;
    }

    .stButton>button:hover {
        opacity: 0.95;
        transform: scale(1.02);
    }

    /* Значки ролей */
    .role-badge {
        font-size: 1rem;
        font-weight: 700;
        padding: 8px 20px;
        border-radius: 30px;
        margin-bottom: 15px;
        display: inline-block;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
            /* Общие контейнеры для игрового вида */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 30px !important;
    }

    /* Карточки лидеров (Подиум) */
    .podium-card {
        background: white;
        border-radius: 35px;
        padding: 25px;
        text-align: center;
        box-shadow: 0 15px 35px rgba(0,0,0,0.05);
        border: 4px solid transparent;
        transition: transform 0.3s ease;
    }
    .podium-card:hover { transform: translateY(-10px); }
    
    /* Золотая, серебряная и бронзовая обводка */
    .gold { border-color: #FFD700; background: linear-gradient(180deg, #FFFDF0 0%, #FFFFFF 100%); }
    .silver { border-color: #C0C0C0; }
    .bronze { border-color: #CD7F32; }

    /* Прогресс-бары в стиле RPG */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #98D8AA 0%, #4FACFE 100%) !important;
        border-radius: 10px;
        height: 12px !important;
    }

    /* Плашки для Скиллов */
    .skill-bubble {
        background: #F0F9FF;
        border-radius: 20px;
        padding: 15px 25px;
        display: inline-block;
        margin: 10px;
        border: 2px solid #E0F2FE;
        font-weight: 700;
        color: #0369A1;
    }

    /* AI Блок - Делаем его как "Сообщение от Мастера" */
    .ai-mentor-box {
        background: #FFFFFF;
        border-radius: 30px;
        padding: 30px;
        border-left: 10px solid #98D8AA;
        box-shadow: 0 10px 30px rgba(152, 216, 170, 0.2);
        margin-top: 20px;
    }
            /* 1. Общая обертка для вкладок, чтобы контент не "расползался" */
    .stTabs {
        background: rgba(255, 255, 255, 0.4);
        border-radius: 30px;
        padding: 20px;
        border: 2px solid rgba(255, 255, 255, 0.6);
        box-shadow: inset 0 0 20px rgba(255, 255, 255, 0.5);
    }

    /* 2. Красивые границы для карточек статов (Level, XP, Rank) */
    .stat-card {
        background: white !important;
        border-radius: 25px !important;
        padding: 20px;
        text-align: center;
        /* Двойная граница: внешняя цветная и внутренняя мягкая */
        border: 4px solid #F0F9FF !important;
        outline: 2px solid #3B82F6; /* Тонкая яркая линия */
        box-shadow: 0 15px 30px rgba(59, 130, 246, 0.1) !important;
        transition: all 0.3s ease;
    }

    /* 3. Границы для AI карточек с градиентным свечением */
    .ai-bubble {
        background: white !important;
        border-radius: 30px !important;
        padding: 25px;
        position: relative;
        border: none !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important;
        z-index: 1;
    }

    /* Создаем цветную "рамку-подложку" для AI блоков */
    .ai-bubble::before {
        content: "";
        position: absolute;
        top: -3px; left: -3px; right: -3px; bottom: -3px;
        background: linear-gradient(135deg, #98D8AA, #4FACFE);
        border-radius: 33px;
        z-index: -1;
        opacity: 0.4; /* Мягкое свечение вокруг */
    }

    /* 4. Рамка для Радарной диаграммы */
    .js-plotly-plot {
        background: white;
        border-radius: 30px;
        padding: 10px;
        border: 3px dashed #E2E8F0; /* Пунктирная "чертежная" граница */
    }

    /* 5. Красивая граница для контейнера выбора студента */
    div[data-baseweb="select"] {
        border: 2px solid #98D8AA !important;
        border-radius: 15px !important;
        background: white !important;
    }

    /* 6. Кастомная граница для Divider (разделителя) */
    hr {
        border: 0;
        height: 2px;
        background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(152, 216, 170, 0.75), rgba(0, 0, 0, 0));
        margin: 40px 0 !important;
    }
            /* Стилизация контейнера табов */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(255, 255, 255, 0.5); /* Полупрозрачный фон */
        padding: 10px 20px;
        border-radius: 50px;
        border: 2px solid #E0F2FE;
    }

    /* Стилизация каждой отдельной вкладки */
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: white !important;
        border-radius: 25px !important;
        padding: 0 25px !important;
        border: 2px solid transparent !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }

    /* Эффект при наведении на вкладку */
    .stTabs [data-baseweb="tab"]:hover {
        border-color: #98D8AA !important;
        transform: translateY(-2px);
        color: #10B981 !important;
    }

    /* Активная (выбранная) вкладка */
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: white !important;
        box-shadow: 0 8px 15px rgba(16, 185, 129, 0.3) !important;
    }

    /* Убираем стандартную подчеркивающую линию Streamlit */
    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }
            /* Анимация для прогресс-бара */
.stProgress > div > div > div > div {
    background-image: linear-gradient(to right, #ff4b4b, #3b82f6);
    box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
    transition: width 0.5s ease-in-out;
}
    </style>
""", unsafe_allow_html=True)

## --- 2. ОБНОВЛЕННЫЙ БЛОК АВТОРИЗАЦИИ (ТЕКСТ ВНУТРИ ПЛАШКИ) ---
if st.session_state.role is None:
    # Немного отступим сверху
    st.write("<br>", unsafe_allow_html=True)
    
    _, center_col, _ = st.columns([0.5, 2, 0.5])
    
    with center_col:
        # Теперь ракета и English Adventure живут внутри auth-container
        st.markdown("""
            <div class="auth-container" style="margin-top: 0; padding: 40px;">
                <h1 style='font-size: 5rem; margin: 0;'>🚀</h1>
                <h1 class='main-title' style='margin-bottom: 5px;'>English Adventure</h1>
                <p style='color: #64748B; font-size: 1.1rem; margin-bottom: 0;'>Are you ready to learn today?</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Оставляем остальное как есть (колонки с кнопками)
        st.write("<br>", unsafe_allow_html=True) 
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown('<span class="role-badge" style="background: #D1FAE5; color: #065F46;">I am a Student 🌟</span>', unsafe_allow_html=True)
            st.write("") 
            if st.button("GO TO CLASS!", use_container_width=True):
                st.session_state.role = "student"
                st.rerun()
                
        with col_right:
            st.markdown('<span class="role-badge" style="background: #DBEAFE; color: #1E40AF;">Teacher Portal 🔑</span>', unsafe_allow_html=True)
            pwd = st.text_input("Enter Secret Key", type="password", placeholder="Your key...", label_visibility="visible")
            if st.button("OPEN DOOR", use_container_width=True):
                if pwd == "1234":
                    st.session_state.role = "admin"
                    st.rerun()
                else:
                    st.error("Oops! Wrong key! 🧐")
        
    st.stop()
with st.sidebar:
    if st.session_state.role == "admin":
        # --- SIDEBAR ДЛЯ УЧИТЕЛЯ ---
        st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 20px; border: 2px solid #E0F2FE; text-align: center;">
                <p style="font-size: 50px; margin: 0;">👩‍🏫</p>
                <h3 style="margin: 10px 0 5px 0;">Miss Aidana</h3>
                <p style="color: #64748B; font-size: 0.8rem;">Academy Mentor</p>
            </div>
        """, unsafe_allow_html=True)
        # ... тут остальной твой код для админа (статистика и т.д.)
        
    elif st.session_state.role == "student":
        # --- SIDEBAR ДЛЯ СТУДЕНТА ---
        # 1. Сначала даем выбрать имя (если нет системы логина по паролю)
        fresh_sts = get_df("SELECT * FROM students")
        student_name = st.selectbox("Who is climbing the mountain today?", fresh_sts['name'].tolist())
        
        # 2. Получаем данные этого студента
        u = fresh_sts[fresh_sts['name'] == student_name].iloc[0]
        
        # 3. Визуальный блок профиля
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #6EE7B7 0%, #3B82F6 100%); 
                        padding: 20px; border-radius: 20px; text-align: center; color: white;">
                <p style="font-size: 50px; margin: 0;">👤</p>
                <h3 style="margin: 10px 0 0 0;">{u['name']}</h3>
                <p style="opacity: 0.9; font-size: 0.8rem;">Level {u['level']} Warrior</p>
            </div>
        """, unsafe_allow_html=True)

        # 4. Прогресс-бар до следующего уровня (гибкий элемент)
        current_xp = u['xp']
        next_lvl_xp = (u['level'] + 1) * 1000 # Допустим, каждый левел — 1000 XP
        progress = (current_xp % 1000) / 1000
        
        st.write("")
        st.markdown(f"**Next Level Progress:** {int(progress*100)}%")
        st.progress(progress)
        
        # 5. Личные ачивки
        st.markdown(f"""
            <div style="background: rgba(255,255,255,0.5); padding: 10px; border-radius: 15px; margin-top: 15px;">
                <p style="margin:0; font-size: 0.8rem;">🏆 <b>Rank:</b> {u['level']}</p>
                <p style="margin:0; font-size: 0.8rem;">🔥 <b>Total XP:</b> {u['xp']}</p>
            </div>
        """, unsafe_allow_html=True)

    # Общая кнопка выхода для всех
    st.write("<br>"*5, unsafe_allow_html=True)
    if st.button("🚪 Leave Adventure", use_container_width=True): 
        st.session_state.role = None
        st.rerun()

# Определяем список вкладок в зависимости от роли
tab_titles = ["🏆 TOP CHART", "👤 MY SKILLS", "📈 HISTORY"]
if st.session_state.role == "admin":
    tab_titles += ["👨‍🏫 CONTROL", "⚙️ DB"]

# Создаем вкладки из этого списка
tabs = st.tabs(tab_titles)
with tabs[0]:
    st.markdown("<h1 style='text-align: center; color: #883322;'>🏆 LEADERBOARD CENTRAL</h1>", unsafe_allow_html=True)

    # 1. Fetch historical weeks from your 'history' table
    weeks_query = """
        SELECT DISTINCT strftime('%W', date) as week_num 
        FROM history 
        ORDER BY week_num DESC
    """
    weeks_df = get_df(weeks_query)

    if not weeks_df.empty:
        all_weeks = weeks_df['week_num'].tolist()
        min_week = int(min(all_weeks)) # First week in your data becomes Week 1
        
        # Style selection area
        st.write("")
        selected_week = st.selectbox(
            "📅 Select Training Week:", 
            all_weeks,
            format_func=lambda x: f"Academic Week {int(x) - min_week + 1}"
        )

        # 2. Get data for the selected week
        weekly_stats = get_df(f"""
            SELECT name, SUM(xp) as w_xp 
            FROM history 
            WHERE strftime('%W', date) = '{selected_week}' 
            GROUP BY name 
            ORDER BY w_xp DESC
        """)

        if not weekly_stats.empty:
            st.write("") 
            
            # --- THE PODIUM (TOP 3) ---
            top_cols = st.columns([1, 1.2, 1]) 
            
            # SILVER - 2nd Place (Left)
            if len(weekly_stats) > 1:
                with top_cols[0]:
                    st.markdown(f"""
                        <div style="background: rgba(192, 192, 192, 0.1); border: 2px solid #C0C0C0; padding: 20px; border-radius: 20px; text-align: center; margin-top: 45px;">
                            <span style="font-size: 2.5rem;">🥈</span>
                            <h3 style="margin: 0; color: #283123; font-size: 1rem;">{weekly_stats.iloc[1]['name']}</h3>
                            <p style="font-weight: bold; color: #71717a; font-size: 1.1rem; margin:0;">{weekly_stats.iloc[1]['w_xp']} XP</p>
                            <small style="color: #C0C0C0; text-transform: uppercase;">Runner Up</small>
                        </div>
                    """, unsafe_allow_html=True)

            # GOLD - 1st Place (Center)
            with top_cols[1]:
                st.markdown(f"""
                    <div style="background: rgba(255, 215, 0, 0.15); border: 3px solid #FFD700; padding: 25px; border-radius: 25px; text-align: center; box-shadow: 0 10px 40px rgba(255, 215, 0, 0.2);">
                        <span style="font-size: 3.5rem;">👑</span>
                        <h2 style="margin: 0; color: #883322; font-size: 1.4rem;">{weekly_stats.iloc[0]['name']}</h2>
                        <p style="font-weight: bold; color: #FFD700; font-size: 1.8rem; margin: 0;">{weekly_stats.iloc[0]['w_xp']} XP</p>
                        <small style="text-transform: uppercase; letter-spacing: 2px; font-weight: bold; color: #883322;">WEEKLY MVP</small>
                    </div>
                """, unsafe_allow_html=True)

            # BRONZE - 3rd Place (Right)
            if len(weekly_stats) > 2:
                with top_cols[2]:
                    st.markdown(f"""
                        <div style="background: rgba(205, 127, 50, 0.1); border: 2px solid #CD7F32; padding: 20px; border-radius: 20px; text-align: center; margin-top: 55px;">
                            <span style="font-size: 2rem;">🥉</span>
                            <h3 style="margin: 0; color: #283123; font-size: 0.9rem;">{weekly_stats.iloc[2]['name']}</h3>
                            <p style="font-weight: bold; color: #CD7F32; font-size: 1rem; margin:0;">{weekly_stats.iloc[2]['w_xp']} XP</p>
                            <small style="color: #CD7F32; text-transform: uppercase;">Rising Star</small>
                        </div>
                    """, unsafe_allow_html=True)

            st.write("")
            st.write("")

            # --- FULL WEEKLY TABLE ---
            st.markdown("### 📋 Full Performance List")
            
            # Rank Logic
            weekly_stats['Rank'] = range(1, len(weekly_stats) + 1)
            
            df_display = weekly_stats[['Rank', 'name', 'w_xp']].rename(columns={
                'Rank': 'Pos', 
                'name': 'Student Name', 
                'w_xp': 'Points (XP)'
            })

            st.dataframe(
                df_display, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Pos": st.column_config.NumberColumn(format="#%d"),
                    "Points (XP)": st.column_config.ProgressColumn(
                        label="Progress Bar",
                        min_value=0, 
                        max_value=int(weekly_stats['w_xp'].max()),
                        format="%d XP"
                    )
                }
            )
    else:
        st.warning("No data found in History yet.")

    st.divider()
    
    # --- GLOBAL HALL OF FAME ---
    st.markdown("<h2 style='text-align: center; color: #283123;'>🌍 GLOBAL HALL OF FAME</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; opacity: 0.7;'>Lifetime ranking of all students</p>", unsafe_allow_html=True)
    
    global_df = get_df("SELECT name, xp, level FROM students ORDER BY xp DESC")
    if not global_df.empty:
        # Add titles to names if you have the get_titled_name function
        # global_df['name'] = global_df.apply(lambda x: get_titled_name(x['name'], x['xp']), axis=1)
        
        st.table(global_df.rename(columns={'name': 'Student', 'xp': 'Total XP', 'level': 'Current LVL'}))
    # --- НОВЫЙ БЛОК: WEEKLY SPRINT ---
# 1. Вычисляем дату начала недели (7 дней назад)



with tabs[1]:
    fresh_sts = get_df("SELECT * FROM students")
    if not fresh_sts.empty:
        # Центрируем выбор ученика
        _, sel_col, _ = st.columns([1, 2, 1])
        with sel_col:
            sel_name = st.selectbox("🔍 Найти героя:", fresh_sts['name'].tolist())
        
        # Логика сброса кеша (оставляем твою)
        if "last_selected_student" not in st.session_state:
            st.session_state.last_selected_student = sel_name
        if st.session_state.last_selected_student != sel_name:
            st.session_state.last_selected_student = sel_name
            if f"ai_advice_{sel_name}" in st.session_state:
                del st.session_state[f"ai_advice_{sel_name}"]

        u = fresh_sts[fresh_sts['name'] == sel_name].iloc[0]
        
        # --- HEADER: ИМЯ И РАНГ ---
        st.markdown(f"""
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="font-size: 3.5rem; margin-bottom: 0;">{sel_name}</h1>
                <div class="rank-badge">✨ {u['xp'] // 1000 + 1} LEVEL ELITE</div>
            </div>
        """, unsafe_allow_html=True)

        # --- КАРТОЧКИ УРОВНЯ ---
        col_rank, col_lvl, col_xp = st.columns(3)
        xp_val = u['xp']
        rank_name = "A1: ELEMENTARY" if xp_val < 1000 else "A2: PRE-INTER" if xp_val < 2000 else "B1: INTERMEDIATE" if xp_val < 3000 else "B2: UPPER-INTER" if xp_val < 6000 else "C2: THE NATIVE"
        
        with col_rank:
            st.markdown(f'<div class="stat-card"><p style="color:#94A3B8; font-weight:700;">RANK</p><h2 style="color:#3B82F6;">{rank_name}</h2></div>', unsafe_allow_html=True)
        with col_lvl:
            st.markdown(f'<div class="stat-card"><p style="color:#94A3B8; font-weight:700;">LEVEL</p><h2 style="color:#10B981;">{u["level"]}</h2></div>', unsafe_allow_html=True)
        with col_xp:
            st.markdown(f'<div class="stat-card"><p style="color:#94A3B8; font-weight:700;">TOTAL XP</p><h2 style="color:#F59E0B;">{xp_val}</h2></div>', unsafe_allow_html=True)

        st.write("")
        
        # --- RADAR CHART (СДЕЛАЕМ ЯРЧЕ) ---
        c_radar, c_info = st.columns([3, 2])
        with c_radar:
            fig = go.Figure(data=go.Scatterpolar(
                r=[u['leadership'], u['discipline'], u['knowledge']],
                theta=['Speaking 🗣️', 'Listening 🎧', 'Grammar 📝'],
                fill='toself', 
                line=dict(color='#FF6B6B', width=4),
                fillcolor='rgba(255, 107, 107, 0.3)'
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor="#E2E8F0")),
                showlegend=False, 
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=14, family="Comfortaa")
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with c_info:
            st.markdown("### 🏹 Skill Progress")
            st.write("Speaking")
            st.progress(u['leadership']/100)
            st.write("Listening")
            st.progress(u['discipline']/100)
            st.write("Grammar")
            st.progress(u['knowledge']/100)

        st.divider()
        
        # --- AI TUTOR (ИГРОВОЙ ВИД) ---
        st.markdown("<h2 style='text-align: center;'>🤖 Your Personal AI Mentor</h2>", unsafe_allow_html=True)
        
        btn_col1, btn_col2, _ = st.columns([1, 1, 2])
        gen_btn = btn_col1.button("✨ Magic Advice", use_container_width=True)
        if btn_col2.button("🔄 Reset Mentor", use_container_width=True):
            if f"ai_advice_{sel_name}" in st.session_state:
                del st.session_state[f"ai_advice_{sel_name}"]
            st.rerun()

        if gen_btn:
            with st.spinner('🧙‍♂️ Wizard is reading your scrolls...'):
                student_history = get_df("SELECT date, xp, type FROM history WHERE name=? ORDER BY date DESC LIMIT 5", (sel_name,))
                current_stats = {'leadership': u['leadership'], 'discipline': u['discipline'], 'knowledge': u['knowledge']}
                res = get_ai_recommendation(sel_name, current_stats, student_history)
                if res:
                    st.session_state[f"ai_advice_{sel_name}"] = res
                    st.rerun()

        advice = st.session_state.get(f"ai_advice_{sel_name}")

        if advice and isinstance(advice, dict):
            # Отображаем как красивые блоки
            ai_cols = st.columns(3)
            
            content = [
                ("🌟 Super Power", advice.get('pros', ''), "#D1FAE5", "🟢"),
                ("🚀 Level Up Plan", advice.get('growth', ''), "#DBEAFE", "🔵"),
                ("🎯 Secret Quest", advice.get('errors', ''), "#FEE2E2", "🔴")
            ]

            for i, col in enumerate(ai_cols):
                with col:
                    st.markdown(f"""
                        <div class="ai-bubble">
                            <h3 style="color: {content[i][2].replace('E', '4')};">{content[i][3]} {content[i][0]}</h3>
                            <p style="font-size: 0.9rem; color: #475569;">{content[i][1]}</p>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("👋 Привет! Нажми 'Magic Advice', чтобы я подсказал, как стать еще круче!")
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

if st.session_state.role == "admin":
    # --- 4. TEACHER CONTROL ---
    with tabs[3]:
        st.markdown(f"""
            <div style="background-color: #ffffff; padding: 20px; border-radius: 15px; 
                        box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-left: 10px solid #F0944D; margin-bottom: 25px;">
                <h2 style="color: #283123; margin: 0;">Good day, Miss Aidana! ✨</h2>
                <p style="color: #883322; font-weight: 500; margin-top: 5px;">Your students have been busy. Let's review their progress.</p>
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
