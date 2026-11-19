from django.db import models
from django.utils.text import Truncator


class Category(models.Model):
    """Категория вопросов"""
    name = models.CharField('Название категории', max_length=200, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, verbose_name="URL-идентификатор")
    description = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name


class QuestionAnswer(models.Model):
    """Вопрос-ответ базы знаний"""
    question = models.TextField('Вопрос', unique=True)
    answer = models.TextField('Ответ')
    keywords = models.TextField(
        'Ключевые слова',
        blank=True,
        help_text='Ключевые слова через запятую для поиска'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Категория',
        related_name='questions'
    )
    is_active = models.BooleanField('Активен', default=True)
    view_count = models.PositiveIntegerField('Просмотров', default=0)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Вопрос-Ответ'
        verbose_name_plural = 'База знаний'
        ordering = ['-created_at']

    def __str__(self):
        return Truncator(self.question).chars(80)


class SearchLog(models.Model):
    """Лог поиска вопросов"""
    query = models.TextField('Запрос')
    found = models.BooleanField('Найден ответ', default=False)
    question_answer = models.ForeignKey(
        QuestionAnswer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Найденный ответ'
    )
    similarity_score = models.FloatField('Оценка схожести', default=0.0)
    ip_address = models.GenericIPAddressField('IP адрес', null=True, blank=True)
    created_at = models.DateTimeField('Дата поиска', auto_now_add=True)

    class Meta:
        verbose_name = 'Лог поиска'
        verbose_name_plural = 'Логи поиска'
        ordering = ['-created_at']

    def __str__(self):
        status = "✓" if self.found else "✗"
        return f"{status} {Truncator(self.query).chars(50)}"
