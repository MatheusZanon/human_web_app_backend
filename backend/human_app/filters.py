from django_filters import rest_framework as filters
from .models import *

class IntervaloDeTempoFilter(filters.FilterSet):
  mes_inicio = filters.NumberFilter(field_name='mes', lookup_expr='gte')
  ano_inicio = filters.NumberFilter(field_name='ano', lookup_expr='gte')
  mes_fim = filters.NumberFilter(field_name='mes', lookup_expr='lte')
  ano_fim = filters.NumberFilter(field_name='ano', lookup_expr='lte')

  class Meta:
    model = ClientesFinanceiroValores
    fields = ['mes_inicio', 'ano_inicio', 'mes_fim', 'ano_fim']