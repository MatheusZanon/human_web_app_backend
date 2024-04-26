from rest_framework.views import APIView, Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        try:
            if response.status_code == 200:
                access_token = response.data.get('access')
                refresh_token = response.data.get('refresh')
                response.set_cookie(
                    key='access_token',
                    value=access_token,
                    httponly=True,
                    samesite='Lax',
                    path='/',
                    secure=False  # True em produção
                )
                del response.data['refresh']  # Remova o refresh token da resposta
            return response
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@permission_classes([IsAuthenticated])
class SessionVerifyToken(APIView):
    def get(self, request, format=None):
        return Response({"Token: Válido"}, status=status.HTTP_200_OK)
    
class SessionLogout(APIView):
    def post(self, request):
        response = JsonResponse({"detail": "Logout realizado com sucesso."}, status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response