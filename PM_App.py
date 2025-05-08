import streamlit as st
import pandas as pd
import uuid
from datetime import datetime, date

# --- Page Configuration & Styling ---
st.set_page_config(
    page_title="Project Management Tool",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    /* Main background */
    .stApp {
        background-color: #f7f9fc;
    }
    /* Sidebar background */
    .css-1d391kg { 
        background-color: #ffffff;
    }
    /* Card headings */
    .stMetric > div {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True
)

# --- Initialize Session State ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user' not in st.session_state:
    st.session_state['user'] = ''
if 'projects' not in st.session_state:
    st.session_state['projects'] = {}
if 'tasks' not in st.session_state:
    st.session_state['tasks'] = {}
if 'project_counter' not in st.session_state:
    st.session_state['project_counter'] = 0
if 'task_counter' not in st.session_state:
    st.session_state['task_counter'] = 0

# --- Authentication ---
def authenticate(email, pwd):
    return email == 'admin@example.com' and pwd == 'password123'

# --- ID Generators ---
def next_project_id():
    st.session_state['project_counter'] += 1
    return f"PRJ-{st.session_state['project_counter']:03d}"

def next_task_id():
    st.session_state['task_counter'] += 1
    return f"TSK-{st.session_state['task_counter']:03d}"

# --- Data Management ---
def add_project(name, desc, start, end, members):
    pid = next_project_id()
    st.session_state['projects'][pid] = {
        'id': pid,
        'name': name,
        'description': desc,
        'start_date': start,
        'end_date': end,
        'status': 'Not Started',
        'members': members,
        'created_by': st.session_state['user'],
        'created_at': datetime.now()
    }
    st.success(f"Project '{name}' added (ID: {pid})")

def delete_project(pid):
    st.session_state['projects'].pop(pid, None)
    st.session_state['tasks'] = {tid: t for tid, t in st.session_state['tasks'].items() if t['project_id'] != pid}
    st.success(f"Project {pid} deleted")


def update_project_status(pid, status):
    st.session_state['projects'][pid]['status'] = status
    st.success(f"Project {pid} set to {status}")

# --- Task Management ---
def add_task(pid, title, due, assignee, status):
    tid = next_task_id()
    st.session_state['tasks'][tid] = {
        'id': tid,
        'project_id': pid,
        'title': title,
        'due_date': due,
        'assignee': assignee,
        'status': status,
        'created_at': datetime.now()
    }
    st.success(f"Task '{title}' added (ID: {tid}) to {pid}")


def update_task(pid, tid, **kwargs):
    for k, v in kwargs.items():
        st.session_state['tasks'][tid][k] = v
    st.success(f"Task {tid} updated")

# --- Data Accessors ---
def get_projects_df():
    return pd.DataFrame(st.session_state['projects'].values())

def get_tasks_df():
    return pd.DataFrame(st.session_state['tasks'].values())

# --- Reporting ---
def project_metrics():
    df = get_projects_df()
    counts = df['status'].value_counts().reindex(['Not Started','In Progress','Completed','On Hold'], fill_value=0)
    return counts


def task_metrics():
    df = get_tasks_df()
    counts = df['status'].value_counts().reindex(['To Do','In Progress','Blocked','Completed'], fill_value=0)
    return counts


def upcoming_deadlines(days=7):
    today = date.today()
    return [p for p in st.session_state['projects'].values() if (p['end_date'] - today).days <= days]

# --- UI Components ---
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

# --- Main UI Flow ---
if not st.session_state['logged_in']:
    login_page()
else:
    # Sidebar Navigation
    st.sidebar.header(f"👤 {st.session_state['user']}")
    menu = st.sidebar.radio('Navigation', ['Dashboard','Projects','Tasks','Reports','Logout'])

    if menu == 'Logout':
        st.session_state['logged_in'] = False
        st.session_state['user'] = ''
        st.experimental_rerun()

    # Dashboard
    if menu == 'Dashboard':
        st.header('📊 Dashboard')
        proj_counts = project_metrics()
        task_counts = task_metrics()
        up_tasks = get_tasks_df()[get_tasks_df()['due_date'] < pd.Timestamp(date.today())]
        upcoming = upcoming_deadlines()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric('Total Projects', len(proj_counts))
        col2.metric('In Progress', proj_counts['In Progress'])
        col3.metric('Total Tasks', task_counts.sum())
        col4.metric('Overdue Tasks', len(up_tasks))

        st.subheader('Project Status Distribution')
        st.bar_chart(proj_counts)

        st.subheader('Task Status Distribution')
        st.bar_chart(task_counts)

        st.subheader('Upcoming Deadlines (7 days)')
        if upcoming:
            st.table(pd.DataFrame(upcoming)[['id','name','end_date']].rename(columns={'id':'ID','name':'Project','end_date':'Ends'}))
        else:
            st.info('No upcoming deadlines')

    # Projects Page
    elif menu == 'Projects':
        st.header('📁 Projects')
        with st.expander('➕ Add New Project'):
            name = st.text_input('Name')
            desc = st.text_area('Description')
            start = st.date_input('Start Date')
            end = st.date_input('End Date')
            members = st.multiselect('Members', ['Alice','Bob','Charlie','Dana'])
            if st.button('Create Project'):
                add_project(name, desc, start, end, members)

        dfp = get_projects_df()
        if not dfp.empty:
            st.table(dfp.set_index('id')[['name','status','start_date','end_date']].rename(columns={'name':'Name','start_date':'Start','end_date':'End','status':'Status'}))
            sel = st.selectbox('Select Project', options=dfp['id'], format_func=lambda x: f"{x} - {st.session_state['projects'][x]['name']}" )
            st.selectbox('Change Status', ['Not Started','In Progress','On Hold','Completed'], key='proj_status')
            if st.button('Update Project Status'):
                update_project_status(sel, st.session_state['proj_status'])
            if st.button('Delete Project'):
                delete_project(sel)
        else:
            st.info('No projects available')

    # Tasks Page
    elif menu == 'Tasks':
        st.header('✅ Tasks')
        with st.expander('➕ Add New Task'):
            pdp = get_projects_df()
            if not pdp.empty:
                pid = st.selectbox('Project', options=pdp['id'], format_func=lambda x: f"{x} - {st.session_state['projects'][x]['name']}" )
                title = st.text_input('Task Title')
                due = st.date_input('Due Date')
                assignee = st.selectbox('Assignee', ['Alice','Bob','Charlie','Dana'])
                status = st.selectbox('Status', ['To Do','In Progress','Blocked','Completed'])
                if st.button('Add Task'):
                    add_task(pid, title, due, assignee, status)
            else:
                st.info('Create a project first')

        dft = get_tasks_df()
        if not dft.empty:
            st.table(dft.set_index('id')[['project_id','title','assignee','status','due_date']].rename(columns={'project_id':'Project','title':'Title','assignee':'Assignee','due_date':'Due'}))
            tid = st.selectbox('Select Task', options=dft['id'])
            new_status = st.selectbox('Update Status', ['To Do','In Progress','Blocked','Completed'], key='task_status')
            if st.button('Update Task'):
                update_task(tid, 'status', new_status)
        else:
            st.info('No tasks available')

    # Reports Page
    elif menu == 'Reports':
        st.header('📈 Reports')
        proj_counts = project_metrics()
        task_counts = task_metrics()
        st.subheader('Projects by Status')
        st.bar_chart(proj_counts)
        st.subheader('Tasks by Status')
        st.bar_chart(task_counts)
        rate = task_counts['Completed'] / task_counts.sum() if task_counts.sum() else 0
        st.metric('Task Completion Rate', f"{rate:.0%}")
