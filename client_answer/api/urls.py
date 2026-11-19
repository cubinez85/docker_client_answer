from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, QuestionAnswerViewSet, SearchViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'questions', QuestionAnswerViewSet, basename='question')
router.register(r'search', SearchViewSet, basename='search')

urlpatterns = [
    path('', include(router.urls)),
]
