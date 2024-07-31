# --------- import modules ---------
from bs4 import BeautifulSoup   
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import re
import datetime
from typing import Optional, Dict, Any
# -----------------------------------------------------------------
movies_url = "https://m.imdb.com/search/title/?explore=genres&title_type=feature"
series_url = "https://m.imdb.com/search/title/?explore=genres&title_type=tv_series,tv_miniseries"
# -----------------------------------------------------------------
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time

# Константи для часто використовуваних селекторів
SHOW_MORE_XPATH = '//button[contains(@class, "ipc-see-more__button")]'
FILM_LINK_CLASS = 'ipc-title-link-wrapper'

def scroll_and_click(driver, i):
    """
    Функція для прокрутки сторінки та кліку на кнопку "Show more"
    
    :param driver: екземпляр веб-драйвера
    :param i: індекс для визначення, до якого елемента прокручувати
    """
    try:
        # Знаходимо елемент для прокрутки
        point = driver.find_element(By.XPATH, f'//li[{i*50}]//a[contains(@class, "ipc-title-link-wrapper")]')
        # Прокручуємо до цього елемента
        driver.execute_script("arguments[0].scrollIntoView()", point)
        time.sleep(5)
        
        # Чекаємо, поки кнопка "Show more" стане клікабельною
        show_more_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, SHOW_MORE_XPATH)))
        # Клікаємо на кнопку
        ActionChains(driver).move_to_element(show_more_button).click().perform()
        time.sleep(10)
    except Exception as e:
        print(f"Помилка при прокрутці та кліку: {e}")

def createLinks(url):
    """
    Основна функція для створення списку посилань на фільми
    
    :param url: URL сторінки для обробки
    :return: список посилань на фільми
    """
    driver = None
    try:
        # Ініціалізуємо веб-драйвер і відкриваємо сторінку
        driver = webdriver.Chrome()
        driver.get(url)

        # Виконуємо прокрутку та клік 6 разів
        for i in range(1, 7):
            scroll_and_click(driver, i)

        # Фінальна прокрутка
        scroll_and_click(driver, 7)

        # Збираємо всі посилання на фільми
        return [a.get_attribute('href') for a in driver.find_elements(By.CLASS_NAME, FILM_LINK_CLASS)]

    except Exception as e:
        print(f"Загальна помилка в createLinks: {e}")
        return []

    finally:
        # Закриваємо драйвер, якщо він був створений
        if driver:
            driver.quit()
            
# -----------------------------------------------------------------
movies_urls_list = createLinks(movies_url)
series_urls_list = createLinks(series_url)
# -----------------------------------------------------------------
#   YEAR
def check_year_format(year_text):
    year_format = re.match(r'^\d{4}(–\d{4})?$', year_text)
    if year_format:
        return True
    
    year_format_partial = re.match(r'^\d{4}–$', year_text)
    if year_format_partial:
        return True
    return False


def parse_year_range(year_str):
    if '–' not in year_str:
        return [int(year_str)]

    start_year, end_year = map(str.strip, year_str.split('–'))

    start_year = int(start_year)

    if not end_year:
        return [start_year, None]
    else:
        end_year = int(end_year)
        return [start_year, end_year]


#   DURATION
def check_time_format(time_str):
    pattern = re.compile(r'^(\d+h)? ?(\d+m)?$')
    return bool(pattern.match(time_str))

def convert_to_minutes(time_str):
    hours, minutes = 0, 0
    if 'h' in time_str:
        hours = int(time_str.split('h')[0])
    if 'm' in time_str:
        minutes = int(time_str.split('m')[0].split()[-1])
    return hours * 60 + minutes

# -----------------------------------------------------------------
def getData(url: str) -> Optional[Dict[str, Any]]:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"Request Error: {e}")
        return None
    
    main_res = {
        'caption': None,
        'start_year': None,
        'end_year': None,
        'duration': None,
        'rates': None,
        'description': None,
        'image': None,
        'genres': None
    }
    
    try:
        if caption := soup.select_one('h1.hero__pageTitle'):
            main_res['caption'] = caption.text.strip()

        if ul := soup.find('ul', class_='ipc-inline-list ipc-inline-list--show-dividers'):
            for li in ul.find_all('li', class_='ipc-inline-list__item'):
                txt = li.text.strip()
                if check_year_format(txt):
                    res = parse_year_range(txt)
                    main_res['start_year'], main_res['end_year'] = res[0], res[1] if len(res) > 1 else None
                elif check_time_format(txt):
                    main_res['duration'] = convert_to_minutes(txt)

        if span_element := soup.select_one('div.sc-acdbf0f3-3 span.sc-bde20123-1'):
            main_res['rates'] = float(span_element.text.strip())

        if description := soup.select_one('p.sc-466bb6c-3 span'):
            main_res['description'] = description.text.strip()

        if image := soup.find('a', class_='ipc-lockup-overlay ipc-focusable'):
            main_res['image'] = image['href']

        if genres_element := soup.select_one('section.sc-9aa2061f-4 div.ipc-chip-list--baseAlt'):
            main_res['genres'] = [a.text.strip() for a in genres_element.find_all('a')]

    except Exception as e:
        print(f'Parsing error: {e}')
    
    required_fields = ['caption', 'start_year', 'description']
    if all(main_res[field] is not None for field in required_fields):
        return main_res
    else:
        return None
    
    dbname = 'fluxmain.db'
    
# -----------------------------------------------------------------
dbname = 'fluxmain.db'

import sqlite3 as sq
with sq.connect(dbname) as con:
    cur = con.cursor()
    
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    nick TEXT NOT NULL,
    email TEXT NOT NULL,
    password TEXT NOT NULL,
    pref_table_id INTEGER
    )""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS films (
    id INTEGER PRIMARY KEY,
    caption TEXT NOT NULL,    
    start_year INTEGER NOT NULL,
    end_year INTEGER,
    duration INTEGER,
    rates FLOAT,
    description TEXT NOT NULL,
    image TEXT
    )""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS genres (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
    )""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS filmsGenres(
    filmId INTEGER NOT NULL,
    genreId INTEGER NOT NULL,
    FOREIGN KEY (filmId) REFERENCES films(id),
    FOREIGN KEY (genreId) REFERENCES genres(id)
    )""")
    
# -----------------------------------------------------------------
import sqlite3 as sq
from typing import List

def insert_content(urls: List[str], dbname: str):
    with sq.connect(dbname) as con:
        cur = con.cursor()
        
        for url in urls:
            try:
                film_data = getData(url)
                if film_data is None: 
                    print(f"Skipping URL {url}: No data retrieved")
                    continue
                
                # Вставка даних про фільм
                sql_query = """
                INSERT INTO films (caption, start_year, end_year, duration, rates, description, image)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                cur.execute(sql_query, (
                    film_data['caption'],
                    film_data['start_year'],
                    film_data['end_year'],
                    film_data['duration'],
                    film_data['rates'],
                    film_data['description'],
                    film_data['image']
                ))
                
                # Отримання ID щойно вставленого фільму
                film_id = cur.lastrowid
                
                # Обробка жанрів
                for genre_name in film_data['genres']:
                    # Спроба вставити жанр, якщо він не існує
                    cur.execute("""
                    INSERT OR IGNORE INTO genres (name)
                    VALUES (?)
                    """, (genre_name,))
                    
                    # Отримання ID жанру
                    cur.execute("SELECT id FROM genres WHERE name = ?", (genre_name,))
                    genre_id = cur.fetchone()[0]
                    
                    # Вставка зв'язку між фільмом та жанром
                    cur.execute("""
                    INSERT INTO filmsGenres (filmId, genreId)
                    VALUES (?, ?)
                    """, (film_id, genre_id))
                
                con.commit()
                print(f"Successfully processed URL: {url}")
            except Exception as e:
                print(f"Error processing URL {url}: {e}")
                con.rollback()  # Відкат змін у разі помилки
                
# -----------------------------------------------------------------
insert_films_and_genres(movies_urls_list, 'fluxmain.db')
insert_films_and_genres(series_urls_list, 'fluxmain.db')