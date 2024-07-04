from rest_framework import serializers
from human_app.models import Robos, RobosParametros, Parametros, Rotinas, SelectOptions

class RobosSerializer(serializers.ModelSerializer):
    class Meta:
       model = Robos
       fields = '__all__'

class SelectOptionsSerializer(serializers.ModelSerializer):
    class Meta:
       model = SelectOptions
       fields = '__all__'

class ParametrosSerializer(serializers.ModelSerializer):
    class Meta:
       model = Parametros
       fields = '__all__'

class ParametrosDetailSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
       model = Parametros
       fields = '__all__'
    
    def get_options(self, obj):
        print(obj)
        if obj.tipo == 'SELECT':
            options = SelectOptions.objects.filter(parametro=obj)
            return SelectOptionsSerializer(options, many=True).data
        return None

class RobosParametrosSerializer(serializers.ModelSerializer):
    parametro_info = serializers.SerializerMethodField()
    class Meta:
       model = RobosParametros
       fields = '__all__'
    
    def get_parametro_info(self, obj):
        if obj.parametro.tipo == "SELECT":
            return ParametrosDetailSerializer(obj.parametro).data
        else:
            return ParametrosSerializer(obj.parametro).data

class RotinasSerializer(serializers.ModelSerializer):
    class Meta:
       model = Rotinas
       fields = '__all__'