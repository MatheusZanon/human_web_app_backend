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
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from human_app.views import *


router = DefaultRouter()

router.register(r'user', UserViewset)
router.register(r'funcionarios', FuncionarioViewset)
router.register(r'clientes_financeiro', ClientesFinanceiroViewset)
router.register(r'financeiro_valores', ClientesFinanceiroValoresViewset)
router.register(r'robos', RobosViewset)
router.register(r'groups', GroupsViewSet)
router.register(r'dashboard', DashboardViewset, basename='dashboard')
router.register(r'google_drive', GoogleDriveViewSet, basename='google_drive')

urlpatterns = [
    path('api/', include(router.urls)),
    path('admin/', admin.site.urls),

    # Autenticação
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/session/renew/', SessionRenewToken.as_view(), name='session_renew_token'),
    path('api/session/verify/', SessionVerifyToken.as_view(), name='session_verify_token'),
    path('api/session/logout/', SessionLogout.as_view(), name='session_logout'),
]
