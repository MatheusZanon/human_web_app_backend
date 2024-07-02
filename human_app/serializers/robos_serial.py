from rest_framework import serializers
from human_app.models import Robos, RobosParametros, Parametros, Rotinas

class RobosSerializer(serializers.ModelSerializer):
    class Meta:
       model = Robos
       fields = '__all__'

class ParametrosSerializer(serializers.ModelSerializer):
    class Meta:
       model = Parametros
       fields = '__all__'

class RobosParametrosSerializer(serializers.ModelSerializer):
    parametro_info = ParametrosSerializer(source='parametro', read_only=True)
    class Meta:
       model = RobosParametros
       fields = '__all__'

class RotinasSerializer(serializers.ModelSerializer):
    class Meta:
       model = Rotinas
       fields = '__all__'