from rest_framework import status
from rest_framework.views import APIView, Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.backends import TokenBackend
from django.http import JsonResponse
from django.conf import settings
import json

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        try:
            if response.status_code == 200:
                access_token = response.data.get('access')
                refresh_token = response.data.get('refresh')
                tokens = json.dumps({
                    'access': access_token,
                    'refresh': refresh_token
                })
                response.set_cookie(
                    key='user_info',
                    value=tokens, 
                    httponly=True,
                    samesite='Lax',
                    path='/',
                    secure=False  # True em produção
                )
                del response.data['refresh']  # Remova o refresh token da resposta
            return response
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class SessionVerifyToken(APIView):
    def get(self, request, format=None):
        # Tentativa de validar o token de acesso primeiro
        raw_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])  # Assume que o token está no cookie
        if not raw_token:
            return Response({"Error": "Nenhum token fornecido"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            tokens = json.loads(raw_token)
            access_token = tokens.get('access')
            refresh_token = tokens.get('refresh')
        except json.JSONDecodeError:
            return Response({"Error": "Formato de token inválido"}, status=status.HTTP_401_UNAUTHORIZED)

        token_backend = TokenBackend(algorithm=settings.SIMPLE_JWT['ALGORITHM'], signing_key=settings.SIMPLE_JWT['SIGNING_KEY'])
        if access_token:
            try:
                token_backend.decode(str(access_token), verify=True)
                return Response({"Token": "Válido"}, status=status.HTTP_200_OK)
            except TokenError as e:
                if refresh_token:
                    try:
                        valid_refresh_token = RefreshToken(refresh_token)
                        new_access_token = valid_refresh_token.access_token
                        response = Response({"Token": "Renovado"}, status=status.HTTP_200_OK)    
                        new_tokens = json.dumps({
                            'access': str(new_access_token),
                            'refresh': str(refresh_token)
                        })
                        response.set_cookie(
                            key='user_info',
                            value=new_tokens,
                            httponly=True,
                            samesite='Lax',
                            path='/',
                            secure=False  # True em produção
                        )
                        return response
                    except TokenError as e:
                        return Response({"Error": "Refresh token inválido"}, status=status.HTTP_401_UNAUTHORIZED)
                else:
                    return Response({"Error": "Refresh Token necessário"}, status=status.HTTP_401_UNAUTHORIZED)      
        return Response({"Error": "Autenticação necessária"}, status=status.HTTP_401_UNAUTHORIZED)


class SessionLogout(APIView):
    def post(self, request):
        response = JsonResponse({"detail": "Logout realizado com sucesso."}, status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('user_info')
        return response