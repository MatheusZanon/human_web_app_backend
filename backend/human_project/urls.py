"""
URL configuration for human_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from human_app.views import *


urlpatterns = [
    path('admin/', admin.site.urls),

    # Autenticação
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', VerifyToken.as_view(), name='token_verify'),

    # User
    path('api/user/', UserAPI.as_view()),

    # Funcionários
    path('api/funcionarios/', FuncionariosAPI.as_view()),

    # Robôs
    path('api/robos/', RobosAPI.as_view()),
    path('api/robos/<id_robo>/', RoboAPI.as_view()),
    path('api/robos/<id_robo>/parametros/', RobosParametrosAPI.as_view()),
    path('api/robos/<id_robo>/parametros/new/', ParametrosAPI.as_view()),
    path('api/robos/<id_robo>/rotinas/', RotinasGetAPI.as_view()),
    path('api/robos/<id_robo>/rotinas/new/', RotinasPostAPI.as_view()),
    path('api/robos/<id_robo>/executar/', ExecutarRoboAPI.as_view()),

    # Clientes Financeiro
    path('api/clientes_financeiro/', ClientesFinanceiroAPI.as_view()),
    path('api/clientes_financeiro_valores/', ClientesFinanceiroValoresAPI.as_view()),
]
