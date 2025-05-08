import streamlit as st
import pandas as pd
import uuid
from datetime import date, datetime

# --- Initialize session state ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user' not in st.session_state:
    st.session_state['user'] = ''
if 'projects' not in st.session_state:
    st.session_state['projects'] = {}
if 'tasks' not in st.session_state:
    st.session_state['tasks'] = {}

# --- Authentication Functions ---
def authenticate_user(email, password):
    # Basit doğrulama: admin@example.com / password123
    return email == 'admin@example.com' and password == 'password123'

def login_page():
    st.title('🔐 Login')
    email = st.text_input('Email')
    password = st.text_input('Password', type='password')
    if st.button('Login'):
        if authenticate_user(email, password):
            st.session_state['logged_in'] = True
            st.session_state['user'] = email
            st.success(f'Logged in as {email}')
        else:
            st.error('Invalid credentials')

# --- Project Management Functions ---
def add_project(name, desc, start, end, members):
    pid = str(uuid.uuid4())
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
    st.success(f'Project "{name}" added')

def delete_project(pid):
    st.session_state['projects'].pop(pid, None)
    # Remove related tasks
    st.session_state['tasks'] = {tid: t for tid, t in st.session_state['tasks'].items() if t['project_id'] != pid}
    st.success('Project deleted')

def list_projects():
    return pd.DataFrame(st.session_state['projects'].values())

def set_project_status(pid, status):
    st.session_state['projects'][pid]['status'] = status
    st.success('Status updated')

# --- Task Management Functions ---
def add_task(pid, title, due_date, assignee):
    tid = str(uuid.uuid4())
    st.session_state['tasks'][tid] = {
        'id': tid,
        'project_id': pid,
        'title': title,
        'due_date': due_date,
        'assignee': assignee,
        'completed': False,
        'created_at': datetime.now()
    }
    st.success('Task added')

def update_task_status(tid, completed):
    st.session_state['tasks'][tid]['completed'] = completed
    st.success('Task status updated')

def list_tasks():
    return pd.DataFrame(st.session_state['tasks'].values())

# --- Reporting Functions ---
def project_summary():
    df = list_projects()
    if not df.empty:
        counts = df['status'].value_counts()
        st.subheader('Project Status Summary')
        st.bar_chart(counts)
        st.write('Total Projects:', len(df))
    else:
        st.info('No projects to summarize')

def upcoming_deadlines(days=7):
    today = date.today()
    upcoming = [p for p in st.session_state['projects'].values() if (p['end_date'] - today).days <= days]
    return pd.DataFrame(upcoming)

# --- UI Flow ---
if not st.session_state['logged_in']:
    login_page()
else:
    st.sidebar.title(f"👤 {st.session_state['user']}")
    page = st.sidebar.selectbox('Menu', ['Dashboard','Projects','Tasks','Reports','Logout'])

    if page == 'Logout':
        st.session_state['logged_in'] = False
        st.session_state['user'] = ''

    elif page == 'Dashboard':
        st.title('📊 Dashboard')
        project_summary()
        st.write('### Upcoming Deadlines (Next 7 days)')
        ud = upcoming_deadlines()
        if not ud.empty:
            st.table(ud)
        else:
            st.info('No upcoming deadlines')

    elif page == 'Projects':
        st.title('📁 Projects')
        with st.expander('➕ Add Project'):
            name = st.text_input('Name')
            desc = st.text_area('Description')
            start = st.date_input('Start Date')
            end = st.date_input('End Date')
            members = st.multiselect('Members', ['Alice','Bob','Charlie'])
            if st.button('Add Project'):
                add_project(name, desc, start, end, members)

        df = list_projects()
        if not df.empty:
            st.table(df)
            pid = st.selectbox('Select Project to Modify', df['id'])
            status = st.selectbox('Set Status', ['Not Started','In Progress','Completed'])
            if st.button('Update Status'):
                set_project_status(pid, status)
            if st.button('Delete Project'):
                delete_project(pid)
        else:
            st.info('No projects yet')

    elif page == 'Tasks':
        st.title('✅ Tasks')
        with st.expander('➕ Add Task'):
            proj_ids = list(st.session_state['projects'].keys())
            if proj_ids:
                pid = st.selectbox('Project', proj_ids)
                title = st.text_input('Task Title')
                due = st.date_input('Due Date')
                assignee = st.selectbox('Assignee', ['Alice','Bob','Charlie'])
                if st.button('Add Task'):
                    add_task(pid, title, due, assignee)
            else:
                st.info('Add a project first')

        dt = list_tasks()
        if not dt.empty:
            st.table(dt)
            tid = st.selectbox('Select Task', dt['id'])
            done = st.checkbox('Completed', value=st.session_state['tasks'][tid]['completed'])
            if st.button('Update Task'):
                update_task_status(tid, done)
        else:
            st.info('No tasks yet')

    elif page == 'Reports':
        st.title('📈 Reports')
        dfp = list_projects()
        if not dfp.empty:
            st.write('**Projects by Member**')
            pm = dfp.explode('members')['members'].value_counts()
            st.bar_chart(pm)
        dt = list_tasks()
        if not dt.empty:
            rate = dt['completed'].mean()
            st.metric('Overall Task Completion Rate', f"{rate:.0%}")
        else:
            st.info('No tasks to report')
