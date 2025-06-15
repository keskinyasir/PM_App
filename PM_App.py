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
        # Check if project_code column exists
        result = conn.execute("PRAGMA table_info(projects)").fetchall()
        columns = [col[1] for col in result]
        if 'project_code' not in columns:
            conn.execute("ALTER TABLE projects ADD COLUMN project_code TEXT")
            conn.commit()
            st.info("Added 'project_code' column to projects table.")


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
        count = result[0] + 1  # Next project number
        return f"PRJ-{count:03}"  # e.g., PRJ-001

def add_project(name, desc, start, end, members):
    project_code = generate_project_code()
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO projects (
                project_code, name, description, start_date, end_date, status, members, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, 'Not Started', ?, ?, ?)
        """, (
            project_code, name, desc, start.isoformat(), end.isoformat(),
            members, st.session_state['user'], datetime.now().isoformat()
        ))
        conn.commit()
    st.success(f"Project '{name}' added with Code {project_code}")

dfp = fetch_projects()
if not dfp.empty:
    st.table(
        dfp.set_index('project_code')[['name','status','start_date','end_date']]
        .rename(columns={'name':'Name','start_date':'Start','end_date':'End','status':'Status'})
    )


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
    st.success(f"Project {pid} updated to {status}")

def add_task(pid, title, due, assignee, status):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO tasks (project_id, title, due_date, assignee, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (pid, title, due, assignee, status, datetime.now()))
        conn.commit()
    st.success(f"Task '{title}' added to project {pid}")

def update_task(task_id, field, value):
    if task_id in st.session_state['tasks']:
        st.session_state['tasks'][task_id][field] = value
        st.success(f"Task {task_id} updated: {field} → {value}")
    else:
        st.error("Task not found.")

# --- Metrics ---
def project_metrics():
    df = fetch_projects()
    return df['status'].value_counts().reindex(['Not Started', 'In Progress', 'On Hold', 'Completed'], fill_value=0)

def task_metrics():
    df = fetch_tasks()
    return df['status'].value_counts().reindex(['To Do', 'In Progress', 'Blocked', 'Completed'], fill_value=0)

def upcoming_deadlines(days=7):
    df = fetch_projects()
    df['end_date'] = pd.to_datetime(df['end_date'])
    upcoming = df[df['end_date'] <= pd.Timestamp(date.today() + pd.Timedelta(days=days))]
    return upcoming[['id','name','end_date']]

# --- Main UI ---
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
        df_tasks = fetch_tasks()
        df_tasks['due_date'] = pd.to_datetime(df_tasks['due_date'])
        overdue = df_tasks[df_tasks['due_date'] < pd.Timestamp(date.today())]
        upcoming = upcoming_deadlines()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric('Total Projects', proj_counts.sum())
        c2.metric('In Progress', proj_counts.get('In Progress', 0))
        c3.metric('Total Tasks', task_counts.sum())
        c4.metric('Overdue Tasks', len(overdue))

        st.subheader('Project Status Distribution')
        st.bar_chart(proj_counts)

        st.subheader('Task Status Distribution')
        st.bar_chart(task_counts)

        st.subheader('Upcoming Deadlines')
        if not upcoming.empty:
            st.table(upcoming.rename(columns={'id':'ID','name':'Project','end_date':'Ends'}))
        else:
            st.info('No upcoming deadlines')

    elif menu == 'Projects':
        st.header('📁 Projects')
        with st.expander('➕ Add New Project'):
            name = st.text_input('Name')
            desc = st.text_area('Description')
            start = st.date_input('Start Date')
            end = st.date_input('End Date')
            members = st.multiselect('Members', ['Alice','Bob','Charlie','Dana'])
            if st.button('Create Project'):
                add_project(name, desc, start, end, ",".join(members))

        dfp = fetch_projects()
        if not dfp.empty:
            st.table(
                dfp.set_index('id')[['name','status','start_date','end_date']]
                .rename(columns={'name':'Name','start_date':'Start','end_date':'End','status':'Status'})
            )
            sel = st.selectbox(
                'Select Project', options=dfp['id'],
                format_func=lambda x: f"{x} - {dfp[dfp['id']==x]['name'].iloc[0]}" if not dfp[dfp['id']==x].empty else str(x)

            )
            new_stat = st.selectbox('Change Status', ['Not Started','In Progress','On Hold','Completed'], key='proj_status')
            if st.button('Update Project Status'):
                update_project_status(sel, new_stat)
            if st.button('Delete Project'):
                delete_project(sel)
        else:
            st.info('No projects available')

    elif menu == 'Tasks':
        st.header('✅ Tasks')
        with st.expander('➕ Add New Task'):
            dproj = fetch_projects()
            if not dproj.empty:
                pid = st.selectbox(
                    'Project', options=dproj['id'],
                    format_func=lambda x: f"{x} - {dproj[dproj['id']==x]['name'].iloc[0]}" if not dproj[dproj['id']==x].empty else str(x)

                )
                title = st.text_input('Task Title')
                due = st.date_input('Due Date')
                assignee = st.selectbox('Assignee', ['Alice','Bob','Charlie','Dana'])
                status = st.selectbox('Status', ['To Do','In Progress','Blocked','Completed'])
                if st.button('Add Task'):
                    add_task(pid, title, due, assignee, status)
            else:
                st.info('Create a project first')

        dft = fetch_tasks()
        if not dft.empty:
            dft['due_date'] = pd.to_datetime(dft['due_date'])
            cols = ['project_id','title','assignee','status','due_date']
            df_disp = dft.set_index('id')[cols]
            st.table(df_disp.rename(columns={'project_id':'Project','title':'Title','assignee':'Assignee','status':'Status','due_date':'Due'}))

            tid = st.selectbox('Select Task', options=dft['id'])
            new_tstat = st.selectbox('Update Status', ['To Do','In Progress','Blocked','Completed'], key='task_status')
            if st.button('Update Task'):
                update_task(tid,'status',new_tstat)
        else:
            st.info('No tasks available')

    elif menu == 'Reports':
        st.header('📈 Reports')
        proj_counts = project_metrics()
        task_counts = task_metrics()
        st.subheader('Projects by Status')
        st.bar_chart(proj_counts)
        st.subheader('Tasks by Status')
        st.bar_chart(task_counts)
        rate = task_counts.get('Completed',0)/task_counts.sum() if task_counts.sum() else 0
        st.metric('Task Completion Rate',f"{rate:.0%}")
