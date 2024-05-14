from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.conf import settings
from rest_framework import exceptions
import json

class JWTAuthenticationFromCookie(JWTAuthentication):
    def authenticate(self, request):
        token_str = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])
        if not token_str:
            return None
        
        try:
            tokens = json.loads(token_str)
            access_token = tokens.get('access')
            if not access_token:
                raise exceptions.AuthenticationFailed('Token não encontrado ou inválido')
            
            valid_token = UntypedToken(access_token)
            user_id = valid_token['user_id']
        except (InvalidToken, TokenError) as e:
            raise exceptions.AuthenticationFailed('Token inválido')

        try:
            user = get_user_model().objects.get(id=user_id)
        except get_user_model().DoesNotExist:
            raise exceptions.AuthenticationFailed('Usuário não encontrado')

        return (user, None)