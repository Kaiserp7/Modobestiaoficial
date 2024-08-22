# productos/forms.py

from datetime import timezone
from django import forms
from .models import Comuna, Pedido, Producto, Categoria, Region
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
import re
from .models import Usuario
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario
from .models import Producto
from .models import OfertaCarrusel, Categoria
from .models import Cupon
from .models import ConfiguracionDiseno

class ConfiguracionDisenoForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionDiseno
        fields = ['color_principal', 'color_secundario', 'fuente', 'logo', 'imagen_fondo']
        widgets = {
            'color_principal': forms.TextInput(attrs={'type': 'color'}),
            'color_secundario': forms.TextInput(attrs={'type': 'color'}),
            'fuente': forms.TextInput(attrs={'type': 'text'}),
            'logo': forms.FileInput(),
            'imagen_fondo': forms.FileInput(),
        }
class CuponForm(forms.ModelForm):
    class Meta:
        model = Cupon
        fields = ['nombre', 'cantidad_usuarios', 'tipo', 'descuento', 'fecha_expiracion']
        widgets = {
            'fecha_expiracion': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        descuento = cleaned_data.get('descuento')
        fecha_expiracion = cleaned_data.get('fecha_expiracion')

        # Validación del descuento
        if descuento is not None:
            if descuento < 0 or descuento > 100:
                raise forms.ValidationError('El descuento debe estar entre 0 y 100.')

        # Validación de la fecha de expiración
        if fecha_expiracion and fecha_expiracion < timezone.now().date():
            raise forms.ValidationError('La fecha de expiración no puede ser en el pasado.')

        return cleaned_data
from django import forms
from .models import OfertaCarrusel
from PIL import Image
import os
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO

class OfertaCarruselForm(forms.ModelForm):
    class Meta:
        model = OfertaCarrusel
        fields = ['nombre_oferta', 'categoria', 'fecha_inicio', 'fecha_fin', 'imagen_promocional']
        widgets = {
            'fecha_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_fin': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean_imagen_promocional(self):
        imagen = self.cleaned_data.get('imagen_promocional')

        if imagen:
            with Image.open(imagen) as img:
                # Redimensionamos la imagen al tamaño deseado
                size = (800, 600)  # Ajusta el tamaño según sea necesario
                img = img.resize(size, Image.LANCZOS)  # Reemplaza ANTIALIAS con LANCZOS

                # Convertimos la imagen redimensionada a un archivo en memoria
                output = BytesIO()
                img.save(output, format='JPEG', quality=90)
                output.seek(0)

                # Creamos un nuevo archivo de imagen en memoria
                imagen = InMemoryUploadedFile(
                    output, 
                    'ImageField', 
                    "%s.jpg" % imagen.name.split('.')[0], 
                    'image/jpeg', 
                    output.tell(), 
                    None
                )

        return imagen
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
import re

class RegistroForm(UserCreationForm):
    nombre = forms.CharField(max_length=50)
    apellido = forms.CharField(max_length=50)
    rut = forms.CharField(max_length=12, label='RUT')
    telefono = forms.CharField(max_length=15, label='Número de Teléfono')
    region = forms.ModelChoiceField(queryset=Region.objects.all(), required=True, label='Región')
    comuna = forms.ModelChoiceField(queryset=Comuna.objects.none(), required=False, label='Comuna')
    direccion = forms.CharField(max_length=100, label='Dirección')
    email = forms.EmailField()

    class Meta:
        model = Usuario
        fields = ['username', 'nombre', 'apellido', 'rut', 'telefono', 'region', 'comuna', 'direccion', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'region' in self.data:
            try:
                region_id = int(self.data.get('region'))
                self.fields['comuna'].queryset = Comuna.objects.filter(region_id=region_id).order_by('nombre')
            except (ValueError, TypeError):
                self.fields['comuna'].queryset = Comuna.objects.none()
        elif self.instance.pk:
            self.fields['comuna'].queryset = self.instance.region.comunas.order_by('nombre')

    def clean_rut(self):
        rut = self.cleaned_data['rut']
        if not re.match(r'^\d{1,8}-[\dkK]$', rut):
            raise ValidationError('RUT inválido. Debe tener el formato: 12345678-9.')
        return rut

    def clean_telefono(self):
        telefono = self.cleaned_data['telefono']
        if not re.match(r'^\+569\d{8}$', telefono):
            raise ValidationError('Número de teléfono debe comenzar con +569 seguido de 8 dígitos.')
        return telefono

    def clean(self):
        cleaned_data = super().clean()
        region = cleaned_data.get('region')
        comuna = cleaned_data.get('comuna')

        if region and not comuna:
            raise ValidationError({'comuna': 'Debe seleccionar una comuna para la región seleccionada.'})

        return cleaned_data
    

class CompraInvitadoForm(forms.Form):
    nombre = forms.CharField(max_length=50, label='Nombre')
    apellido = forms.CharField(max_length=50, label='Apellido')
    rut = forms.CharField(max_length=12, label='RUT')
    telefono = forms.CharField(max_length=15, label='Número de Teléfono')
    region = forms.ModelChoiceField(queryset=Region.objects.all(), required=True, label='Región')
    comuna = forms.ModelChoiceField(queryset=Comuna.objects.none(), required=False, label='Comuna')
    direccion = forms.CharField(max_length=100, label='Dirección')
    email = forms.EmailField(label='Correo Electrónico')
    tipo_envio = forms.ChoiceField(choices=Pedido.TIPO_ENVIO_CHOICES, label='Tipo de Envío')
    metodo_pago = forms.ChoiceField(choices=[('transbank', 'Transbank'), ('transferencia', 'Transferencia Bancaria')], label='Método de Pago')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'region' in self.data:
            try:
                region_id = int(self.data.get('region'))
                self.fields['comuna'].queryset = Comuna.objects.filter(region_id=region_id).order_by('nombre')
            except (ValueError, TypeError):
                self.fields['comuna'].queryset = Comuna.objects.none()
        elif 'instance' in kwargs:
            self.fields['comuna'].queryset = kwargs['instance'].region.comunas.order_by('nombre')

    def clean_rut(self):
        rut = self.cleaned_data['rut']
        if not re.match(r'^\d{1,8}-[\dkK]$', rut):
            raise forms.ValidationError('RUT inválido. Debe tener el formato: 12345678-9.')
        return rut

    def clean_telefono(self):
        telefono = self.cleaned_data['telefono']
        if not re.match(r'^\+569\d{8}$', telefono):
            raise forms.ValidationError('Número de teléfono debe comenzar con +569 seguido de 8 dígitos.')
        return telefono

    def clean(self):
        cleaned_data = super().clean()
        region = cleaned_data.get('region')
        comuna = cleaned_data.get('comuna')

        if region and not comuna:
            raise forms.ValidationError({'comuna': 'Debe seleccionar una comuna para la región seleccionada.'})

        return cleaned_data
from django.contrib.auth.forms import UserChangeForm
class ActualizarUsuarioForm(UserChangeForm):
    password = None  # Para no mostrar el campo de contraseña en este formulario
    
    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'rut', 'telefono', 'direccion', 'email']

    def clean_rut(self):
        rut = self.cleaned_data['rut']
        # Validación del RUT
        if not re.match(r'^\d{1,8}-[\dkK]$', rut):
            raise ValidationError('RUT inválido. Debe tener el formato: 12345678-9.')
        return rut

    def clean_telefono(self):
        telefono = self.cleaned_data['telefono']
        # Validación del número de teléfono
        if not re.match(r'^\+569\d{8}$', telefono):
            raise ValidationError('Número de teléfono debe comenzar con +569 seguido de 8 dígitos.')
        return telefono
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'nombre', 'descripcion', 'sabor', 'sabor_secundario', 
            'precio', 'imagen', 'imagen_secundaria', 'categoria', 
            'stock', 'es_oferta', 'descuento', 'fecha_inicio_oferta', 
            'fecha_fin_oferta', 'imagen_oferta'
        ]
        widgets = {
            'fecha_inicio_oferta': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_fin_oferta': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'imagen']

from .models import Slider

class SliderForm(forms.ModelForm):
    class Meta:
        model = Slider
        fields = ['categoria', 'productos', 'imagen_slider', 'imagen_decorativa', 'url_imagen_decorativa']
        widgets = {
            'productos': forms.CheckboxSelectMultiple,  # Permite seleccionar varios productos
        }
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario
from .models import Producto
from .models import OfertaCarrusel, Categoria
from .models import Cupon

class CuponForm(forms.ModelForm):
    class Meta:
        model = Cupon
        fields = ['nombre', 'cantidad_usuarios', 'tipo', 'descuento', 'fecha_expiracion']

    def clean(self):
        cleaned_data = super().clean()
        fecha_expiracion = cleaned_data.get('fecha_expiracion')

        if fecha_expiracion:
            # Asegúrate de que fecha_expiracion esté en formato datetime
            if fecha_expiracion < timezone.now():
                self.add_error('fecha_expiracion', 'La fecha de expiración no puede ser en el pasado.')

        return cleaned_data