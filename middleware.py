from .models import ConfiguracionDiseno

class ConfiguracionDisenoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        configuracion = ConfiguracionDiseno.objects.first()
        request.configuracion_diseno = configuracion
        response = self.get_response(request)
        return response