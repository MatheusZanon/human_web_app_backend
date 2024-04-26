from rest_framework.views import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import Group
from human_app.models import User, Funcionarios
from ..serializers import UserSerializer, FuncionariosSerializer, GroupSerializer

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

@permission_classes([IsAuthenticated])
class GroupsViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer