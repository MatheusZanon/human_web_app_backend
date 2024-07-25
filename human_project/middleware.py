from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from aws_parameters import get_ssm_parameter

FRONTEND_URL_AWS_DOMAIN = get_ssm_parameter('/human/FRONTEND_URL_AWS_DOMAIN')

class BlockDirectAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.META.get('HTTP_REFERER') != 'https://app.humanrh.com.br' and request.path == '/api/':
            return HttpResponseForbidden()
        response = self.get_response(request)
        return response