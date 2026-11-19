from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.db.models import Count

from knowledge_base.models import Category, QuestionAnswer, SearchLog
from knowledge_base.services import check_duplicate, search_answer
from .serializers import (
    CategorySerializer,
    QuestionAnswerSerializer,
    QuestionAnswerCreateSerializer,
    SearchQuerySerializer,
    DuplicateCheckSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD для категорий"""
    queryset = Category.objects.annotate(question_count=Count('questions'))
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ['name', 'description']


class QuestionAnswerViewSet(viewsets.ModelViewSet):
    """CRUD для вопросов-ответов с проверкой на дубликаты"""
    queryset = QuestionAnswer.objects.select_related('category').all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ['question', 'answer', 'keywords']
    filterset_fields = ['category', 'is_active']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return QuestionAnswerCreateSerializer
        return QuestionAnswerSerializer

    def create(self, request, *args, **kwargs):
        """Создание вопроса-ответа с проверкой на дубликат"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            {'message': 'Вопрос-ответ успешно добавлен в базу знаний'},
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(detail=False, methods=['post'])
    def check_duplicate(self, request):
        """Проверка вопроса на дубликат без сохранения"""
        serializer = DuplicateCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        question = serializer.validated_data['question']
        result = check_duplicate(question)
        
        return Response(result)


class SearchViewSet(viewsets.ViewSet):
    """Поиск ответа на вопрос клиента"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def create(self, request):
        """POST /api/search/ — найти ответ на вопрос"""
        serializer = SearchQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        query = serializer.validated_data['query']
        result = search_answer(query)
        
        # Логируем поиск
        SearchLog.objects.create(
            query=query,
            found=result['found'],
            question_answer_id=result.get('question_answer_id'),
            similarity_score=result['similarity_score'],
            ip_address=self.get_client_ip(request)
        )
        
        return Response(result)

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """GET /api/search/popular/ — популярные вопросы"""
        questions = QuestionAnswer.objects.filter(
            is_active=True
        ).order_by('-view_count')[:10]
        serializer = QuestionAnswerSerializer(questions, many=True)
        return Response(serializer.data)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
