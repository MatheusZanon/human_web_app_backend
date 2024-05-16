from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import exceptions

class JWTAuthenticationFromCookie(JWTAuthentication):
    def authenticate(self, request):   
        access_token = request.COOKIES.get('access_token')
        if access_token:
            try:
                validated_token = self.get_validated_token(access_token)
                user = self.get_user(validated_token)
                return (user, validated_token)
            except (InvalidToken, TokenError) as e:
                raise exceptions.AuthenticationFailed('Token inválido')
        elif not access_token:
            return None
            