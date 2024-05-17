import os
from dotenv import load_dotenv
from operator import itemgetter
from human_app.services.google_drive_service import Create_Service
from rest_framework import status, viewsets
from rest_framework.views import Response
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated


#------------------- CONFIGURACOES GOOGLE DRIVE -------------------
load_dotenv()

CLIENT_SECRET_FILE = os.getenv('CLIENT_SECRET_FILE')
API_NAME = os.getenv('API_NAME')
API_VERSION = os.getenv('API_VERSION')
SCOPES = [os.getenv('SCOPES')]
#------------------------------------------------------------------

@permission_classes([IsAuthenticated])
class GoogleDriveViewSet(viewsets.ModelViewSet):

    @action(detail=False, methods=['get'], url_path='upload_arquivos')
    def upload_arquivo(self, request):
        print("upload_arquivo")

    @action(detail=False, methods=['get'], url_path='listar_arquivos')
    def listar_arquivos(self, request):
        try:    
            service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
            print(service)
            folder_id = request.query_params.get('folder_id')
            query = f"parents in '{folder_id}'"

            response = service.files().list(q=query, fields="nextPageToken, files(id, name, mimeType, parents, modifiedTime)").execute()
            arquivos = response.get('files', [])

            arquivos_ordenados = sorted(arquivos, key=itemgetter('mimeType'), reverse=True)

            return Response(arquivos_ordenados, status=status.HTTP_200_OK)
        except Exception as error:
            print(error)
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='preview_arquivo')
    def preview_arquivo(self, request):
        try:
            print("preview_arquivo", request.query_params.get('arquivo_id'))
            return Response("preview_arquivo", status=status.HTTP_200_OK)
        except Exception as error:
            print(error)
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)