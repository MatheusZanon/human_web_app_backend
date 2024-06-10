import os
import io
import tempfile
from dotenv import load_dotenv
from operator import itemgetter
from human_app.services.google_drive_service import Create_Service
from django.http import HttpResponse, FileResponse
from rest_framework import status, viewsets
from rest_framework.views import Response
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from django.views.decorators.clickjacking import xframe_options_exempt, xframe_options_deny, xframe_options_sameorigin



#------------------- CONFIGURACOES GOOGLE DRIVE -------------------
load_dotenv()

SECRET_SERVICE_FILE = os.getenv('SECRET_SERVICE_FILE')
API_NAME = os.getenv('API_NAME')
API_VERSION = os.getenv('API_VERSION')
SCOPES = [os.getenv('SCOPES')]
#------------------------------------------------------------------

@permission_classes([IsAuthenticated])
class GoogleDriveViewSet(viewsets.ModelViewSet):
    queryset = None

    @action(detail=False, methods=['get'], url_path='upload_arquivos')
    def upload_arquivo(self, request):
        print("upload_arquivo")

    @action(detail=False, methods=['get'], url_path='listar_arquivos')
    def listar_arquivos(self, request):
        try:    
            service = Create_Service(SECRET_SERVICE_FILE, API_NAME, API_VERSION, SCOPES)
            folder_id = request.query_params.get('folder_id')
            query = f"parents in '{folder_id}'"

            response = service.files().list(q=query, fields="nextPageToken, files(id, name, mimeType, parents, modifiedTime)").execute()
            arquivos = response.get('files', [])
            arquivos_ordenados = sorted(arquivos, key=itemgetter('mimeType', 'name'))

            return Response(arquivos_ordenados, status=status.HTTP_200_OK)
        except Exception as error:
            print(error)
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['post'], url_path='upload_arquivo')
    def upload_arquivo(self, request):
        try:
            files = request.FILES.getlist('files')
            mime_types = request.data.getlist('mime_types')
            folder_id = request.data.get('parents')
            service = Create_Service(SECRET_SERVICE_FILE, API_NAME, API_VERSION, SCOPES)

            for file, mime_type in zip(files, mime_types):
                file_metadata = {
                    'name': file.name,
                    'parents': [folder_id],
                }
                print(file_metadata)

                # Cria um arquivo temporário se necessário
                if hasattr(file, 'temporary_file_path'):
                    file_path = file.temporary_file_path()
                else:
                    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                        temp_file.write(file.read())
                        file_path = temp_file.name

                media = MediaFileUpload(file_path, mimetype=mime_type)
                service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            return Response("Arquivos enviados com sucesso.", status=status.HTTP_200_OK)
        except Exception as error:
            print(error)
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def download_arquivo(service, arquivo_id):
        try:
            request = service.files().get_media(fileId=arquivo_id)
            file_io = io.BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            file_io.seek(0)
            return Response(file_io, status=status.HTTP_200_OK)
        except Exception as error:
            print(error)
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @xframe_options_exempt
    @action(detail=False, methods=['get'], url_path='serve_file_preview')
    def serve_file_preview(self, request):
        try:
            arquivo_id = request.query_params.get('arquivo_id')
            print("Arquivo ID:", arquivo_id)
            service = Create_Service(SECRET_SERVICE_FILE, API_NAME, API_VERSION, SCOPES)
            
            file_info = service.files().get(fileId=arquivo_id, fields='name, mimeType').execute()
            mimeType = file_info.get('mimeType')
            filename = file_info.get('name')

            request = service.files().get_media(fileId=arquivo_id)
            file_io = io.BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)

            done = False
            while not done:
                _, done = downloader.next_chunk()
            file_io.seek(0)

            return FileResponse(file_io, as_attachment=False, filename=filename, content_type=mimeType)
        except Exception as error:
            print(error)
            return Response(f"{error}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)