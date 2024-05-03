from rest_framework.views import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import Group
from human_app.models import User, Funcionarios
from ..serializers import FuncionariosSerializer, UserSerializer

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
        
    def partial_update(self, request, *args, **kwargs):
        try:
            user = User.objects.get(id=kwargs['pk'])
            funcionario = Funcionarios.objects.get(user=user)

            # Atualizar campos do usuário
            user_data = {}
            if 'username' in request.data:
                user_data['username'] = request.data['username']
            if 'email' in request.data:
                user_data['email'] = request.data['email']
            if 'first_name' in request.data:
                user_data['first_name'] = request.data['first_name']
            if 'last_name' in request.data:
                user_data['last_name'] = request.data['last_name']

            # Atualizar grupos
            if 'groups' in request.data:
                user.groups.clear()
                for group_id in request.data['groups']:
                    group = Group.objects.get(id=group_id)
                    user.groups.add(group)

            # Atualizar campos de Funcionarios
            funcionario_data = {}
            if 'phone' in request.data:
                funcionario_data['telefone_celular'] = request.data['phone']

            # Validar e salvar User
            user_serializer = UserSerializer(user, data=user_data, partial=True)
            funcionario_serializer = FuncionariosSerializer(funcionario, data=funcionario_data, partial=True)
            if user_serializer.is_valid() and funcionario_serializer.is_valid():
                user_serializer.save()
                funcionario_serializer.save()
            else:
                errors = user_serializer.errors
                errors.append(funcionario_serializer.errors)
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

            data = funcionario_serializer.data
            del data['user_permissions']
            return Response(data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "Usuário não encontrado"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as error:
            return Response({"error": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)