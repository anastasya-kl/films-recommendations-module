from session import *
import streamlit as st
import sqlite3 as sq
from collections import defaultdict
import time
import math

unique = 0
def up_unique():
    global unique;
    unique += 1
    return unique
# ------ робота з базою даних ------

# пошук фільмів на основі фільтрації
def search(data):
    rtypes = data['rtypes']
    rgenres = data['rgenres']
    ryears = data['ryears']

    bound = 5.0  # Мінімальний рейтинг для фільмів
    idgenres = convert_genres(rgenres)

    # Отримуємо фільми, що відповідають жанрам
    matchedFilms = get_matching_films(idgenres, dbname="fluxmain.db")
    matchedFilms2, matchedFilms3 = {}, {}

    # Фільтруємо за роками
    for key in matchedFilms:
        matchedFilms2[key] = get_films_by_years_and_ids(ryears, matchedFilms[key])

    # Фільтруємо за типами (фільм/серіал)
    for key in matchedFilms2:
        matchedFilms3[key] = get_filtered_film_ids(rtypes, matchedFilms2[key])
        
    final_result = []
    # Сортуємо фільми за рейтингом
    for key in matchedFilms3:
        final_result += sort_films_by_rates(matchedFilms3[key], bound)
        
    # Якщо результатів менше 100, розширюємо пошук
    if len(final_result) < 100:
        final_result = []
        # Повторно сортуємо за рейтингом, ігноруючи фільтр типів
        for key in matchedFilms2:
            final_result += sort_films_by_rates(matchedFilms2[key], bound)

    # Якщо все ще менше 100, ще більше розширюємо пошук
    if len(final_result) < 100:
        # Сортуємо за рейтингом, ігноруючи фільтри типів та років
        for key in matchedFilms:
            final_result += sort_films_by_rates(matchedFilms[key], bound)

    # Обмежуємо результат до 100 фільмів
    limit = 100 if len(final_result) >= 100 else len(final_result)
    return final_result[:limit]

# дістати коди жанрів
def convert_genres(rgenres, dbname="fluxmain.db"):
    try:
        with sq.connect(dbname) as con:
            cur = con.cursor()
            cur.execute(
                'SELECT id FROM genres WHERE name IN ({})'.format(','.join(['?'] * len(rgenres))),
                rgenres)
            result = cur.fetchall()
            for i in range(len(result)): result[i] = result[i][0]
            return result
    except Exception as e:
        st.error(f"Помилка підключення до сервера: {e}")
        return False
    
# вибрати фільми за жанрами у порядку кількості зівпадінь
def get_matching_films(idgenres, dbname="fluxmain.db"):
    try:
        with sq.connect(dbname) as con:
            cur = con.cursor()
            
            sql_query = """
                SELECT filmId, COUNT(*) AS match_count
                FROM filmsGenres
                WHERE genreId IN ({})
                GROUP BY filmId
                HAVING COUNT(*) > 0
                ORDER BY match_count DESC
            """.format(','.join(['?'] * len(idgenres)))

            cur.execute(sql_query, idgenres)
            result = cur.fetchall()
            result_dict = {}

            for item in result:
                count = item[1]
                if count not in result_dict: result_dict[count] = [item[0]]
                else: result_dict[count].append(item[0])
            return result_dict
    except Exception as e:
        st.error(f"Помилка підключення до сервера: {e}")
        return False
    
# отримати код фільмів які підходять під задані роки
def get_films_by_years_and_ids(ryears, film_ids, dbname="fluxmain.db"):
    try:
        with sq.connect(dbname) as con:
            cur = con.cursor()
            films_with_years_and_ids = []
            for pair in ryears:
                cur.execute("""
                    SELECT id
                    FROM films
                    WHERE start_year BETWEEN ? AND ?
                        AND id IN ({})
                """.format(','.join(['?'] * len(film_ids))), (pair[0], pair[1]) + tuple(film_ids))

                for i in cur.fetchall():
                    films_with_years_and_ids.append(i[0])
            return films_with_years_and_ids
    except Exception as e:
        st.error(f"Помилка підключення до сервера: {e}")
        return False
    
# фільтрація фільмів за типами
def get_filtered_film_ids(rtypes, matched_films, dbname="fluxmain.db"):
    try:
        with sq.connect(dbname) as con:
            cur = con.cursor()
            filtered_film_ids = []
            cur.execute(
                """
                SELECT id
                FROM films
                WHERE id IN ({})
                    AND type IN ({})
                """.format(','.join(['?'] * len(matched_films)), ','.join(['?'] * len(rtypes))),
                matched_films + rtypes)
            for i in cur.fetchall(): filtered_film_ids.append(i[0])
            
            return filtered_film_ids
    except Exception as e:
        st.error(f"Помилка підключення до сервера: {e}")
        return False
    
# сортування фільмів за рейтингом    
def sort_films_by_rates(filtered_film_ids, bound, dbname="fluxmain.db"):
    try:
        with sq.connect(dbname) as con:
            cur = con.cursor()
            cur.execute("""
                SELECT id, rates
                FROM films
                WHERE id IN ({}) AND rates >= ?
                """.format(','.join(['?'] * len(filtered_film_ids))),
                tuple(filtered_film_ids) + (bound,)
            )
            sorted_films = sorted(cur.fetchall(), key=lambda x: x[1], reverse=True)
            result = [film[0] for film in sorted_films]

            return result
    except Exception as e:
        st.error(f"Помилка підключення до сервера: {e}")
        return False
    
# знайти недавні високорейтингові фільми    
def get_high_rated_films(dbname="fluxmain.db"):
    try:
        with sq.connect(dbname) as con:
            cur = con.cursor()
            cur.execute("""
                SELECT id
                FROM films
                WHERE rates >= 7.5
                ORDER BY start_year DESC, rates DESC
            """)
            result = [row[0] for row in cur.fetchall()]
            return result[:100]
    except Exception as e:
        print(f"Помилка підключення до бази даних: {e}")
        return None

# отримання всієї інформації про фільми    
def get_reccomendations(ids, dbname="fluxmain.db"):
    try:
        with sq.connect(dbname) as con:
            cur = con.cursor()

            cur.execute("""
                SELECT id, caption, start_year, end_year, rates, duration, description, type
                FROM films
                WHERE id IN ({})
                """.format(','.join(['?'] * len(ids))),
                tuple(ids)
            )

            films_data_dict = {film[0]: dict(zip(["caption", "start_year", "end_year", "rates", "duration", "description", "type"], film[1:])) for film in cur.fetchall()}

            cur.execute("""
                SELECT filmId, genreId
                FROM filmsGenres
                WHERE filmId IN ({})
                """.format(','.join(['?'] * len(ids))),
                tuple(ids)
            )
            films_genres_dict = defaultdict(list)
            for film_id, genre_id in cur.fetchall():
                films_genres_dict[film_id].append(genre_id)

            cur.execute("""
                SELECT id, name
                FROM genres
                """)
            
            genres_dict = dict(cur.fetchall())
            for film_id, genres in films_genres_dict.items():
                films_data_dict[film_id]["genres"] = [genres_dict[genre_id] for genre_id in genres]
            
            sorted_films_data_dict = dict(sorted(films_data_dict.items(), key=lambda x: ids.index(x[0])))
            return sorted_films_data_dict
    except Exception as e:
        st.error(f"Помилка підключення до сервера: {e}")
        return None
    
# перевірка наявності запису в таблиці збережених користувача
def is_saved(user_id, film_id, dbname="fluxmain.db"):
    try:
        with sq.connect(dbname) as con:
            cur = con.cursor()

            
            cur.execute('SELECT * FROM saves WHERE user_id = ? AND film_id = ?', (user_id, film_id))
            existing_row = cur.fetchone()
            if existing_row: return 1
            else: return 0
    except Exception as e:
        st.error(f'Не можливо дістати дані: {e}')
        return None

# додати/видалити фільм у збережені користувача
def process_save(user_id, film_id, dbname="fluxmain.db"):
    try:
        with sq.connect(dbname) as con:
            cur = con.cursor()
            cur.execute('SELECT * FROM saves WHERE user_id = ? AND film_id = ?', (user_id, film_id))
            existing_row = cur.fetchone()

            if existing_row:
                cur.execute('DELETE FROM saves WHERE user_id = ? AND film_id = ?', (user_id, film_id))
            else:
                cur.execute('INSERT INTO saves (user_id, film_id) VALUES (?, ?)', (user_id, film_id))
            con.commit()
            return True
    except Exception as e:
        st.error(f'Помилка підключення до бази даних: {e}')
        return False

# отримати збережені користувача
def get_saves(user_id, dbname="fluxmain.db"):
    try:
        with sq.connect(dbname) as con:
            cur = con.cursor()
            cur.execute('SELECT film_id FROM saves WHERE user_id = ?', (user_id,))
            existing_row = cur.fetchall()
            if existing_row is not None:
                result = [i[0] for i in existing_row]
                return result
            return None
    except Exception as e:
        print(f'Помилка підключення до бази даних: {e}')
        return None
    
# пошук фільмів за назвою
def search_films(query):
    try:
        with sq.connect("fluxmain.db") as con:
            cur = con.cursor()
            cur.execute("SELECT id FROM films WHERE caption LIKE ?", ('%' + query + '%',))
            results = [i[0] for i in cur.fetchall()]
            return results
    except Exception as e:
        print(f"Помилка підключення до бази даних: {e}")
        return None

    
# дістати список словників, де записані частота зустрічання жанрів та відсортовані по рейтингу для них фільми
def get_top_rated_films(genre_counts, dbname="fluxmain.db"):
    try:
        with sq.connect(dbname) as con:
            cur = con.cursor()

            # Створюємо словник для зберігання результатів
            result_dict = {}

            # Проходимося по жанрам та вибираємо фільми з бази даних
            for genre_id, count in genre_counts.items():
                # SQL-запит для отримання фільмів за кодом жанру
                cur.execute("""
                    SELECT id
                    FROM films
                    JOIN filmsGenres ON films.id = filmsGenres.filmId
                    WHERE filmsGenres.genreId = ?
                    ORDER BY rates DESC
                """, (genre_id,))

                # Отримуємо результат запиту
                films = [film[0] for film in cur.fetchall()]

                # Перевіряємо, чи є фільми для поточного жанру
                if films:
                    # Додаємо фільми до словника за ключем (жанром)
                    result_dict[genre_id] = films

            return result_dict

    except Exception as e:
        st.error(f"Помилка підключення до сервера: {e}")
        return None

# дістати код і токени для цільового фільму та для решти записів
def split_films_data(fid, dbname="fluxmain.db"):
    try:
        with sq.connect(dbname) as con:
            cur = con.cursor()
            cur.execute("""
                SELECT id, tokens
                FROM films
            """)

            all_films_data = cur.fetchall()
            film_data_dict = {}
            other_films_data_dict = {}

            for film_id, tokens in all_films_data:
                if film_id == fid:
                    if tokens is not None:
                        film_data_dict[film_id] = tokens.split()
                    else: return None, None
                elif tokens is not None:
                    other_films_data_dict[film_id] = tokens.split()

            return film_data_dict, other_films_data_dict
        
    except Exception as e:
        st.error(f"Помилка підключення до бази даних: {e}")
        return None, None

# дістаємо коди у порядку спадання кількості входжень токенів
def find_most_similar_with_intersections(film_data, other_films_data):
    current_values = next(iter(film_data.values()))
    similar_key_pairs = []

    for key, values in other_films_data.items():
        intersection = len(set(values).intersection(set(current_values)))
        if intersection != 0: 
            similar_key_pairs.append((key, intersection))

    similar_key_pairs.sort(key=lambda x: x[1], reverse=True)
    return [film_id for film_id, _ in similar_key_pairs]

# отримати список жанрів
def get_genres(dbname="fluxmain.db"):
    try:
        with sq.connect(dbname) as con:
            cur = con.cursor()
            cur.execute(
                "SELECT name FROM genres;")
            result = cur.fetchall()
            for i in range(len(result)): result[i] =result[i][0]
            return result
    except Exception as e:
        print(f"Помилка підключення до сервера: {e}")
        return False
    
# ------ робота виводом даних ------

# дістати співвідношення виводу контенту
def sort_and_limit_dict(input_dict, limit = 100):
    sorted_dict = dict(sorted(input_dict.items(), key=lambda x: x[0], reverse=True))
    total_values = sum(key for key in sorted_dict)

    result = []
    it = list(sorted_dict.keys())[:-1]
    for key in it:
        value = math.ceil(key/total_values*100)
        n = len(sorted_dict[key])
        value = n if value > n else value
        result.append(value)
    value = (100-sum(result))
    n = len(sorted_dict[list(sorted_dict.keys())[-1]]) 
    value = n if value > n else value
    result.append(value)
    return result

# видаляє дублікати для формату повернених даних функції get_top_rated_films
def remove_duplicates(input_dict):
    result = {}
    used_items = set()
    for key, items in input_dict.items():
        new_items = []
        for item in items:
            if item not in used_items:
                new_items.append(item)
                used_items.add(item)
        result[key] = new_items
    return result

# видаляє дублікати для формату даних із remove_duplicates які є у saves
def remove_if_used(input_dict, saves):
    result = {}
    
    for key, values in input_dict.items():
        filtered = []
        for value in values:
            if value not in saves:
                filtered.append(value)
                
        result[key] = filtered
        
    return result

# перетворити хвилин у формат: години h хвилини m
def format_minutes(minutes):
    hours = minutes // 60
    remaining_minutes = minutes % 60
    formatted_time = f"{hours}h {remaining_minutes}m"
    return formatted_time
    
# отримати поділ років для фільтрації
def get_start_years(dbname="fluxmain.db"):
    try:
        with sq.connect(dbname) as con:
            cur = con.cursor()
            cur.execute(
                "SELECT start_year FROM films;")
            result = cur.fetchall()
            for i in range(len(result)): result[i] =result[i][0]
            unique_years = sorted(set(result))
            unique_years = [year for year in unique_years if year <= 2023]
            min_year = min(unique_years)
            max_year = max(unique_years)
            grouped_years = []
            step = 10
            current_year = min_year
            while current_year < max_year:
                end_year = min(current_year + step , max_year)
                grouped_years.append([current_year, end_year])
                current_year = end_year 
            return grouped_years
    except Exception as e:
        print(f"Помилка підключення до сервера: {e}")
        return False

def show_reccomendations(ids):
    data = get_reccomendations(ids)
    view = []
    for key in data: view.append(data[key])
    idss = [key for key in data]
    
    keys = [i for i in idss]
    for f_id in data: 
        
        c1, c2 = st.columns(2)
        with c1:
            try:
                style(data[f_id], f_id)
            except:
                continue
        with c2:
            film_data, other_films_data = split_films_data(f_id)
            if film_data is not None and other_films_data is not None:
                similiar_ids = find_most_similar_with_intersections(film_data, other_films_data)
                if len(similiar_ids) != 0:
                    similiar_data = get_reccomendations(similiar_ids)
                    l=0
                    for i in similiar_data:
                        if l > 3: break
                        short_style(similiar_data[i])
                        l+=1
        st.write("---")

# відображення конкретного фільму
def style(r, counter=None):
    info_block = ''
    info_block += f"{r['type']}"
    if r['end_year']: info_block += f" • {r['start_year']}-{r['end_year']}"
    else: info_block += f" • {r['start_year']}"
    if r['duration']: info_block +=f" • {format_minutes(r['duration'])}"
    if r['rates']: info_block += f" • {r['rates']}"
    st.subheader(r['caption'])
    try:
        html_code = ""
        for genre in r['genres']:
            html_code +=f"""
            <span style="display: inline-block; 
                         padding: 5px 10px; 
                         background-color: #ddd; 
                         border-radius: 10px; 
                         margin: 2px;">{genre}</span>
            """
        html_code=html_code.replace('\n', '')
        html_code = f"""<div style="display: flex;">""" + html_code + f"""</div>"""
        st.markdown(html_code, unsafe_allow_html=True)
    except: pass
    
    st.write(info_block)
    if r['description'] is not None: st.write(f"{(r['description'])}")
    if 'inac' in st.session_state and st.session_state['inac'] and counter:        
        label = is_saved(st.session_state['id'], counter)
        labels = ['Зберегти', 'Видалити']
        button_c = st.empty()
        button1 = button_c.button(labels[label], key=counter)
        if button1 and process_save(st.session_state['id'], counter):
            label = 0 if label == 1 else 1
            button_c.empty()
            button2 = button_c.button(labels[label], key=-counter)
    
# відображення конкретного фільму
def short_style(r):
    st.markdown(f"""
        <p style="font-size: 20px; font-weight: bold; padding:0; padding-top: 5px; margin:0;">{r['caption']}</p>
        """, unsafe_allow_html=True)
    try:
        genres_block = ''
        for genre in r['genres']: genres_block += genre + ' • '
        genres_block = genres_block[:-2]
        st.markdown(f"""
        <p style="font-size: 12px; padding: 0; padding-top: 5px; margin:0;">{genres_block}</p>
        """, unsafe_allow_html=True)
    except: pass
    
    info_block = ''
    info_block += f"{r['type']}"
    if r['end_year']: info_block += f" • {r['start_year']}-{r['end_year']}"
    else: info_block += f" • {r['start_year']}"
    if r['duration']: info_block +=f" • {format_minutes(r['duration'])}"
    if r['rates']: info_block += f" • {r['rates']}"
    st.markdown(f"""
        <p style="font-size: 12px; padding: 0; padding-top: 5px; margin:0;">{info_block}</p>
        """, unsafe_allow_html=True)
    st.write("---")
    
# ------ кластеризація ------
from account_module import calculate_age
from datetime import datetime
import os
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np
import math
from sklearn.cluster import KMeans
from collections import Counter

# дістати кількість зустрічань жанрів у списку фільмів за id
def count_genre_occurrences(ids, dbname="fluxmain.db"):
    try:
        with sq.connect(dbname) as con:
            cur = con.cursor()

            # SQL-запит для отримання жанрів та їх кількості
            cur.execute("""
                SELECT g.id, COUNT(*) as count
                FROM filmsGenres fg
                JOIN genres g ON fg.genreId = g.id
                WHERE fg.filmId IN ({})
                GROUP BY g.name
            """.format(','.join(['?'] * len(ids))),
            tuple(ids))

            # Створення словника з результатами
            genre_count_dict = dict(cur.fetchall())
            
            return genre_count_dict

    except Exception as e:
        st.error(f"Помилка підключення до сервера: {e}")
        return None

# Встановлюємо змінну середовища OMP_NUM_THREADS
os.environ["OMP_NUM_THREADS"] = "1"

# інформація про користувачів для кластеризації
def users_analysis(dbname="fluxmain.db"):
    try:
        with sq.connect(dbname) as con:
            analysis_info = {}
            cur = con.cursor()
            cur.execute('SELECT id, birthday, gender FROM user')
            r = cur.fetchall()
            users_info = {'male':[], 'female':[]}
            for user in r:
                saves = get_saves(user[0])
                if not saves: continue
                genres_counts = count_genre_occurrences(saves)
                users_info[user[2]].append({
                    'id':user[0],
                    'age':calculate_age(user[1]),
                    'genres':genres_counts
                })
            return users_info
    except Exception as e:
        st.error(f'Помилка підключення до бази даних: {e}')
        return None

# визначити кількість кластерів
def get_k(data):
    if len(data) > 0 and len(data[0]['genres']) > 0:  # Перевірка, що є хоча б один користувач і хоча б один жанр
        X = np.array([[user['age'], len(user['genres'])] for user in data])

        # Визначення оптимальної кількості кластерів
        inertia_values = []
        possible_k_values = range(1, min(len(data), 11))  # обмежте до кількості користувачів у вашому наборі даних

        for k in possible_k_values:
            kmeans = KMeans(n_clusters=k, random_state=42)
            kmeans.fit(X)
            inertia_values.append(kmeans.inertia_)

        if len(inertia_values) > 1:
            elbow_point = np.argmin(np.diff(inertia_values)) + 1
        else: elbow_point=1
        return elbow_point
    
# кластеризація
def cluster_users(user_data):
    # Знайдемо максимальну кількість жанрів серед всіх користувачів
    max_num_genres = max(len(user['genres']) for user in user_data)
    
    # Доповнимо коротші списки нулями
    X = np.array([[user['age']] + list(user['genres'].values()) + [0] * (max_num_genres - len(user['genres'])) for user in user_data])
    
    #num_clusters = math.ceil(len(user_data) / 5)
    num_clusters = get_k(user_data)
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    clusters = kmeans.fit_predict(X)
    
    for i, user in enumerate(user_data):
        user['cluster'] = clusters[i]
        #st.write(clusters[i])
    return user_data

    
# визначити найпопулярніші дані
def concentrated_data(data):
    counters = [Counter(lst) for lst in data]
    common_elements = list(set(counters[0].keys()) & set(counters[1].keys()))
    common_elements.sort(key=lambda x: counters[0][x] + counters[1][x], reverse=True)
    result_list = common_elements + [element for element in data[0] + data[1] if element not in common_elements]
    return result_list

# визначити рекомендації для користувачів на основі кластерного аналізу
def clustering_analysis(user_id, clusters_info, dbname="fluxmain.db"):
    user_cluster, neighbors_cluster = {}, []
    
    for user in clusters_info:
        if user['id'] == user_id: user_cluster=user
    if len(user_cluster)==0: return None

    for user in clusters_info:
        if user['id'] == user_id: continue
        elif user['cluster'] == user_cluster['cluster']: neighbors_cluster.append(user)
    
    user_saves = get_saves(user_cluster['id'])
    neighbors_saves = [get_saves(user['id']) for user in clusters_info]

    concentrated = concentrated_data(neighbors_saves)
    filtered_concentrated = [element for element in concentrated if element not in user_saves]
    
    return filtered_concentrated