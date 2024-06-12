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
    
    @action(detail=False, methods=['post'], url_path='criar_pasta')
    def criar_pastas(self, request):
        try:
            service = Create_Service(SECRET_SERVICE_FILE, API_NAME, API_VERSION, SCOPES)
            folder_name = request.data.get('folder_name')
            parents = request.data.get('parents')

            if not folder_name or not parents:
                return Response("Nome da pasta e ID do diretório pai são obrigatórios.", status=status.HTTP_400_BAD_REQUEST)

            query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and '{parents}' in parents and trashed = false"
            results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            items = results.get('files', [])

            if items:
                return Response("Pasta já existe.", status=status.HTTP_400_BAD_REQUEST)

            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parents]
            }
            folder = service.files().create(body=folder_metadata, fields='id').execute()
            return Response("Pasta criada com sucesso.", status=status.HTTP_200_OK)
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
    
    @action(detail=False, methods=['get'], url_path='download_arquivo')
    def download_arquivo(self, request):
        try:
            file_id = request.query_params.get('id')
            if not file_id:
                return Response("O ID do arquivo deve ser informado.", status=status.HTTP_400_BAD_REQUEST)
            service = Create_Service(SECRET_SERVICE_FILE, API_NAME, API_VERSION, SCOPES)

            request = service.files().get_media(fileId=file_id) 
            file_io = io.BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)
         
            done = False
            while not done:
                download_status, done = downloader.next_chunk()
                print(f"Download {int(download_status.progress() * 100)}%")

            file_io.seek(0)
            file_metadata = service.files().get(fileId=file_id, fields="name, mimeType").execute()

            # Retornar o arquivo como resposta HTTP
            response = HttpResponse(file_io.read(), content_type=file_metadata.get('mimeType'))
            response['Content-Length'] = len(file_io.getvalue())  # Adicionar o tamanho do arquivo
            return response
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