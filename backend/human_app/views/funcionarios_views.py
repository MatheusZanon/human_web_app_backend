from rest_framework.views import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import Group
from human_app.models import User, Funcionarios
from ..serializers import FuncionariosSerializer

@permission_classes([IsAuthenticated])
class FuncionarioViewset(viewsets.ModelViewSet):
    queryset = Funcionarios.objects.all()    
    serializer_class = FuncionariosSerializer
    
    def retrieve(self, request, pk=None):
        try:
            user = Funcionarios.objects.get(user=pk)
            serializer = FuncionariosSerializer(user)
            if serializer:
                user_data = serializer.data
                groups = [group.name for group in Group.objects.filter(user=user.user.id).all()]
                user_data['groups'] = groups
                del user_data['user_permissions']
                return Response(user_data, status=status.HTTP_200_OK)
        except Funcionarios.DoesNotExist:
            return Response({'error': 'Funcionário não encontrado'}, status=status.HTTP_404_NOT_FOUND)
    
    def list(self, request, *args, **kwargs):
        try:
            funcionarios = Funcionarios.objects.all()
            serializer = FuncionariosSerializer(funcionarios, many=True)
            if serializer:
                funcionarios_data = serializer.data
                index = 0
                for funcionario in funcionarios_data:
                    groups = [group.name for group in Group.objects.filter(user=funcionario.get('id')).all()]
                    funcionario['groups'] = groups
                    del funcionario['user_permissions']
                    funcionarios_data[index] = funcionario
                    index += 1
                return Response(funcionarios_data, status=status.HTTP_200_OK)
        except Funcionarios.DoesNotExist:
            return Response({'error': 'Funcionários não encontrado'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['put'], url_path='activate')
    def activate_user(self, request, pk=None):
        try:
            user = User.objects.filter(id=pk).get()

            ids = request.data['id']
            for id in ids:
                group = Group.objects.get(id=id)
                user.groups.add(group)
                user.is_active = True
                if group.name == 'ADMIN':
                    user.is_staff = True
                user.save()
            return Response(f"O usuário {user.username} foi ativado com sucesso", status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['put'], url_path='deactivate')
    def desactivate_user(self, request, pk=None):
        try:
            user = User.objects.filter(id=pk).get()
            user.is_active = False
            user.save()
            return Response(f"O usuário {user.username} foi desativado com sucesso", status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)