import sys
sys.path.insert(0, 'modules')
#-----------------------------------------------------
import streamlit as st
from reccomendation_module import *

st.markdown("# Пошук фільмів")
st.sidebar.markdown("# Пошук фільмів")

genres = get_genres()
start_years = get_start_years()
types = ['movie', 'series']
#------------------ Пошук за назвою ------------------
try:
    search_query = st.text_input("Введіть запит пошуку")
    if st.button("Шукати"):
        with st.expander("Результати", expanded=True):
            if search_query:
                ids = search_films(search_query)
                if ids: show_reccomendations(ids)
                else: st.write("Нічого не знайдено.")
        search_query = st.text_input("Введіть запит пошуку")
except:
    pass
selected_option = st.selectbox("Пошук фільмів", ["Пошук по фільтрам", "Популярні"], index=0)
#------------------ Пошук за фільтрами ------------------   

#st.checkbox('hello', key='hello', on_change=None)
if selected_option == "Пошук по фільтрам":
    with st.expander("Пошук по фільтрам", expanded=True):
        with st.container():
            st.write(""" Оберіть тип """)
            c1, c2 = st.columns(2)
            chunk_size = len(types) // 2
            types_chunked = [types[i:i + chunk_size] for i in range(0, len(types), chunk_size)]
            selected_types = []
            with c1:
                selected_types.extend(st.checkbox(genre, key=f'type_checkbox_{genre}') for genre in types_chunked[0])
            with c2:
                selected_types.extend(st.checkbox(genre, key=f'type_checkbox_{genre}') for genre in types_chunked[1])

        # жанр 
        with st.container():
            st.write(""" Оберіть жанри """)
            c1, c2, c3, c4 = st.columns(4)
            chunk_size = len(genres) // 4 + 1
            genres_chunked = [genres[i:i + chunk_size] for i in range(0, len(genres), chunk_size)]
            selected_genres = []

            with c1:
                selected_genres.extend(st.checkbox(genre, key=f'genre_checkbox_{genre}') for genre in genres_chunked[0])

            with c2:
                selected_genres.extend(st.checkbox(genre, key=f'genre_checkbox_{genre}') for genre in genres_chunked[1])

            with c3:
                selected_genres.extend(st.checkbox(genre, key=f'genre_checkbox_{genre}') for genre in genres_chunked[2])

            with c4:
                selected_genres.extend(st.checkbox(genre, key=f'genre_checkbox_{genre}') for genre in genres_chunked[3])

        # роки 
        with st.container():
            st.write("""
                Виберіть роки фільмів, які вас цікавлять
            """)
            c1, c2, c3, c4 = st.columns(4)
            chunk_size = len(start_years) // 4 + 1
            years_chunked = [start_years[i:i + chunk_size] for i in range(0, len(start_years), chunk_size)]
            selected_years = []

            with c1:
                selected_years.extend(st.checkbox(f"{year[0]}-{year[1]}", key=f'year_checkbox_{year[0]}_{year[1]}') for year in years_chunked[0])

            with c2:
                selected_years.extend(st.checkbox(f"{year[0]}-{year[1]}", key=f'year_checkbox_{year[0]}_{year[1]}') for year in years_chunked[1])

            with c3:
                selected_years.extend(st.checkbox(f"{year[0]}-{year[1]}", key=f'year_checkbox_{year[0]}_{year[1]}') for year in years_chunked[2])

            with c4:
                selected_years.extend(st.checkbox(f"{year[0]}-{year[1]}", key=f'year_checkbox_{year[0]}_{year[1]}') for year in years_chunked[3])
        
        # обробка пошуку
        button = st.button("Далі")
        if button:
            rtypes = [genre for genre, selected in zip(types, selected_types) if selected]
            rgenres = [genre for genre, selected in zip(genres, selected_genres) if selected]
            ryears = [year for year, selected in zip(start_years, selected_years) if selected]

            response = search({'rtypes':rtypes, 'rgenres':rgenres, 'ryears':ryears})
            with st.container(): show_reccomendations(response)

else:
    with st.expander("Популярні:", expanded=True):
        ids = get_high_rated_films()
        show_reccomendations(ids)