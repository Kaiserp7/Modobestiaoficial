import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from productos.models import Region, Comuna

class Command(BaseCommand):
    help = 'Carga las regiones y comunas desde un archivo JSON'

    def handle(self, *args, **kwargs):
        json_file_path = os.path.join(settings.BASE_DIR, 'static/productos/js/comunas-regiones.json')
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Archivo JSON no encontrado'))
            return
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('Error al decodificar el archivo JSON'))
            return

        # Borrar datos existentes
        Region.objects.all().delete()
        Comuna.objects.all().delete()

        # Cargar regiones y comunas
        for region_data in data.get('regiones', []):
            region, created = Region.objects.get_or_create(nombre=region_data['region'])
            if created:
                self.stdout.write(self.style.SUCCESS(f'Región creada: {region.nombre}'))
            
            for comuna_nombre in region_data.get('comunas', []):
                comuna, created = Comuna.objects.get_or_create(nombre=comuna_nombre, region=region)
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Comuna creada: {comuna.nombre}'))

        self.stdout.write(self.style.SUCCESS('Datos cargados exitosamente'))
