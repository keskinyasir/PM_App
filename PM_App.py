# Updated Streamlit App with SQLite Integration
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date

DB_PATH = 'pm_app.db'

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_code TEXT UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                start_date TEXT,
                end_date TEXT,
                status TEXT,
                members TEXT,
                created_by TEXT,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                title TEXT NOT NULL,
                due_date TEXT,
                assignee TEXT,
                status TEXT,
                created_at TEXT,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        """)
        conn.commit()

def add_project_code_column_if_missing():
    with get_connection() as conn:
        result = conn.execute("PRAGMA table_info(projects)").fetchall()
        columns = [col[1] for col in result]
        if 'project_code' not in columns:
            conn.execute("ALTER TABLE projects ADD COLUMN project_code TEXT")
            conn.commit()
            st.toast("Added 'project_code' column to projects table")

# Initialize DB and fix schema
initialize_database()
add_project_code_column_if_missing()

# --- Page Configuration & Styling ---
st.set_page_config(
    page_title="Project Management Tool",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #f9f9f9; }
[data-testid="stSidebar"] { background-color: #1E3A8A; }
[data-testid="stSidebar"] * { color: #ffffff; }
.stMetric > div { background-color: #FFFFFF; border-left: 4px solid #1E3A8A; border-radius: 8px; padding: 10px; }
thead tr th { background-color: #E1EAF6 !important; color: #1E3A8A !important; }
.stButton>button { background-color: #1E3A8A; color: #ffffff; border-radius: 5px; }
.stButton>button:hover { background-color: #162c61; }
</style>
""", unsafe_allow_html=True)

# --- Authentication ---
def authenticate(email, pwd):
    return email == 'admin@example.com' and pwd == 'password123'

def login_page():
    st.title('🔐 Login')
    email = st.text_input('Email')
    pwd = st.text_input('Password', type='password')
    if st.button('Login'):
        if authenticate(email, pwd):
            st.session_state['logged_in'] = True
            st.session_state['user'] = email
            st.success(f"Welcome, {email}!")
        else:
            st.error('Invalid credentials')

# --- Database Helpers ---
def fetch_projects():
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM projects", conn)

def fetch_tasks():
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM tasks", conn)

def generate_project_code():
    with get_connection() as conn:
        result = conn.execute("SELECT COUNT(*) FROM projects").fetchone()
        count = result[0] + 1
        return f"PRJ-{count:03}"

def add_project(name, desc, start, end, members):
    project_code = generate_project_code()
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO projects (
                project_code, name, description, start_date, end_date, status, members, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, 'Not Started', ?, ?, ?)
        """, (
            project_code, name, desc, start.isoformat(), end.isoformat(),
            members, st.session_state['user'], datetime.now().isoformat()
        ))
        conn.commit()
    st.success(f"Project '{name}' added with Code {project_code}")

# Show initial preview table
dfp = fetch_projects()
if not dfp.empty:
    if 'project_code' in dfp.columns:
        st.table(
            dfp.set_index('project_code')[['name','status','start_date','end_date']]
            .rename(columns={'name':'Name','start_date':'Start','end_date':'End','status':'Status'})
        )
    else:
        st.warning("Project codes missing in database. Please refresh or check schema.")

# --- Rest of your code continues ---
# (You can keep all your existing project/task/dashboard/report menus unchanged)
