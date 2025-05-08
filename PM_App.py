import streamlit as st
import pandas as pd
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
    .stApp { background-color: #f7f9fc; }
    .css-1d391kg { background-color: #ffffff; }
    .stMetric > div { background-color: #ffffff; border-radius: 8px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True
)

# --- Session State Initialization ---
for key, default in [('logged_in', False), ('user', ''), ('projects', {}), ('tasks', {}), ('project_counter', 0), ('task_counter', 0)]:
    if key not in st.session_state:
        st.session_state[key] = default

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
    st.session_state['projects'][pid] = {'id':pid,'name':name,'description':desc,'start_date':start,'end_date':end,'status':'Not Started','members':members,'created_by':st.session_state['user'],'created_at':datetime.now()}
    st.success(f"Project '{name}' added (ID: {pid})")

def delete_project(pid):
    st.session_state['projects'].pop(pid, None)
    st.session_state['tasks'] = {tid:t for tid,t in st.session_state['tasks'].items() if t.get('project_id')!=pid}
    st.success(f"Project {pid} deleted")

def update_project_status(pid, status):
    if pid in st.session_state['projects']:
        st.session_state['projects'][pid]['status'] = status
        st.success(f"Project {pid} set to {status}")

# --- Task Management ---
def add_task(pid, title, due, assignee, status):
    if pid in st.session_state['projects']:
        tid = next_task_id()
        st.session_state['tasks'][tid] = {'id':tid,'project_id':pid,'title':title,'due_date':due,'assignee':assignee,'status':status,'created_at':datetime.now()}
        st.success(f"Task '{title}' added (ID: {tid}) to {pid}")
    else:
        st.error('Invalid project selected')

def update_task(tid, field, value):
    if tid in st.session_state['tasks'] and field in st.session_state['tasks'][tid]:
        st.session_state['tasks'][tid][field] = value
        st.success(f"Task {tid} updated: {field} set to {value}")
    else:
        st.error('Invalid task or field')

# --- Data Accessors ---
def get_projects_df():
    return pd.DataFrame(st.session_state['projects'].values()) if st.session_state['projects'] else pd.DataFrame()

def get_tasks_df():
    df = pd.DataFrame(st.session_state['tasks'].values()) if st.session_state['tasks'] else pd.DataFrame()
    if not df.empty and 'due_date' in df:
        df['due_date'] = pd.to_datetime(df['due_date'])
    return df

# --- Reporting ---
def project_metrics():
    df = get_projects_df()
    base = ['Not Started','In Progress','On Hold','Completed']
    return df['status'].value_counts().reindex(base, fill_value=0) if 'status' in df else pd.Series(0,index=base)

def task_metrics():
    df = get_tasks_df()
    base = ['To Do','In Progress','Blocked','Completed']
    return df['status'].value_counts().reindex(base, fill_value=0) if 'status' in df else pd.Series(0,index=base)

def upcoming_deadlines(days=7):
    today = date.today()
    return [p for p in st.session_state['projects'].values() if p.get('end_date') and (p['end_date']-today).days<=days]

# --- Main UI ---
if not st.session_state['logged_in']:
    login_page()
else:
    st.sidebar.header(f"👤 {st.session_state['user']}")
    menu = st.sidebar.radio('Navigation',['Dashboard','Projects','Tasks','Reports','Logout'])

    if menu=='Logout':
        st.session_state['logged_in']=False
        st.session_state['user']=''
        st.experimental_rerun()

    if menu=='Dashboard':
        st.header('📊 Dashboard')
        proj_counts=project_metrics()
        task_counts=task_metrics()
        df_tasks=get_tasks_df()
        overdue=df_tasks[df_tasks['due_date']<pd.Timestamp(date.today())] if 'due_date' in df_tasks.columns else pd.DataFrame()
        upcoming=upcoming_deadlines()

        c1,c2,c3,c4=st.columns(4)
        c1.metric('Total Projects',proj_counts.sum())
        c2.metric('In Progress',proj_counts.get('In Progress',0))
        c3.metric('Total Tasks',task_counts.sum())
        c4.metric('Overdue Tasks',len(overdue))

        st.subheader('Project Status Distribution')
        st.bar_chart(proj_counts)
        st.subheader('Task Status Distribution')
        st.bar_chart(task_counts)
        st.subheader('Upcoming Deadlines')
        if upcoming:
            st.table(pd.DataFrame(upcoming)[['id','name','end_date']].rename(columns={'id':'ID','name':'Project','end_date':'Ends'}))
        else:
            st.info('No upcoming deadlines')

    elif menu=='Projects':
        st.header('📁 Projects')
        with st.expander('➕ Add New Project'):
            name=st.text_input('Name')
            desc=st.text_area('Description')
            start=st.date_input('Start Date')
            end=st.date_input('End Date')
            members=st.multiselect('Members',['Alice','Bob','Charlie','Dana'])
            if st.button('Create Project'):
                add_project(name,desc,start,end,members)
        dfp=get_projects_df()
        if not dfp.empty:
            st.table(dfp.set_index('id')[['name','status','start_date','end_date']].rename(columns={'name':'Name','start_date':'Start','end_date':'End','status':'Status'}))
            sel=st.selectbox('Select Project',options=dfp['id'],format_func=lambda x:f"{x} - {st.session_state['projects'][x]['name']}")
            new_stat=st.selectbox('Change Status',['Not Started','In Progress','On Hold','Completed'],key='proj_status')
            if st.button('Update Project Status'):
                update_project_status(sel,new_stat)
            if st.button('Delete Project'):
                delete_project(sel)
        else:
            st.info('No projects available')

    elif menu=='Tasks':
        st.header('✅ Tasks')
        with st.expander('➕ Add New Task'):
            dproj=get_projects_df()
            if not dproj.empty:
                pid=st.selectbox('Project',options=dproj['id'],format_func=lambda x:f"{x} - {st.session_state['projects'][x]['name']}")
                title=st.text_input('Task Title')
                due=st.date_input('Due Date')
                assignee=st.selectbox('Assignee',['Alice','Bob','Charlie','Dana'])
                status=st.selectbox('Status',['To Do','In Progress','Blocked','Completed'])
                if st.button('Add Task'):
                    add_task(pid,title,due,assignee,status)
            else:
                st.info('Create a project first')
        dft=get_tasks_df()
        if not dft.empty:
            st.table(dft.set_index('id')[['project_id','title','assignee','status','due_date']].rename(columns={'project_id':'Project','title':'Title','assignee':'Assignee','due_date':'Due'}))
            tid=st.selectbox('Select Task',options=dft['id'])
            new_tstat=st.selectbox('Update Status',['To Do','In Progress','Blocked','Completed'],key='task_status')
            if st.button('Update Task'):
                update_task(tid,'status',new_tstat)
        else:
            st.info('No tasks available')

    elif menu=='Reports':
        st.header('📈 Reports')
        proj_counts=project_metrics()
        task_counts=task_metrics()
        st.subheader('Projects by Status')
        st.bar_chart(proj_counts)
        st.subheader('Tasks by Status')
        st.bar_chart(task_counts)
        rate=task_counts.get('Completed',0)/task_counts.sum() if task_counts.sum() else 0
        st.metric('Task Completion Rate',f"{rate:.0%}")
