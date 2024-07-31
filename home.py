import sys
sys.path.insert(0, 'modules')

#-----------------------------------------------------
import streamlit as st
import requests 
from streamlit_lottie import st_lottie
from home_module import *
#-----------------------------------------------------

st.markdown("# Домашня 🎈")
st.sidebar.markdown("# Домашня 🎈")
with st.container():
    st.title('FLUX')
    st.subheader('The perfect match for your next watch')
    with st.container():
        #st.write("---")
        left_column, right_column = st.columns(2)
        with left_column:
            st.header("Які можливості FLUX?")
            st.write("##")
            st.write("""
                     Наш ресурс може:
                     - надати інформацію по більш ніж 7000 фільмів і серіалів
                     - порекомендувати фільми, що точно зацікавлять😉
                     - створити список обраного матеріалу
                     """)
        with right_column:
            lottie_coding = loadLotiieUrl("https://lottie.host/6a99d2c6-20ee-401d-ab1d-c1f2f7433e8f/ZIiBqeIZS8.json")
            st_lottie(lottie_coding, height=500, key='coding')

#-----------------------------------------------------
