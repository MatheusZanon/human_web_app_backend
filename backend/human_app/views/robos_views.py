from rest_framework.views import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from human_app.models import Robos, RobosParametros, Parametros
from ..serializers.robos_serial import *
import subprocess
from datetime import datetime
from time import sleep
import requests
import json

@permission_classes([IsAuthenticated])
class RobosViewset(viewsets.ModelViewSet):
    queryset = Robos.objects.all()    
    serializer_class = RobosSerializer

    def destroy(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        
        try:
            robo_parametros = RobosParametros.objects.filter(robo=pk)
            if robo_parametros:
                parametro = None
                for param in robo_parametros:
                    print(param.pk)
                    parametro = Parametros.objects.get(pk=param.parametro.pk)
                    if parametro:
                        param.delete()
                        parametro.delete()

            robo.delete()
            return Response(f"Robo excluído com sucesso", status=status.HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='executar')
    def executar_robo(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
            if not robo:
                return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
            
            parametros = {}
            for key, value in request.data.items():
                parametros[key] = value

            robo_parametros = RobosParametros.objects.filter(robo=pk).all()

            if not robo_parametros:
                return Response("O robo não possui parâmetros definidos", status=status.HTTP_404_NOT_FOUND)
            
            parametros_testados = []
            for key, value in parametros.items():
                for param in robo_parametros:
                    parametro = Parametros.objects.get(pk=param.parametro.pk)
                    if not parametro:
                        return Response("Os parâmetros do robo não foram encontrados", status=status.HTTP_404_NOT_FOUND)
                    parametros_testados.append(parametro.nome)
                    if parametro.nome == key:
                        param.valor = value
                        param.save()
                        print(f"Parametro {key} atualizado")
                if not parametros_testados:
                    return Response("Os parâmetros do robo não foram encontrados", status=status.HTTP_404_NOT_FOUND)
            if param in parametros_testados != request.data.keys():
                print(f"Os parâmetros do robo são diferentes do enviado. Esperado: {', '.join(parametros_testados)}, Enviado: {key}")

            nome_robo = robo.nome.lower().replace(" ", "_")
            script_path = f"C:/Users/ACP/projetos/robo_{nome_robo}"
            robo_processo = subprocess.Popen(['powershell', '-Command', f"& cd '{script_path}'; ./.venv/Scripts/Activate.ps1; python robo_{nome_robo}.py"], shell=True, creationflags=subprocess.DETACHED_PROCESS, start_new_session=True)
            print("Robo em execução")
            sleep(2)
            parametros_json = json.dumps(parametros)
            resultado_request = requests.post(f"http://127.0.0.1:5000/", data=parametros_json, headers={'Content-Type': 'application/json'})
 
            if resultado_request.status_code == 200:
                print(f"Req concluída")
                robo.execucoes = robo.execucoes + 1 if robo.execucoes else 1
                robo.ultima_execucao = datetime.now()
                robo.save()
                print(f"{resultado_request.text}")
                requests.post(f"http://127.0.0.1:5000/shutdown")
                return Response("Robo executado com sucesso", status=status.HTTP_200_OK)
            else:
                print(f"{resultado_request.text}")
                requests.post(f"http://127.0.0.1:5000/shutdown")
                return Response("Erro ao executar o robo", status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True, methods=['post'], url_path='parametros/criar')
    def criar_parametro(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            if Parametros.objects.filter(nome=request.data['nome']).exists():
                return Response("Este parâmetro já foi criado", status=status.HTTP_400_BAD_REQUEST)
            
            parametro_serializer = ParametrosSerializer(data=request.data)

            if parametro_serializer.is_valid():                
                parametro_serializer.save()

                robo_parametro_serializer = RobosParametrosSerializer(data={'robo': robo.id, 'parametro': parametro_serializer.data['id']})
                if robo_parametro_serializer.is_valid():
                    robo_parametro_serializer.save()
                    return Response(f"Parâmetro criado com sucesso", status=status.HTTP_201_CREATED)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True, methods=['get'], url_path='parametros/listar')
    def listar_parametros(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            robo_parametros = RobosParametros.objects.filter(robo=pk)

            if not robo_parametros:
                return Response("O robo não possui parâmetros definidos", status=status.HTTP_204_NO_CONTENT)
            serializer = RobosParametrosSerializer(robo_parametros, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['put'], url_path='parametros/atualizar')
    def atualizar_parametros(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)

        try:
            robo_parametros = RobosParametros.objects.filter(robo=pk)

            if not robo_parametros:
                return Response("O robo não possui parâmetros definidos", status=status.HTTP_204_NO_CONTENT)
                
            parametros_testados = []
            for key, value in request.data.items():
                for param in robo_parametros:
                    parametro = Parametros.objects.get(pk=param.parametro.pk)
                    if not parametro:
                        return Response("Os parâmetros do robo não foram encontrados", status=status.HTTP_404_NOT_FOUND)
                    parametros_testados.append(parametro.nome)
                    if parametro.nome == key:
                        param.valor = value
                        param.save()
                        return Response("Parâmetros atualizados com sucesso", status=status.HTTP_204_NO_CONTENT)
                if not parametros_testados:
                    return Response("Os parâmetros do robo não foram encontrados", status=status.HTTP_404_NOT_FOUND)
            return Response(f"Os parâmetros do robo são diferentes do enviado. Esperado: {', '.join(parametros_testados)}, Enviado: {key}", status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['put'], url_path='parametros/atualizar/(?P<param_pk>[^/.]+)')
    def atualizar_parametro(self, request, pk=None, param_pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            robo_parametros = RobosParametros.objects.filter(robo=pk)
            if not robo_parametros:
                return Response("O parâmetro do robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
            parametro = None
            for param in robo_parametros:
                if param.parametro.pk == int(param_pk):
                    parametro = Parametros.objects.get(pk=param.parametro.pk)
                    break

            if not parametro:
                return Response("O parâmetro do robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)

            parametro_serializer = ParametrosSerializer(parametro, data=request.data)

            if parametro_serializer.is_valid():
                parametro_serializer.save()
                return Response("Parâmetro atualizado com sucesso", status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['delete'], url_path='parametros/excluir/(?P<param_pk>[^/.]+)')
    def excluir_parametro(self, request, pk=None, param_pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            robo_parametros = RobosParametros.objects.filter(robo=pk)
            if not robo_parametros:
                return Response("O parâmetro do robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
            
            parametro = None
            for param in robo_parametros:
                print(param.pk == int(param_pk))
                if param.pk == int(param_pk):
                    parametro = Parametros.objects.get(pk=param.parametro.pk)
                    print(parametro.nome)
                    break

            if not parametro:
                return Response("O parâmetro do robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)

            parametro.delete()
            param.delete()
            return Response("Parâmetro excluído com sucesso", status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='rotinas')
    def rotinas(self, request, pk=None):
        rotinas = Rotinas.objects.filter(robo=pk)
        serializer = RotinasSerializer(rotinas, many=True)
        if serializer:
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], url_path='rotinas/criar')
    def criar_rotina(self, request, pk=None):
        request_data = request.data
        request_data['robo'] = pk
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            if Rotinas.objects.filter(robo=pk, nome=request_data['nome']).exists():
                return Response("Esta rotina já foi criada", status=status.HTTP_400_BAD_REQUEST)
            
            print(request_data)

            serializer = RotinasSerializer(data=request_data)

            if serializer.is_valid():
                serializer.save(robo=robo)
                return Response(f"Rotina criada com sucesso", status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='rotinas/listar')
    def listar_rotinas(self, request, pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            robo_rotinas = Rotinas.objects.filter(robo=pk)

            if not robo_rotinas:
                return Response("O robo não possui rotinas definidas", status=status.HTTP_204_NO_CONTENT)
            
            serializer = RotinasSerializer(robo_rotinas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['put'], url_path='rotinas/atualizar/(?P<rotina_pk>[^/.]+)')
    def editar_rotina(self, request, pk=None, rotina_pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            robo_rotinas = Rotinas.objects.filter(robo=pk)
            if not robo_rotinas:
                return Response("O robo não possui rotinas definidas", status=status.HTTP_404_NOT_FOUND)
            
            robo_rotina = None
            for rotina in robo_rotinas:
                if rotina.pk == int(rotina_pk):
                    robo_rotina = rotina
                    break

            if not robo_rotina:
                return Response("A rotina do robo não foi encontrada", status=status.HTTP_404_NOT_FOUND)

            request.data['robo'] = pk
            robo_rotina_serializer = RotinasSerializer(robo_rotina, data=request.data)
            if robo_rotina_serializer.is_valid():
                robo_rotina_serializer.save()
                return Response("Rotina atualizada com sucesso", status=status.HTTP_204_NO_CONTENT)

            return Response(robo_rotina_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['delete'], url_path='rotinas/excluir/(?P<rotina_pk>[^/.]+)')
    def excluir_rotina(self, request, pk=None, rotina_pk=None):
        try:
            robo = Robos.objects.get(id=pk)
        except Robos.DoesNotExist:
            return Response("O robo não foi encontrado", status=status.HTTP_404_NOT_FOUND)
        try:
            robo_rotinas = Rotinas.objects.filter(robo=pk)
            if not robo_rotinas:
                return Response("O robo não possui rotinas definidas", status=status.HTTP_404_NOT_FOUND)
            
            robo_rotina = None
            for rotina in robo_rotinas:
                if rotina.pk == int(rotina_pk):
                    robo_rotina = rotina
                    break

            if not robo_rotina:
                return Response("A rotina do robo não foi encontrada", status=status.HTTP_404_NOT_FOUND)

            robo_rotina.delete()
            return Response("Rotina excluída com sucesso", status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)