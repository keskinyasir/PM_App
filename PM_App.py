# Project Management Streamlit App with Dynamic SQLite Database
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

# Call init
initialize_database()

# --- Page Configuration ---
st.set_page_config(page_title="Project Management Tool", page_icon="📋", layout="wide")

# --- Styling ---
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #f9f9f9; }
[data-testid="stSidebar"] { background-color: #1E3A8A; }
[data-testid="stSidebar"] * { color: #ffffff; }
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

# --- Helpers ---
def fetch_projects():
    with get_connection() as conn:
        return pd.read_sql("SELECT * FROM projects", conn)

def fetch_tasks():
    with get_connection() as conn:
        return pd.read_sql("SELECT * FROM tasks", conn)

def generate_project_code():
    return f"PRJ-{int(datetime.now().timestamp())}"

def add_project(name, desc, start, end, members):
    code = generate_project_code()
    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO projects (project_code, name, description, start_date, end_date, status, members, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, 'Not Started', ?, ?, ?)
        """, (code, name, desc, start.isoformat(), end.isoformat(), members, st.session_state['user'], datetime.now().isoformat()))
        conn.commit()
        pid = cur.lastrowid
    st.success(f"Project '{name}' added (ID: {pid})")

def delete_project(pid):
    with get_connection() as conn:
        conn.execute("DELETE FROM projects WHERE id = ?", (pid,))
        conn.execute("DELETE FROM tasks WHERE project_id = ?", (pid,))
        conn.commit()
    st.success(f"Project {pid} deleted")

def update_project_status(pid, status):
    with get_connection() as conn:
        conn.execute("UPDATE projects SET status = ? WHERE id = ?", (status, pid))
        conn.commit()
    st.success(f"Project {pid} status updated")

def add_task(pid, title, due, assignee, status):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO tasks (project_id, title, due_date, assignee, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (pid, title, due, assignee, status, datetime.now().isoformat()))
        conn.commit()
    st.success(f"Task '{title}' added")

def update_task(task_id, field, value):
    with get_connection() as conn:
        conn.execute(f"UPDATE tasks SET {field} = ? WHERE id = ?", (value, task_id))
        conn.commit()
    st.success(f"Task {task_id} updated")

def project_metrics():
    df = fetch_projects()
    return df['status'].value_counts().reindex(['Not Started', 'In Progress', 'On Hold', 'Completed'], fill_value=0)

def task_metrics():
    df = fetch_tasks()
    return df['status'].value_counts().reindex(['To Do', 'In Progress', 'Blocked', 'Completed'], fill_value=0)

def upcoming_deadlines(days=7):
    df = fetch_projects()
    df['end_date'] = pd.to_datetime(df['end_date'])
    return df[df['end_date'] <= pd.Timestamp(date.today() + pd.Timedelta(days=days))]

# --- Main ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_page()
else:
    st.sidebar.header(f"👤 {st.session_state['user']}")
    menu = st.sidebar.radio('Navigation', ['Dashboard', 'Projects', 'Tasks', 'Reports', 'Logout'])

    if menu == 'Logout':
        st.session_state['logged_in'] = False
        st.session_state['user'] = ''
        st.experimental_rerun()

    if menu == 'Dashboard':
        st.header('📊 Dashboard')
        proj_counts = project_metrics()
        task_counts = task_metrics()
        overdue = fetch_tasks()
        overdue['due_date'] = pd.to_datetime(overdue['due_date'])
        overdue = overdue[overdue['due_date'] < pd.Timestamp.today()]
        upcoming = upcoming_deadlines()

        st.metric('Total Projects', proj_counts.sum())
        st.metric('Total Tasks', task_counts.sum())
        st.metric('Overdue Tasks', len(overdue))

        st.subheader('Projects by Status')
        st.bar_chart(proj_counts)

        st.subheader('Tasks by Status')
        st.bar_chart(task_counts)

        st.subheader('Upcoming Deadlines')
        st.dataframe(upcoming[['id','name','end_date']])

    elif menu == 'Projects':
        st.header('📁 Projects')
        with st.expander('➕ Add New Project'):
            name = st.text_input('Project Name')
            desc = st.text_area('Description')
            start = st.date_input('Start Date')
            end = st.date_input('End Date')
            members = st.text_input('Members (comma-separated)')
            if st.button('Add Project'):
                add_project(name, desc, start, end, members)

        dfp = fetch_projects()
        st.dataframe(dfp)

        sel = st.selectbox('Select Project ID to Update/Delete', dfp['id'])
        status = st.selectbox('Change Status', ['Not Started','In Progress','On Hold','Completed'])
        if st.button('Update Status'):
            update_project_status(sel, status)
        if st.button('Delete Project'):
            delete_project(sel)

    elif menu == 'Tasks':
        st.header('✅ Tasks')
        dproj = fetch_projects()
        with st.expander('➕ Add New Task'):
            pid = st.selectbox('Project', dproj['id'])
            title = st.text_input('Task Title')
            due = st.date_input('Due Date')
            assignee = st.text_input('Assignee')
            status = st.selectbox('Status', ['To Do','In Progress','Blocked','Completed'])
            if st.button('Add Task'):
                add_task(pid, title, due, assignee, status)

        dft = fetch_tasks()
        st.dataframe(dft)

        tid = st.selectbox('Select Task ID')
        tstatus = st.selectbox('Update Status', ['To Do','In Progress','Blocked','Completed'])
        if st.button('Update Task'):
            update_task(tid, 'status', tstatus)

    elif menu == 'Reports':
        st.header('📈 Reports')
        proj_counts = project_metrics()
        task_counts = task_metrics()
        st.bar_chart(proj_counts)
        st.bar_chart(task_counts)
        rate = task_counts.get('Completed',0)/task_counts.sum() if task_counts.sum() else 0
        st.metric('Task Completion Rate', f"{rate:.0%}")
