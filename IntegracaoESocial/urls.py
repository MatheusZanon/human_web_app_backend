from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmpregadorViewSet

router = DefaultRouter()
router.register(r'empregador', EmpregadorViewSet, basename='empregador')

urlpatterns = [
    path('', include(router.urls)),
]