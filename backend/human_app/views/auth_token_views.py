from rest_framework import status
from rest_framework.views import APIView, Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.conf import settings
from human_app.models import User
from ..serializers.user_serial import *

class CheckUser(APIView):
    serializer = UserSerializer
    def post(self, request):
        try:
            user = User.objects.get(username=request.data['username'])
            if user.is_active:
                return Response({"Usuário ativo"}, status=status.HTTP_200_OK)
            return Response({"Usuário inativo"}, status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return Response({"Usuário inexistente"}, status=status.HTTP_404_NOT_FOUND)

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        try:
            if response.status_code == 200:
                access_token = response.data.get('access')
                refresh_token = response.data.get('refresh')

                # Configurar o cookie para o token de acesso
                response.set_cookie(
                    key='access_token',
                    value=access_token,
                    max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                    httponly=True,
                    samesite='Lax',
                    path='/',
                    secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],  # True em produção
                )

                # Configurar o cookie para o token de refresh
                response.set_cookie(
                    key='refresh_token',
                    value=refresh_token,
                    max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                    httponly=True,
                    samesite='Lax',
                    path='/',
                    secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],  # True em produção
                )

                # Remove os tokens do corpo da resposta
                del response.data['refresh']
                del response.data['access']
                return response
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@permission_classes([IsAuthenticated])   
class SessionVerifyToken(APIView):
    def get(self, request, format=None):
        return Response({"Token": "Verificado"}, status=status.HTTP_200_OK)

class SessionRenewToken(APIView):
    def post(self, request, format=None):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                # Cria um novo token de acesso usando o token de refresh
                valid_refresh_token = RefreshToken(refresh_token)
                new_access_token = valid_refresh_token.access_token
                response = Response({"Token": "Renovado"}, status=status.HTTP_200_OK)
                response.set_cookie(
                    key='access_token',
                    value=str(new_access_token),
                    max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                    httponly=True,
                    samesite='Lax',
                    path='/',
                    secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],  # True em produção
                )
                return response
            except TokenError as e:
                return Response({"Error": "Refresh Token inválido"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({"Error": "Não há Refresh Token"}, status=status.HTTP_404_NOT_FOUND)

class SessionLogout(APIView):
    def post(self, request):
        response = JsonResponse({"detail": "Logout realizado com sucesso."}, status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response