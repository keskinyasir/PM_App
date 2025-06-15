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

initialize_database()

# --- Page config and styling ---
st.set_page_config(
    page_title="Project Management Tool",
    page_icon=":clipboard:",
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
    st.title('Login')
    email = st.text_input('Email', key='login_email')
    pwd = st.text_input('Password', type='password', key='login_password')
    login_clicked = st.button('Login')

    if login_clicked:
        if authenticate(email, pwd):
            st.session_state['logged_in'] = True
            st.session_state['user'] = email
            st.success(f"Welcome, {email}!")
        else:
            st.error('Invalid credentials')

# --- DB helpers ---
def fetch_projects():
    try:
        with get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM projects", conn)
    except Exception as e:
        st.error(f"Failed to fetch projects: {e}")
        return pd.DataFrame()

def fetch_tasks():
    try:
        with get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM tasks", conn)
    except Exception as e:
        st.error(f"Failed to fetch tasks: {e}")
        return pd.DataFrame()

def add_project(id, name, desc, start, end, members):
    try:
        with get_connection() as conn:
            #project_code = f"PRJ-{int(datetime.now().timestamp())}"
            cursor = conn.execute("""
                INSERT INTO projects (id, name, description, start_date, end_date, status, members, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, 'Not Started', ?, ?, ?)
            """, (id, name, desc, start.isoformat(), end.isoformat(), members, st.session_state['user'], datetime.now().isoformat()))
            conn.commit()
            pid = cursor.lastrowid
        st.success(f"Project '{name}' added with ID {pid}")
    except Exception as e:
        import traceback
        st.error(f"Error adding project: {e}")  
        st.text(traceback.format_exc())
    cursor = conn.execute("SELECT last_insert_rowid()")
    st.write("Last inserted project ID:", cursor.fetchone()[0])

    df = fetch_projects()
    st.write(df)    




def delete_project(pid):
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM projects WHERE id = ?", (pid,))
            conn.execute("DELETE FROM tasks WHERE project_id = ?", (pid,))
            conn.commit()
        st.success(f"Project {pid} deleted")
    except Exception as e:
        st.error(f"Failed to delete project {pid}: {e}")

def update_project_status(pid, status):
    try:
        with get_connection() as conn:
            conn.execute("UPDATE projects SET status = ? WHERE id = ?", (status, pid))
            conn.commit()
        st.success(f"Project {pid} updated to {status}")
    except Exception as e:
        st.error(f"Failed to update project status: {e}")

def add_task(pid, title, due, assignee, status):
    try:
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO tasks (project_id, title, due_date, assignee, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (pid, title, due.isoformat(), assignee, status, datetime.now().isoformat()))
            conn.commit()
        st.success(f"Task '{title}' added to project {pid}")
    except Exception as e:
        st.error(f"Failed to add task: {e}")

def update_task(task_id, field, value):
    allowed_fields = ['title', 'due_date', 'assignee', 'status']
    if field not in allowed_fields:
        st.error(f"Field '{field}' is not allowed to update")
        return
    try:
        with get_connection() as conn:
            conn.execute(f"UPDATE tasks SET {field} = ? WHERE id = ?", (value, task_id))
            conn.commit()
        st.success(f"Task {task_id} updated: {field} → {value}")
    except Exception as e:
        st.error(f"Failed to update task: {e}")

# --- Metrics ---
def project_metrics():
    df = fetch_projects()
    if df.empty:
        return pd.Series(dtype=int)
    return df['status'].value_counts().reindex(['Not Started', 'In Progress', 'On Hold', 'Completed'], fill_value=0)

def task_metrics():
    df = fetch_tasks()
    if df.empty:
        return pd.Series(dtype=int)
    return df['status'].value_counts().reindex(['To Do', 'In Progress', 'Blocked', 'Completed'], fill_value=0)

def upcoming_deadlines(days=7):
    df = fetch_projects()
    if df.empty:
        return pd.DataFrame()
    df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce')
    upcoming = df[(df['end_date'] <= pd.Timestamp(date.today() + pd.Timedelta(days=days))) & (df['end_date'] >= pd.Timestamp(date.today()))]
    return upcoming[['id','name','end_date']]

# --- Main UI ---

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user' not in st.session_state:
    st.session_state['user'] = ''

if not st.session_state['logged_in']:
    login_page()
else:
    st.sidebar.header(f"👤 {st.session_state['user']}")

    menu = st.sidebar.radio('Navigation', ['Dashboard', 'Projects', 'Tasks', 'Reports', 'Logout'])

    if menu == 'Logout':
        st.session_state['logged_in'] = False
        st.session_state['user'] = ''
        st.experimental_rerun = lambda: None  # noop to prevent errors if accidentally called

    elif menu == 'Dashboard':
        st.header("📊 Dashboard")
        proj_counts = project_metrics()
        task_counts = task_metrics()
        df_tasks = fetch_tasks()
        if not df_tasks.empty:
            df_tasks['due_date'] = pd.to_datetime(df_tasks['due_date'], errors='coerce')
            overdue = df_tasks[df_tasks['due_date'] < pd.Timestamp(date.today())]
        else:
            overdue = pd.DataFrame()

        upcoming = upcoming_deadlines()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric('Total Projects', int(proj_counts.sum()))
        c2.metric('In Progress', int(proj_counts.get('In Progress', 0)))
        c3.metric('Total Tasks', int(task_counts.sum()))
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
        st.header("📁 Projects")
        with st.expander('➕ Add New Project'):
            project_code = f"PRJ-{int(datetime.now().timestamp())}"
            name = st.text_input('Name', key='add_proj_name')
            desc = st.text_area('Description', key='add_proj_desc')
            start = st.date_input('Start Date', value=date.today(), key='add_proj_start')
            end = st.date_input('End Date', value=date.today(), key='add_proj_end')
            members = st.multiselect('Members', ['Alice','Bob','Charlie','Dana'], key='add_proj_members')
            if st.button('Create Project', key='btn_add_project'):
                if not name:
                    st.error("Project name is required")
                elif start > end:
                    st.error("Start date cannot be after End date")
                else:
                    add_project(project_code ,name, desc, start, end, ",".join(members))

        dfp = fetch_projects()
        if not dfp.empty:
            st.table(dfp.set_index('id')[['name','status','start_date','end_date']]
                .rename(columns={'name':'Name','start_date':'Start','end_date':'End','status':'Status'}))
            sel = st.selectbox('Select Project', options=dfp['id'], key='sel_project',
                format_func=lambda x: f"{x} - {dfp[dfp['id']==x]['name'].iloc[0]}" if not dfp[dfp['id']==x].empty else str(x))
            new_stat = st.selectbox('Change Status', ['Not Started','In Progress','On Hold','Completed'], key='proj_status')
            if st.button('Update Project Status', key='btn_update_proj_status'):
                update_project_status(sel, new_stat)
            if st.button('Delete Project', key='btn_delete_proj'):
                delete_project(sel)
        else:
            st.info('No projects available')

    elif menu == 'Tasks':
        st.header('✅ Tasks')
        with st.expander('➕ Add New Task'):
            dproj = fetch_projects()
            if not dproj.empty:
                pid = st.selectbox('Project', options=dproj['id'], key='task_proj_select',
                    format_func=lambda x: f"{x} - {dproj[dproj['id']==x]['name'].iloc[0]}" if not dproj[dproj['id']==x].empty else str(x))
                title = st.text_input('Task Title', key='task_title')
                due = st.date_input('Due Date', value=date.today(), key='task_due')
                assignee = st.selectbox('Assignee', ['Alice','Bob','Charlie','Dana'], key='task_assignee')
                status = st.selectbox('Status', ['To Do','In Progress','Blocked','Completed'], key='task_status_add')
                if st.button('Add Task', key='btn_add_task'):
                    if not title:
                        st.error("Task title is required")
                    else:
                        add_task(pid, title, due, assignee, status)
            else:
                st.info('Create a project first')

        dft = fetch_tasks()
        if not dft.empty:
            dft['due_date'] = pd.to_datetime(dft['due_date'], errors='coerce')
            cols = ['project_id','title','assignee','status','due_date']
            df_disp = dft.set_index('id')[cols]
            st.table(df_disp.rename(columns={'project_id':'Project','title':'Title','assignee':'Assignee','status':'Status','due_date':'Due'}))

            tid = st.selectbox('Select Task', options=dft['id'], key='task_select')
            new_tstat = st.selectbox('Update Status', ['To Do','In Progress','Blocked','Completed'], key='task_status_update')
            if st.button('Update Task', key='btn_update_task'):
                update_task(tid,'status',new_tstat)
        else:
            st.info('No tasks available')

    elif menu == 'Reports':
        st.header("📈 Reports")
        proj_counts = project_metrics()
        task_counts = task_metrics()
        st.subheader('Projects by Status')
        st.bar_chart(proj_counts)
        st.subheader('Tasks by Status')
        st.bar_chart(task_counts)
        rate = (task_counts.get('Completed',0) / task_counts.sum()) if task_counts.sum() else 0
        st.metric('Task Completion Rate',f"{rate:.0%}")
