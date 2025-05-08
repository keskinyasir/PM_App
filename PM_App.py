import streamlit as st
import pandas as pd
import uuid
from datetime import date, datetime

# --- Initialize session state ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = ''  # default empty string
if 'projects' not in st.session_state:
    st.session_state.projects = {}
if 'tasks' not in st.session_state:
    st.session_state.tasks = {}

# --- Authentication Functions ---
def authenticate_user(email, password):
    # Basit doğrulama: admin@example.com / password123
    return email == 'admin@example.com' and password == 'password123'

def login_page():
    st.title('🔐 Login')
    email = st.text_input('Email')
    pwd = st.text_input('Password', type='password')
    if st.button('Login'):
        if authenticate_user(email, pwd):
            st.session_state.logged_in = True
            st.session_state.user = email
            st.success('Logged in as ' + email)
            st.experimental_rerun()
        else:
            st.error('Invalid credentials')

# --- Project Management Functions ---
def add_project(name, desc, start, end, members):
    pid = str(uuid.uuid4())
    st.session_state.projects[pid] = {
        'id': pid,
        'name': name,
        'description': desc,
        'start_date': start,
        'end_date': end,
        'status': 'Not Started',
        'members': members,
        'created_by': st.session_state.user,
        'created_at': datetime.now()
    }
    st.success(f'Project "{name}" eklendi')

def edit_project(pid, **updates):
    for key, val in updates.items():
        if key in st.session_state.projects[pid]:
            st.session_state.projects[pid][key] = val
    st.success('Project updated')

def delete_project(pid):
    st.session_state.projects.pop(pid, None)
    # Ayrıca ilgili görevleri sil
    st.session_state.tasks = {tid: t for tid, t in st.session_state.tasks.items() if t['project_id'] != pid}
    st.success('Project deleted')

def list_projects(filter_status=None, assigned_to=None):
    df = pd.DataFrame(st.session_state.projects.values())
    if filter_status:
        df = df[df['status'] == filter_status]
    if assigned_to:
        df = df[df['members'].apply(lambda m: assigned_to in m)]
    return df

def set_project_status(pid, status):
    st.session_state.projects[pid]['status'] = status
    st.success('Status updated')

# --- Task Management Functions ---

def add_task(pid, title, due_date, assignee):
    tid = str(uuid.uuid4())
    st.session_state.tasks[tid] = {
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
    st.session_state.tasks[tid]['completed'] = completed
    st.success('Task status updated')

def list_tasks(pid=None, assignee=None, completed=None):
    df = pd.DataFrame(st.session_state.tasks.values())
    if pid:
        df = df[df['project_id'] == pid]
    if assignee:
        df = df[df['assignee'] == assignee]
    if completed is not None:
        df = df[df['completed'] == completed]
    return df

# --- Reporting Functions ---
def project_summary():
    df = pd.DataFrame(st.session_state.projects.values())
    status_counts = df['status'].value_counts()
    st.subheader('Project Status Count')
    st.bar_chart(status_counts)
    st.write('Total Projects:', len(df))

def upcoming_deadlines(days=7):
    today = date.today()
    upcoming = [p for p in st.session_state.projects.values()
                if (p['end_date'] - today).days <= days]
    return pd.DataFrame(upcoming)

# --- UI Flow ---
if not st.session_state.logged_in:
    login_page()
else:
    # Kullanıcı adı boş değilse göster
    st.sidebar.title(f'👤 {st.session_state.user}')
    page = st.sidebar.selectbox('Menu', [
        'Dashboard', 'Projects', 'Tasks', 'Reports', 'Logout'
    ])

    if page == 'Logout':
        st.session_state.logged_in = False
        st.session_state.user = ''
        st.experimental_rerun()

    elif page == 'Dashboard':
        st.title('📊 Dashboard')
        project_summary()
        st.write('### Upcoming Deadlines (Next 7 days)')
        df_up = upcoming_deadlines()
        st.table(df_up if not df_up.empty else 'No upcoming deadlines')

    elif page == 'Projects':
        st.title('📁 Projects')
        # Add/Edit/Delete Project
        with st.expander('➕ Add Project'):
            name = st.text_input('Name')
            desc = st.text_area('Description')
            start = st.date_input('Start Date')
            end = st.date_input('End Date')
            members = st.multiselect('Members', ['Alice','Bob','Charlie'])
            if st.button('Add'): add_project(name, desc, start, end, members)

        df = list_projects()
        st.table(df)
        # Edit/Delete
        if not df.empty:
            selected = st.selectbox('Select Project to Edit/Delete', df['id'])
            if selected:
                st.write('Editing:', st.session_state.projects[selected]['name'])
                new_status = st.selectbox('Status', ['Not Started','In Progress','Completed'], key='stat')
                if st.button('Update Status'): set_project_status(selected, new_status)
                if st.button('Delete Project'): delete_project(selected)

    elif page == 'Tasks':
        st.title('✅ Tasks')
        with st.expander('➕ Add Task'):
            p_sel = st.selectbox('Project', list(st.session_state.projects.keys()))
            title = st.text_input('Task Title')
            due = st.date_input('Due Date')
            assignee = st.selectbox('Assignee', ['Alice','Bob','Charlie'])
            if st.button('Add Task'): add_task(p_sel, title, due, assignee)

        df_t = list_tasks()
        st.table(df_t)
        if not df_t.empty:
            sel_t = st.selectbox('Select Task', df_t['id'])
            comp = st.checkbox('Completed', st.session_state.tasks[sel_t]['completed'])
            if st.button('Update Task'): update_task_status(sel_t, comp)

    elif page == 'Reports':
        st.title('📈 Reports')
        st.write('**Projects by Member**')
        df = pd.DataFrame(st.session_state.projects.values())
        by_member = df.explode('members')['members'].value_counts()
        st.bar_chart(by_member)
        st.write('**Tasks Completion Rate**')
        df_t = pd.DataFrame(st.session_state.tasks.values())
        if not df_t.empty:
            rate = df_t['completed'].mean()
            st.metric('Completion Rate', f'{rate:.0%}')
        else:
            st.info('No tasks to report')
