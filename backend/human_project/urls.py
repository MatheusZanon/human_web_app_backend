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
from human_app.views import *


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/', User.as_view()),
    path('api/login/', UserAuthToken.as_view()),
    #path('api/solicitacoes_cadastro/', SolicitacoesCadastroAPI.as_view()),
    path('api/funcionarios/', FuncionariosAPI.as_view()),
    path('api/clientes_financeiro/', ClientesFinanceiroAPI.as_view()),
    path('api/clientes_financeiro_valores/', ClientesFinanceiroValoresAPI.as_view()),
    path('api/robos/', RobosAPI.as_view()),
    path('api/robos/<id_robo>/', RoboAPI.as_view()),
    path('api/robos/<id_robo>/parametros/', RobosParametrosAPI.as_view()),
    path('api/robos/<id_robo>/rotinas/', RotinasAPI.as_view()),
    path('api/robos/<id_robo>/executar/', ExecutarRoboAPI.as_view()),
]
