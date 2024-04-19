from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken
from django.contrib.auth import get_user_model
from rest_framework import exceptions

class JWTAuthenticationFromCookie(JWTAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get('access_token')
        if not raw_token:
            return None
        try:
            valid_token = UntypedToken(raw_token)
            user_id = valid_token['user_id']
        except (InvalidToken, TokenError) as e:
            raise exceptions.AuthenticationFailed('Token inválido')

        try:
            user = get_user_model().objects.get(id=user_id)
        except get_user_model().DoesNotExist:
            raise exceptions.AuthenticationFailed('Usuário não encontrado')

        return (user, None)