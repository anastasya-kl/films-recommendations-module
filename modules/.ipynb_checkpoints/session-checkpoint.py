import streamlit as st

def save_session(user_id, nickname, gender, age, table, password=None):
    st.session_state['id'] = user_id
    st.session_state['nickname'] = nickname
    st.session_state['gender'] = gender
    st.session_state['age'] = age
    st.session_state['table'] = table
    st.session_state['inac'] = True
    
def reset_session():
    st.session_state['id'] = None
    st.session_state['nickname'] = None
    st.session_state['gender'] = None
    st.session_state['age'] = None
    st.session_state['table'] = None
    st.session_state['inac'] = False
