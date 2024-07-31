import streamlit as st
import sqlite3 as sq
import hashlib
import time
from datetime import datetime
from session import *
#-----------------------------------------------------
# перевірка формату дати
def date_input(label, key=None):
    date_str = st.text_input(label, key=key, value="")
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj
    except ValueError:
        if date_str != "":
            st.error("Неправильний формат дати. Використовуйте YYYY-MM-DD.")
        return None

# обрахунок віку на основі дати народження
def calculate_age(birthdate_str):
    try: 
        birthdate_str = birthdate_str.split()[0]
        birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d")
    except: birthdate = birthdate_str
    current_date = datetime.now()
    age = current_date.year - birthdate.year - ((current_date.month, current_date.day) < (birthdate.month, birthdate.day))
    return age

# хешування паролю
def hash_password(password):
    sha256 = hashlib.sha256()
    sha256.update(password.encode('utf-8'))
    return sha256.hexdigest()
    
# реєстрація у базі даних                
def register(nickname, password, gender, birthday, dbname = 'fluxmain.db'):
    try:
        with sq.connect(dbname) as con:
            cur = con.cursor()
            
            cur.execute('SELECT nickname FROM user WHERE nickname = ?', (nickname,))
            result = cur.fetchone()
            if result: 
                st.error("Ім'я користувача вже існує")
                return False
            else:
                try:
                    cur.execute('''
                        INSERT INTO user (nickname, password, gender, birthday)
                        VALUES (?, ?, ?, ?)
                    ''', (nickname, password, gender, birthday))
                    con.commit()
                    cur.execute('SELECT id FROM user WHERE nickname = ?', (nickname,))
                    user_id = cur.fetchone()[0]
                    save_session(user_id, nickname, gender, calculate_age(birthday), None)
                    st.success('Ви успішно зареєструвалися')
                    return True  
                except Exception as e:
                    st.error("Помилка при зверненні до бази даних")
                    return False
    except Exception as e:
        st.error("Помилка підключення до сервера")
        return False

# вхід у базу даних  
def login(nickname, password, dbname='fluxmain.db'):
    try:
        with sq.connect(dbname) as con:
            cur = con.cursor()

            cur.execute('SELECT id FROM user WHERE nickname = ? AND password = ?', (nickname, password))
            user_id = cur.fetchone()

            if not user_id: 
                st.error(f"Логін або пароль введені неправильно")
                return False
            else: 
                response = cur.execute('''SELECT nickname, gender, birthday, table_id FROM user WHERE id = ?''', (user_id[0],)).fetchone()
                st.success('Ви успішно увійшли')
                save_session(user_id[0], response[0], response[1], calculate_age(response[2]), response[3])
    except Exception as e:
        st.error(f"Помилка підключення до бази даних: {e}")
        return None
    return True