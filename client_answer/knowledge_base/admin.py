from django.contrib import admin
from .models import Category, QuestionAnswer, SearchLog


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(QuestionAnswer)
class QuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ('short_question', 'category', 'is_active', 'view_count', 'created_at')
    list_filter = ('is_active', 'category', 'created_at')
    search_fields = ('question', 'answer', 'keywords')
    list_editable = ('is_active',)
    readonly_fields = ('view_count', 'created_at', 'updated_at')
    fieldsets = (
        ('Основное', {
            'fields': ('question', 'answer', 'category', 'is_active')
        }),
        ('Поиск', {
            'fields': ('keywords',),
            'description': 'Ключевые слова через запятую для улучшения поиска'
        }),
        ('Статистика', {
            'fields': ('view_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def short_question(self, obj):
        return obj.question[:80] + '...' if len(obj.question) > 80 else obj.question
    short_question.short_description = 'Вопрос'


@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
    list_display = ('query', 'found', 'similarity_score', 'ip_address', 'created_at')
    list_filter = ('found', 'created_at')
    search_fields = ('query',)
    readonly_fields = ('query', 'found', 'question_answer', 'similarity_score', 'ip_address', 'created_at')
