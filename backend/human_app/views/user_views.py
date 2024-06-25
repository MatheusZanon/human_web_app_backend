from rest_framework.views import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail
from django.contrib.auth.models import Group
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.conf import settings
import os
from human_app.models import User, Funcionarios, PasswordResetTokens
from ..serializers import UserSerializer, FuncionariosSerializer, GroupSerializer, PasswordResetTokenSerializer

class UserViewset(viewsets.ModelViewSet):
    queryset = User.objects.all()    
    serializer_class = UserSerializer

    @action(detail=False, methods=['get'], url_path='login')
    def login(self, request, *args, **kwargs):
        try:
            user = Funcionarios.objects.get(user=request.user)
            serializer = FuncionariosSerializer(user)
            if serializer:
                user_data = serializer.data
                groups = [group.name for group in Group.objects.filter(user=request.user).all()]
                user_data['groups'] = groups
                del user_data['user_permissions']
                return Response(user_data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response({'error': str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # CADASTRO  
    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        email = request.data.get('email')
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Esse nome de usuário já existe.'}, status=status.HTTP_400_BAD_REQUEST)
        elif User.objects.filter(email=email).exists():
            return Response({'error': 'Esse email já existe.'}, status=status.HTTP_400_BAD_REQUEST) 
        try:
            user = None
            user_serializer = UserSerializer(data=request.data)
            if user_serializer.is_valid():
                user = user_serializer.save()
                funcionario_data = {
                    'rg': request.data.get('rg'),
                    'cpf': request.data.get('cpf'),
                    'telefone_celular': request.data.get('telefone_celular'),
                }
                funcionario = Funcionarios.objects.create(user=user, **funcionario_data)
                funcionario.save()
                return Response(user_serializer.data, status=status.HTTP_201_CREATED)
            else:
                print("USER SERIALIZER INVALIDO")
                return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response({'error': str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='forgot-password')
    def forgot_password(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response('Email obrigatório.', status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response('Usuário não encontrado.', status=status.HTTP_404_NOT_FOUND)
        
        token = get_random_string(length=32)
        token_data = {
            'user': user.pk,
            'token': token,
        }

        token_serializer = PasswordResetTokenSerializer(data=token_data)

        if token_serializer.is_valid():
            token_serializer.save()
            # reset_url = request.build_absolute_uri(
            #    reverse('user-reset-password') + f"?token={token}"
            # )
            frontend_url = os.getenv('FRONTEND_URL')
            reset_front_url = f"{frontend_url}/reset-password?token={token}"
            send_mail(
                'Recuperação de senha',
                f'''Por favor clique no link abaixo para redefinir sua senha: {reset_front_url}
se não solicitou esta redefinição, ignore este email.''',
                settings.DEFAULT_FROM_EMAIL,
                [email],
            )

            return Response({'message': 'Email enviado com sucesso.'}, status=status.HTTP_200_OK)
        else:
            return Response(token_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='reset-password')
    def reset_password(self, request):
        token = request.query_params.get('token')
        new_password = request.data.get('new_password')

        if not all([token, new_password]):
            return Response('Token e senha obrigatórias.', status=status.HTTP_400_BAD_REQUEST)

        try:
            reset_token = PasswordResetTokens.objects.get(token=token)

            if not reset_token.is_valid():
                reset_token.delete()
                return Response('Token inválido ou expirado.', status=status.HTTP_400_BAD_REQUEST)
        except PasswordResetTokens.DoesNotExist:
            return Response('Token não encontrado.', status=status.HTTP_404_NOT_FOUND)
        
        user = reset_token.user
        user.set_password(new_password)
        user.save()
        reset_token.delete()

        return Response({'message': 'Senha redefinida com sucesso.'}, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
class GroupsViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer