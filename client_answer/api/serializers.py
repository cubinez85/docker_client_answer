from rest_framework import serializers
from knowledge_base.models import Category, QuestionAnswer, SearchLog


class CategorySerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'question_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class QuestionAnswerSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)

    class Meta:
        model = QuestionAnswer
        fields = [
            'id', 'question', 'answer', 'keywords', 'category',
            'category_name', 'is_active', 'view_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['view_count', 'created_at', 'updated_at']


class QuestionAnswerCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания вопроса с проверкой на дубликат"""

    class Meta:
        model = QuestionAnswer
        fields = ['question', 'answer', 'keywords', 'category', 'is_active']

    def validate_question(self, value):
        """Проверка на дубликат при создании"""
        from knowledge_base.services import check_duplicate
        
        result = check_duplicate(value)
        
        if result['is_duplicate']:
            raise serializers.ValidationError(
                f"Дубликат найден! Похожий вопрос уже существует в базе знаний "
                f"(схожесть: {result['similarity_score']:.1%}): "
                f"'{result['existing_question']}'"
            )
        return value


class SearchQuerySerializer(serializers.Serializer):
    query = serializers.CharField(
        max_length=1000,
        help_text='Текст вопроса для поиска ответа'
    )


class SearchResponseSerializer(serializers.Serializer):
    found = serializers.BooleanField()
    answer = serializers.CharField(allow_null=True)
    question = serializers.CharField(allow_null=True)
    category = serializers.CharField(allow_null=True)
    similarity_score = serializers.FloatField()
    method = serializers.CharField()


class DuplicateCheckSerializer(serializers.Serializer):
    question = serializers.CharField(
        max_length=1000,
        help_text='Вопрос для проверки на дубликат'
    )
