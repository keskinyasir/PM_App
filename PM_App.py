import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client, Client

# --- Supabase Config ---
SUPABASE_URL = "https://sxpjijtxiqhxzgyxpgtm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN4cGppanR4aXFoeHpneXhwZ3RtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAwMTExMzAsImV4cCI6MjA2NTU4NzEzMH0.N_Ud7Pc83W5mf1yYYsJ8NzfQr_AeEkrGYT_CDFt0LB8"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        res = supabase.table("projects").select("*").execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Failed to fetch projects: {e}")
        return pd.DataFrame()

def fetch_tasks():
    try:
        res = supabase.table("tasks").select("*").execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Failed to fetch tasks: {e}")
        return pd.DataFrame()

def add_project(id, name, desc, start, end, members):
    try:
        new_project = {
            "id": id,
            "name": name,
            "description": desc,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "status": "Not Started",
            "members": members,
            "created_by": st.session_state['user'],
            "created_at": datetime.now().isoformat()
        }
        supabase.table("projects").insert(new_project).execute()
        st.success(f"Project '{name}' added.")
    except Exception as e:
        st.error(f"Error adding project: {e}")

def delete_project(pid):
    try:
        supabase.table("tasks").delete().eq("project_id", pid).execute()
        supabase.table("projects").delete().eq("id", pid).execute()
        st.success(f"Project {pid} deleted")
    except Exception as e:
        st.error(f"Failed to delete project {pid}: {e}")

def update_project_status(pid, status):
    try:
        supabase.table("projects").update({"status": status}).eq("id", pid).execute()
        st.success(f"Project {pid} updated to {status}")
    except Exception as e:
        st.error(f"Failed to update project status: {e}")

def add_task(pid, title, due, assignee, status):
    try:
        new_task = {
            "project_id": pid,
            "title": title,
            "due_date": due.isoformat(),
            "assignee": assignee,
            "status": status,
            "created_at": datetime.now().isoformat()
        }
        supabase.table("tasks").insert(new_task).execute()
        st.success(f"Task '{title}' added to project {pid}")
    except Exception as e:
        st.error(f"Failed to add task: {e}")

def update_task(task_id, field, value):
    try:
        supabase.table("tasks").update({field: value}).eq("id", task_id).execute()
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
        st.experimental_rerun()

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
                    add_project(project_code, name, desc, start, end, ",".join(members))

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
