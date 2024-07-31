# import libraries
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
import string
import re
import spacy
from googletrans import Translator
#----------------------------------------

stop_words = set(stopwords.words('english'))

def process_text_to_tokens(text, stop_words, target_language='en'):
    # Попередня обробка тексту
    text = text.replace('/', ' ').replace('-', ' ')
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = ' '.join(text.split())
    text = re.sub(r'\d+', '', text)
    
    # Токенізація
    tokens = word_tokenize(text)
    
    # Переклад
    translator = Translator()
    tokens = [translator.translate(token, dest=target_language).text for token in tokens]
    
    # Приведення до нижнього регістру
    tokens = [token.lower() for token in tokens]
    
    # Повторна токенізація після перекладу
    tokens = [word for token in tokens for word in word_tokenize(token)]
    
    # Видалення дублікатів
    tokens = list(set(tokens))
    
    # Видалення стоп-слів
    tokens = [token for token in tokens if token not in stop_words]
    
    # Лематизація
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    # Об'єднання токенів у рядок
    str_tokens = ' '.join(tokens)
    
    if not str_tokens:
        return None
    
    return str_tokens

#----------------------------------------
def update_tokens_column(stop_words, dbname="fluxmain.db"):
    try:
        with sq.connect(dbname) as con:
            cur = con.cursor()

            # Отримати всі дані зі стовпця caption та id таблиці films
            cur.execute("""
                SELECT id, caption, tokens
                FROM films
            """)
            
            films_data = cur.fetchall()

            for film_id, caption, tokens in films_data:
                if tokens is None:
                    tokens = process_text_to_tokens(caption, stop_words)
                    cur.execute("""
                        UPDATE films
                        SET tokens = ?
                        WHERE id = ?
                    """, (tokens, film_id))

                    con.commit()
    except Exception as e:
        print(f"Помилка підключення до сервера: {e}")
        update_tokens_column(stop_words)


# Виклик функції для оновлення стовпця tokens
update_tokens_column(stop_words)