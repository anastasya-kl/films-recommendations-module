import sys
sys.path.insert(0, 'modules')
#-----------------------------------------------------
import streamlit as st
from account_module import *
from reccomendation_module import show_reccomendations, get_saves
#-----------------------------------------------------

st.markdown("# Акаунт")
st.sidebar.markdown("# Акаунт")

if 'inac' not in st.session_state or st.session_state['inac'] is False: inac = False
else: inac = True

if not inac:
    st.write('Увійдіть в акаунт, щоб ми могли запам\'ятати Ваші вподобання')
    tab1, tab2 = st.tabs(["Вхід", "Реєстрація"])

    with tab1:
        c1, c2 = st.columns(2)

        with c1:
            nickname = st.text_input("Нікнейм", value="")
        with c2:
            password = st.text_input("Пароль", type="password", value="")

        if st.button("Увійти"):
            hashed_password = hash_password(password)
            if password == "" or nickname=="": st.error('Будь ласка, заповніть усі поля')
            else: res=login(nickname, hashed_password)

    with tab2:
        st.subheader("Зареєструйтеся, щоб продовжити")
        c1, c2 = st.columns(2)

        with c1:
            nickname = st.text_input("Нікнейм (не менше 4 символів)", value="")
            if nickname!="" and (len(nickname))<4: st.error("Логін має мати не менше 4 символів")
            birthday = date_input("Дата народження (YYYY-MM-DD)")

        with c2:
            password = st.text_input("Пароль (не менше 6 символів)", type="password", value="")
            if password!="" and (len(password))<6: st.error("Пароль має мати не менше 6 символів")
            selected_option = st.selectbox("Стать", ["male", "female"], index=0)

        if st.button("Зареєструватися"):
            if len(nickname)<4 or len(password)<6 or birthday is None: pass
            else:
                hashed_password = hash_password(password)
                gender = selected_option
                res = register(nickname, hashed_password, gender, birthday)
else:
    st.subheader(st.session_state['nickname'])
    saves = get_saves(st.session_state['id'])
    show_reccomendations(saves)
    
