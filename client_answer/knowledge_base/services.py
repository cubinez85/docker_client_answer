"""
Сервис анализа схожести вопросов.
Использует TF-IDF + косинусное сходство для определения дубликатов.
"""
import re
import logging
from typing import Optional, Tuple

from django.conf import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords

from .models import QuestionAnswer

logger = logging.getLogger(__name__)

# Загружаем стоп-слова для русского языка
try:
    RUSSIAN_STOPWORDS = set(stopwords.words('russian'))
except LookupError:
    nltk.download('stopwords')
    RUSSIAN_STOPWORDS = set(stopwords.words('russian'))

# Дополнительные стоп-слова
EXTRA_STOPWORDS = {
    'что', 'как', 'где', 'когда', 'почему', 'зачем', 'какой', 'какая',
    'какие', 'кто', 'можно', 'нужно', 'надо', 'подскажите', 'скажите',
    'расскажите', 'объясните', 'хочу', 'узнать', 'вопрос'
}
ALL_STOPWORDS = RUSSIAN_STOPWORDS | EXTRA_STOPWORDS


def normalize_text(text: str) -> str:
    """Нормализация текста: удаление спецсимволов, приведение к нижнему регистру"""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def extract_keywords(text: str) -> list:
    """Извлечение ключевых слов из текста"""
    normalized = normalize_text(text)
    words = normalized.split()
    keywords = [
        word for word in words
        if word not in ALL_STOPWORDS and len(word) > 2
    ]
    return keywords


def find_similar_question(
    new_question: str,
    threshold: float = None
) -> Tuple[Optional[QuestionAnswer], float]:
    """
    Поиск похожего вопроса в базе знаний.
    
    Алгоритм:
    1. Нормализуем новый вопрос
    2. Извлекаем ключевые слова
    3. Сравниваем с существующими вопросами через TF-IDF + cosine similarity
    4. Если схожесть >= threshold — считаем дубликатом
    
    Returns:
        Tuple[Optional[QuestionAnswer], float]: (найденный вопрос или None, оценка схожести)
    """
    if threshold is None:
        threshold = getattr(settings, 'SIMILARITY_THRESHOLD', 0.75)

    # Получаем все активные вопросы из базы
    existing_questions = QuestionAnswer.objects.filter(is_active=True)
    
    if not existing_questions.exists():
        return None, 0.0

    # Формируем корпус документов
    corpus = [qa.question for qa in existing_questions]
    corpus.append(new_question)

    # TF-IDF векторизация
    vectorizer = TfidfVectorizer(
        stop_words=list(ALL_STOPWORDS),
        ngram_range=(1, 2),  # Учитываем биграммы
        max_features=5000,
        sublinear_tf=True
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        logger.warning("Не удалось создать TF-IDF матрицу для вопроса: %s", new_question)
        return None, 0.0

    # Косинусное сходство нового вопроса со всеми существующими
    new_vector = tfidf_matrix[-1]
    existing_vectors = tfidf_matrix[:-1]
    
    similarities = cosine_similarity(new_vector, existing_vectors).flatten()
    
    # Находим максимальную схожесть
    max_idx = similarities.argmax()
    max_similarity = similarities[max_idx]

    if max_similarity >= threshold:
        similar_qa = existing_questions[max_idx]
        logger.info(
            "Найден дубликат: '%s' (схожесть: %.2f) с '%s'",
            new_question[:50], max_similarity, similar_qa.question[:50]
        )
        return similar_qa, float(max_similarity)

    return None, float(max_similarity)


def check_duplicate(new_question: str) -> dict:
    """
    Проверка вопроса на дубликат.
    
    Returns:
        dict с результатами:
        {
            'is_duplicate': bool,
            'existing_question': str or None,
            'similarity_score': float,
            'message': str
        }
    """
    similar_qa, score = find_similar_question(new_question)
    
    if similar_qa:
        return {
            'is_duplicate': True,
            'existing_question': similar_qa.question,
            'existing_answer': similar_qa.answer,
            'similarity_score': round(score, 4),
            'message': (
                f'Внимание: найден похожий вопрос в базе знаний '
                f'(схожесть: {score:.1%}). '
                f'Вопрос не будет добавлен как дубликат.'
            )
        }
    
    return {
        'is_duplicate': False,
        'existing_question': None,
        'existing_answer': None,
        'similarity_score': round(score, 4),
        'message': (
            f'Дубликат не найден (макс. схожесть: {score:.1%}). '
            f'Вопрос будет добавлен в базу знаний.'
        )
    }


def search_answer(query: str) -> dict:
    """
    Поиск ответа на вопрос клиента.
    
    Returns:
        dict с результатом поиска
    """
    # Сначала ищем по ключевым словам (exact match)
    keywords = extract_keywords(query)
    
    # Поиск по точному совпадению вопроса
    exact_match = QuestionAnswer.objects.filter(
        question__iexact=query.strip(),
        is_active=True
    ).first()
    
    if exact_match:
        exact_match.view_count += 1
        exact_match.save(update_fields=['view_count'])
        return {
            'found': True,
            'answer': exact_match.answer,
            'question': exact_match.question,
            'category': exact_match.category.name if exact_match.category else None,
            'similarity_score': 1.0,
            'method': 'exact_match'
        }
    
    # Поиск по ключевым словам в поле keywords
    for keyword in keywords:
        keyword_match = QuestionAnswer.objects.filter(
            keywords__icontains=keyword,
            is_active=True
        ).first()
        if keyword_match:
            keyword_match.view_count += 1
            keyword_match.save(update_fields=['view_count'])
            return {
                'found': True,
                'answer': keyword_match.answer,
                'question': keyword_match.question,
                'category': keyword_match.category.name if keyword_match.category else None,
                'similarity_score': 0.9,
                'method': 'keyword_match'
            }
    
    # Поиск через TF-IDF similarity
    similar_qa, score = find_similar_question(query)
    
    if similar_qa:
        similar_qa.view_count += 1
        similar_qa.save(update_fields=['view_count'])
        return {
            'found': True,
            'answer': similar_qa.answer,
            'question': similar_qa.question,
            'category': similar_qa.category.name if similar_qa.category else None,
            'similarity_score': score,
            'method': 'tfidf_similarity'
        }
    
    return {
        'found': False,
        'answer': None,
        'question': None,
        'category': None,
        'similarity_score': score,
        'method': 'none'
    }
