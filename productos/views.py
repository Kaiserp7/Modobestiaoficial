from decimal import Decimal, InvalidOperation
import json
import os
from io import BytesIO
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.lib.units import inch
from django.conf import settings
from django.views.decorators.http import require_POST
from datetime import datetime
from .models import Comuna, Pedido, Region, Usuario
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from wtforms import ValidationError
from .models import EstadisticasVentas, HistorialVentas, Oferta, OfertaCarrusel, PedidoProducto, Producto, Categoria, Venta, Carrito, Pedido 
from .forms import  ProductoForm, CategoriaForm, RegistroForm, SliderForm
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib.pagesizes import letter
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from io import BytesIO
from django.contrib.auth.decorators import login_required
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer
from .models import Pedido
from django.conf import settings
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
from .forms import OfertaCarruselForm
from .forms import CuponForm
from .models import Cupon
from PIL import Image
from .forms import CompraInvitadoForm
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'cambiar_contraseña.html'  # Nombre del archivo de plantilla
    success_url = reverse_lazy('password_change_done')
@login_required
def agregar_cupon(request):
    if request.method == 'POST':
        form = CuponForm(request.POST)
        if form.is_valid():
            cupon = form.save()
            messages.success(request, 'Cupón creado exitosamente.')
            return redirect('agregar_cupon')
        else:
            messages.error(request, 'Error al crear el cupón.')
    else:
        form = CuponForm()
    return render(request, 'productos/crear_cupon.html', {'form': form})
def agregar_al_carrito(request, producto_id):
    response_data = {
        'success': False,
        'messages': []
    }

    try:
        producto = get_object_or_404(Producto, id=producto_id)

        if not request.user.is_authenticated:
            # Redirige a una página que pregunta si quiere iniciar sesión o comprar como invitado
            request.session['producto_id'] = producto_id
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            usuario = None
        else:
            usuario = request.user
            session_key = None

        if request.method == 'POST':
            cantidad = request.POST.get('cantidad', 1)
            sabor = request.POST.get('sabor')  # Obtener el sabor del formulario

            if not cantidad:
                response_data['messages'].append({
                    'icon': 'error',
                    'title': 'Error',
                    'text': 'Debe especificar una cantidad.'
                })
                return JsonResponse(response_data)

            try:
                cantidad = int(cantidad)
                if cantidad < 1:
                    response_data['messages'].append({
                        'icon': 'error',
                        'title': 'Error',
                        'text': 'La cantidad debe ser al menos 1.'
                    })
                    return JsonResponse(response_data)
            except ValueError:
                response_data['messages'].append({
                    'icon': 'error',
                    'title': 'Error',
                    'text': 'La cantidad debe ser un número entero.'
                })
                return JsonResponse(response_data)

            if producto.stock < cantidad:
                response_data['messages'].append({
                    'icon': 'error',
                    'title': 'Error',
                    'text': 'No hay stock disponible.'
                })
                return JsonResponse(response_data)

            carrito_item, created = Carrito.objects.get_or_create(
                usuario=usuario,
                session_key=session_key,
                producto=producto,
                sabor=sabor,
                defaults={'cantidad': cantidad}
            )

            if not created:
                if carrito_item.cantidad + cantidad > producto.stock:
                    response_data['messages'].append({
                        'icon': 'error',
                        'title': 'Error',
                        'text': 'La cantidad solicitada supera el stock disponible.'
                    })
                    return JsonResponse(response_data)
                carrito_item.cantidad += cantidad
                carrito_item.save()
            else:
                carrito_item.cantidad = cantidad
                carrito_item.save()

            response_data['success'] = True
            response_data['messages'].append({
                'icon': 'success',
                'title': 'Éxito',
                'text': 'Producto agregado al carrito exitosamente.'
            })

            carrito_items = Carrito.objects.filter(usuario=usuario) if usuario else Carrito.objects.filter(session_key=session_key)
            carrito_total = sum(item.producto.precio_con_descuento() * item.cantidad for item in carrito_items)
            response_data['carrito_total'] = carrito_total

            return JsonResponse(response_data)

        else:
            response_data['messages'].append({
                'icon': 'error',
                'title': 'Error',
                'text': 'Método de solicitud no permitido.'
            })
            return JsonResponse(response_data)
    except Exception as e:
        response_data['messages'].append({
            'icon': 'error',
            'title': 'Error',
            'text': f'Ocurrió un error inesperado: {str(e)}'
        })
        return JsonResponse(response_data)
def index(request):
    ahora = timezone.now()
    # Obtener solo las ofertas que están actualmente activas
    ofertas_activas = OfertaCarrusel.objects.filter(fecha_inicio__lte=ahora, fecha_fin__gte=ahora)

    categorias = Categoria.objects.all()

    return render(request, 'productos/index.html', {
        'ofertas': ofertas_activas,
        'categorias': categorias
    })
 

def logout_view(request):
    logout(request)
    return redirect('index')

# Vista de detalle del producto
def product_detail(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    now = timezone.now()
    context = {
        'producto': producto,
        'now': now,
    }
    return render(request, 'productos/product_detail.html', context)

from django.db.models import Q
# Vista de productos por categoría
def category(request, categoria_id):
    # Obtener la categoría usando get_object_or_404 para manejar errores de forma adecuada
    categoria = get_object_or_404(Categoria, id=categoria_id)
    productos = Producto.objects.filter(categoria=categoria)

    # Obtener filtros de la solicitud GET
    query = request.GET.get('q')
    precio_min = request.GET.get('precio_min')
    precio_max = request.GET.get('precio_max')
    ordenar = request.GET.get('ordenar')

    # Aplicar filtros de búsqueda
    if query:
        productos = productos.filter(Q(nombre__icontains=query) | Q(descripcion__icontains=query))

    # Aplicar filtros de precio
    if precio_min:
        try:
            precio_min = float(precio_min)
            productos = productos.filter(precio__gte=precio_min)
        except ValueError:
            pass  # Ignorar si no se puede convertir a float

    if precio_max:
        try:
            precio_max = float(precio_max)
            productos = productos.filter(precio__lte=precio_max)
        except ValueError:
            pass  # Ignorar si no se puede convertir a float

    # Aplicar ordenamiento
    if ordenar == 'menor_a_mayor':
        productos = productos.order_by('precio')
    elif ordenar == 'mayor_a_menor':
        productos = productos.order_by('-precio')

    context = {
        'categoria': categoria,
        'productos': productos
    }

    return render(request, 'productos/category.html', context)

# Vista de creación de productos (solo para administradores)
@login_required
def create_product(request):
    if not request.user.is_superuser:
        return redirect('index')

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = ProductoForm()
    return render(request, 'productos/create_product.html', {'form': form})

# Vista de creación de categorías (solo para administradores)
@login_required
def create_category(request):
    if not request.user.is_superuser:
        return redirect('index')

    if request.method == 'POST':
        form = CategoriaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = CategoriaForm()
    return render(request, 'productos/create_category.html', {'form': form})

# Vista de historial de ventas (solo para administradores)
@login_required
@user_passes_test(lambda u: u.is_superuser)
def sales_history(request):
    ventas = Venta.objects.all().order_by('-fecha')
    return render(request, 'productos/sales_history.html', {'ventas': ventas})
import requests

def register(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')  # Redirige a la página de inicio o a otra página
        else:
            # Imprime los errores del formulario para depurar
            print("Form errors:", form.errors)
    else:
        form = RegistroForm()

    # Obtener regiones y comunas para inicializar los selectores
    regiones = Region.objects.all()
    comunas = Comuna.objects.all()
    return render(request, 'registration/register.html', {
        'form': form,
        'regiones': regiones,
        'comunas': comunas,
    })
def get_comunas(request):
    region_nombre = request.GET.get('region_nombre', '')
    if region_nombre:
        region = Region.objects.filter(nombre=region_nombre).first()
        comunas = Comuna.objects.filter(region=region).values_list('nombre', flat=True) if region else []
    else:
        comunas = []
    
    regiones = Region.objects.values_list('nombre', flat=True)
    
    return JsonResponse({
        'regiones': list(regiones),
        'comunas': list(comunas)
    })

    try:
        # Consultar las regiones
        url_regiones = 'https://apis.digital.gob.cl/dpa/regiones/'
        response_regiones = requests.get(url_regiones)
        regiones = response_regiones.json()

        # Crear un diccionario para almacenar la información de las regiones y comunas
        datos = {'regiones': []}

        for region in regiones:
            codigo_region = region['codigo']
            nombre_region = region['nombre']
            
            # Consultar las comunas para la región actual
            url_comunas = f'https://apis.digital.gob.cl/dpa/comunas?region={codigo_region}'
            response_comunas = requests.get(url_comunas)
            comunas = response_comunas.json()

            datos['regiones'].append({
                'region': nombre_region,
                'comunas': [comuna['nombre'] for comuna in comunas]
            })

        return JsonResponse(datos)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'productos/login.html', {'form': form})

# Cierre de sesión de usuarios
def logout_view(request):
    logout(request)
    return redirect('index')

# Vista de productos por categoría
def ver_productos_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    productos = Producto.objects.filter(categoria=categoria)
    return render(request, 'productos/ver_productos_categoria.html', {'categoria': categoria, 'productos': productos})

# Edición de productos (solo para administradores)
@login_required
def edit_product(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('product_detail', producto_id=producto.id)
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'productos/edit_product.html', {'form': form, 'producto': producto})

# Eliminación de productos (solo para administradores)
@login_required
def delete_product(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        producto.delete()
        return redirect('index')
    return render(request, 'productos/delete_product.html', {'producto': producto})

from django.core.files.storage import default_storage
def ver_carrito(request):
    if not request.user.is_authenticated:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        carrito_items = Carrito.objects.filter(usuario__isnull=True, session_key=session_key)
        pedido = None
    else:
        carrito_items = Carrito.objects.filter(usuario=request.user)
        pedido, created = Pedido.objects.get_or_create(
            usuario=request.user,
            estado='carrito',
            defaults={'tipo_envio': 'domicilio_registro'}
        )

    total_carrito = sum(item.producto.precio_con_descuento() * item.cantidad for item in carrito_items)
    subtotal_por_producto = {
        item.id: item.producto.precio_con_descuento() * item.cantidad
        for item in carrito_items
    }

    subtotal_items = [(item_id, subtotal) for item_id, subtotal in subtotal_por_producto.items()]

    cupon = request.POST.get('cupon', None)
    if cupon:
        try:
            cupon_obj = Cupon.objects.get(nombre=cupon)
            total_carrito = cupon_obj.aplicar_cupon(total_carrito)
            cupon_obj.usar_cupon()
            messages.success(request, 'Cupón aplicado correctamente.')
        except Cupon.DoesNotExist:
            messages.error(request, 'Cupón no válido.')

    if request.method == 'POST':
        tipo_envio = request.POST.get('tipo_envio')
        if tipo_envio in dict(Pedido.TIPO_ENVIO_CHOICES).keys():
            if pedido:
                pedido.tipo_envio = tipo_envio
                if tipo_envio == 'retiro_sucursal':
                    pedido.direccion_envio = ''
                else:
                    pedido.direccion_envio = request.user.direccion
                pedido.save()
                messages.success(request, 'Tipo de envío actualizado correctamente.')

                # Manejar el comprobante si se seleccionó transferencia bancaria
                if tipo_envio == 'transferencia_bancaria':
                    if 'comprobante' in request.FILES:
                        comprobante = request.FILES['comprobante']
                        # Guarda el comprobante en el sistema de archivos
                        path = default_storage.save('comprobantes/' + comprobante.name, comprobante)
                        # Aquí puedes hacer algo con el archivo guardado, como asociarlo al pedido
                        messages.success(request, 'Comprobante subido correctamente.')
                    else:
                        messages.error(request, 'Debe subir un comprobante.')

            return redirect('ver_carrito')
        else:
            messages.error(request, 'Opción de tipo de envío no válida.')

    tipo_envio_choices = Pedido.TIPO_ENVIO_CHOICES if pedido else []

    context = {
        'carrito_items': carrito_items,
        'total_carrito': total_carrito,
        'total_carrito_con_descuento': total_carrito - (pedido.descuento if pedido else 0),
        'pedido': pedido,
        'tipo_envio_choices': tipo_envio_choices,
        'subtotal_items': subtotal_items,
    }

    return render(request, 'productos/carrito.html', context)
@login_required
def limpiar_carrito(request):
    # Eliminar todos los elementos del carrito para el usuario
    Carrito.objects.filter(usuario=request.user).delete()
    messages.success(request, 'Carrito limpiado correctamente.')
    return redirect('ver_carrito')
def estado_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    subtotales = []
    total_sin_descuento = 0

    for item in pedido.productos.all():
        subtotal = item.cantidad * item.producto.precio_con_descuento()  # Llama al método con paréntesis
        subtotales.append({
            'producto': item.producto,
            'cantidad': item.cantidad,
            'subtotal': subtotal
        })
        total_sin_descuento += subtotal

    # Aplica descuento si hay
    descuento_aplicado = pedido.descuento_aplicado if pedido.descuento_aplicado else 0
    total_con_descuento = total_sin_descuento - descuento_aplicado

    return render(request, 'productos/estado_pedido.html', {
        'pedido': pedido,
        'subtotales': subtotales,
        'total_pedido': total_con_descuento,
        'descuento_aplicado': descuento_aplicado
    })

@login_required
def eliminar_del_carrito(request, item_id):
    if request.method == 'POST':
        try:
            item = Carrito.objects.get(id=item_id, usuario=request.user)
            item.delete()
            carrito_items = Carrito.objects.filter(usuario=request.user)
            total_carrito = sum(item.producto.precio * item.cantidad for item in carrito_items)
            return JsonResponse({
                'success': True,
                'message': 'Producto eliminado del carrito correctamente.',
                'carrito_total': total_carrito
            })
        except Carrito.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'El producto no existe en el carrito.'})
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})

# Sistema de gestión de pedidos
@login_required
@user_passes_test(lambda u: u.is_superuser)
def gestionar_pedidos(request):
    # Obtener el valor de búsqueda del query param 'q' desde la URL
    query = request.GET.get('q')

    # Filtrar los pedidos en función de la búsqueda
    if query:
        pedidos = Pedido.objects.filter(
            Q(id__icontains=query) |  # Filtrar por ID de pedido
            Q(usuario__username__icontains=query) |  # Filtrar por nombre de usuario
            Q(estado__icontains=query)  # Filtrar por estado del pedido
        )
    else:
        pedidos = Pedido.objects.all()

    # Calcular el valor total de cada pedido
    for pedido in pedidos:
        total_pedido = sum(item.producto.precio * item.cantidad for item in pedido.productos.all())
        pedido.valor_total = total_pedido  # Añadimos un atributo dinámico al objeto pedido
    
    context = {
        'pedidos': pedidos,
        'query': query,  # Pasar el valor de búsqueda al contexto para mantenerlo en el formulario
    }
    return render(request, 'productos/gestionar_pedidos.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def aprobar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    try:
        # Cambiar el estado del pedido a 'aceptado'
        pedido.estado = 'aceptado'
        pedido.save()

        # Guardar en el historial de ventas
        historial_venta = HistorialVentas(pedido=pedido, usuario=pedido.usuario, valor_total=pedido.total_compras)
        historial_venta.save()

        # Actualizar las estadísticas de ventas
        for item in pedido.productos.all():
            producto = item.producto
            estadisticas, created = EstadisticasVentas.objects.get_or_create(producto=producto)
            estadisticas.cantidad_vendida += item.cantidad
            estadisticas.total_ventas_diarias = 0
            estadisticas.total_ventas_semanales = 0
            estadisticas.total_ventas_mensuales = 0
            estadisticas.actualizar_estadisticas()

        # Enviar un correo al usuario notificando la aprobación
        subject = 'Pedido Aprobado'
        message = f'Estimado {pedido.usuario.username},\n\nTu pedido ha sido aprobado y está en proceso de preparación.'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [pedido.usuario.email]
        
        send_mail(subject, message, from_email, recipient_list)

        # Redirigir a la página de gestión de pedidos
        return redirect('gestionar_pedidos')

    except Exception as e:
        # Manejo de errores si algo sale mal
        print(f"Error al aprobar pedido: {e}")
        return redirect('gestionar_pedidos')
@login_required
@user_passes_test(lambda u: u.is_superuser)
def cancelar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    try:
        # Actualiza el stock de los productos asociados al pedido
        for item in pedido.productos.all():
            item.producto.stock += item.cantidad
            item.producto.save()

        # Cambiar el estado del pedido a 'cancelado'
        pedido.estado = 'cancelado'
        pedido.save()

        # Enviar un correo al usuario notificando la cancelación
        subject = 'Pedido Cancelado'
        message = f'Estimado {pedido.usuario.username},\n\nTu pedido ha sido cancelado. Para más información, por favor contacta con soporte.'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [pedido.usuario.email]

        send_mail(subject, message, from_email, recipient_list)

        # Redirigir a la página de gestión de pedidos
        return redirect('gestionar_pedidos')

    except Exception as e:
        # Manejo de errores si algo sale mal
        print(f"Error al cancelar pedido: {e}")
        return redirect('gestionar_pedidos')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def eliminar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    pedido.delete()
    return redirect('gestionar_pedidos')
@login_required
def some_view(request):
    # Obtener el pedido activo del usuario actual si está autenticado
    pedido_activo = Pedido.objects.filter(usuario=request.user, estado='activo').first()

    return render(request, 'base.html', {'pedido_activo': pedido_activo})

@login_required
def mis_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-fecha')

    context = {
        'pedidos': pedidos,
    }
    return render(request, 'productos/mis_pedidos.html', context)

@login_required
def actualizar_tipo_envio(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    if request.method == 'POST':
        tipo_envio = request.POST.get('tipo_envio')

        response_data = {
            'success': False,
            'messages': []
        }

        if tipo_envio in dict(Pedido.TIPO_ENVIO_CHOICES).keys():
            pedido.tipo_envio = tipo_envio
            pedido.save()

            if tipo_envio == 'retiro_sucursal':
                pedido.direccion_envio = None
                pedido.save()

            response_data['success'] = True
            response_data['messages'].append({
                'icon': 'success',
                'title': 'Éxito',
                'text': 'Tipo de envío actualizado correctamente.'
            })
            response_data['redirect'] = reverse('ver_carrito')

        else:
            response_data['messages'].append({
                'icon': 'error',
                'title': 'Error',
                'text': 'Opción de tipo de envío no válida.'
            })

        return JsonResponse(response_data)

    return JsonResponse({
        'success': False,
        'messages': [{
            'icon': 'error',
            'title': 'Error',
            'text': 'Método no permitido.'
        }]
    })


def eliminar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    if request.method == 'POST':
        # Actualiza el stock de los productos antes de eliminar el pedido
        for item in pedido.productos.all():
            item.producto.stock += item.cantidad
            item.producto.save()

        # Elimina el pedido
        pedido.delete()
        messages.success(request, 'El pedido ha sido eliminado exitosamente.')
        return redirect('gestionar_pedidos')
    
    return render(request, 'productos/eliminar_pedido_confirmacion.html', {'pedido': pedido})

# views.py
def actualizar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    if request.method == 'POST':
        tipo_envio = request.POST.get('tipo_envio')
        
        if tipo_envio == 'retiro_sucursal':
            pedido.tipo_envio = 'retiro_sucursal'
        elif tipo_envio == 'domicilio_registro':
            pedido.tipo_envio = 'domicilio_registro'
        
        pedido.save()
        return redirect('estado_pedido', pedido_id=pedido.id)
    
    return render(request, 'actualizar_pedido.html', {'pedido': pedido})


@login_required
def eliminar_del_carrito(request, item_id):
    item = get_object_or_404(Carrito, id=item_id, usuario=request.user)
    item.delete()
    
    response_data = {
        'success': True,
        'message': {
            'icon': 'success',
            'title': 'Éxito',
            'text': 'Producto eliminado del carrito.'
        },
        'carrito_total': calcular_total_carrito(request.user)
    }
    return JsonResponse(response_data)

@login_required
def modificar_cantidad(request, item_id):
    item = get_object_or_404(Carrito, id=item_id, usuario=request.user)
    response_data = {'success': False, 'messages': []}
    
    if request.method == 'POST':
        nueva_cantidad = request.POST.get('cantidad')
        
        try:
            nueva_cantidad = int(nueva_cantidad)
            if nueva_cantidad < 1:
                response_data['messages'].append({
                    'icon': 'error',
                    'title': 'Error',
                    'text': 'La cantidad debe ser al menos 1.'
                })
            elif nueva_cantidad > item.producto.stock:
                response_data['messages'].append({
                    'icon': 'error',
                    'title': 'Error',
                    'text': 'La cantidad solicitada supera el stock disponible.'
                })
            else:
                item.cantidad = nueva_cantidad
                item.save()
                response_data['success'] = True
                response_data['messages'].append({
                    'icon': 'success',
                    'title': 'Éxito',
                    'text': 'Cantidad actualizada correctamente.'
                })
                response_data['carrito_total'] = calcular_total_carrito(request.user)
        except ValueError:
            response_data['messages'].append({
                'icon': 'error',
                'title': 'Error',
                'text': 'La cantidad debe ser un número entero.'
            })

        return JsonResponse(response_data)

    return redirect('ver_carrito')

def calcular_total_carrito(usuario):
    # Calcula el total del carrito para el usuario actual
    carrito_items = Carrito.objects.filter(usuario=usuario)
    total = sum(Decimal(item.producto.precio_con_descuento()) * item.cantidad for item in carrito_items)
    
    # Convertir el total a float para asegurar la serialización JSON
    return float(total)
def calcular_total_pedido(pedido):
    # Calcula el total del pedido, aplicando descuento si es necesario
    total = sum(item.producto.precio_con_descuento() * item.cantidad for item in pedido.productos.all())
    if pedido.descuento:
        total -= total * (pedido.descuento / 100)
    return total



def gestionar_slider(request):
    if request.method == 'POST':
        form = SliderForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('gestionar_slider')  # Redirige a la misma página o a otra que desees
    else:
        form = SliderForm()
    
    categorias = Categoria.objects.all()
    return render(request, 'productos/gestionar_slider.html', {'form': form, 'categorias': categorias})
from reportlab.platypus import Image 
def exportar_boleta_pdf(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []

    styles = getSampleStyleSheet()
    centered_style = ParagraphStyle(name="Centered", alignment=TA_CENTER, fontSize=12, spaceAfter=10)
    title_style = ParagraphStyle(name="Title", alignment=TA_CENTER, fontSize=14, fontName='Helvetica-Bold', spaceAfter=15)
    subtitle_style = ParagraphStyle(name="Subtitle", alignment=TA_CENTER, fontSize=12, fontName='Helvetica', spaceAfter=10)
    
    # Estilo para texto en la tabla
    table_text_style = ParagraphStyle(name="TableText", fontName='Helvetica', fontSize=10, alignment=1, spaceAfter=5)

    # Agregar el logo centrado
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'productos', 'logo', 'logo3.png')
    if os.path.exists(logo_path):
        logo_image = Image(logo_path, width=150, height=80)
        logo_image.hAlign = 'CENTER'
        story.append(logo_image)

    # Añadir la fecha de emisión de la boleta
    story.append(Spacer(1, 12))
    current_date = datetime.now().strftime("%d/%m/%Y")
    story.append(Paragraph(f"Fecha: {current_date}", centered_style))

    # Agregar título centrado
    story.append(Spacer(1, 12))
    story.append(Paragraph("Detalles de la Boleta", title_style))

    # Agregar detalles del pedido
    pedido_data = [['Producto', 'Cantidad', 'Precio Unitario', 'Subtotal']]
    for item in pedido.productos.all():
        producto = item.producto
        subtotal = item.cantidad * producto.precio
        pedido_data.append([
            Paragraph(producto.nombre, table_text_style),
            str(item.cantidad),
            f"${producto.precio:,.0f}",
            f"${subtotal:,.0f}"
        ])

    # Ajustar el ancho de las columnas
    col_widths = [3 * inch, 1 * inch, 1.5 * inch, 1.5 * inch]

    # Crear tabla con los detalles del pedido
    table = Table(pedido_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(table)

    # Agregar total centrado
    total = sum(item.cantidad * item.producto.precio for item in pedido.productos.all())
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Total: ${total:,.0f}", title_style))

    # Generar código QR y agregarlo al PDF
    qr_code_url = request.build_absolute_uri(f"/pedido/{pedido.id}/")
    qr_code_img = qrcode.make(qr_code_url)

    qr_buffer = BytesIO()
    qr_code_img.save(qr_buffer)
    qr_buffer.seek(0)

    qr_code_image = Image(qr_buffer)
    qr_code_image.hAlign = 'CENTER'
    qr_code_image.drawHeight = 1.5 * inch
    qr_code_image.drawWidth = 1.5 * inch
    story.append(Spacer(1, 12))
    story.append(qr_code_image)

    # Agregar pie de página con información adicional
    story.append(Spacer(1, 24))
    footer = Paragraph("Gracias por su compra. Para más información, visite nuestro sitio web o contáctenos.", subtitle_style)
    story.append(footer)

    # Construir el PDF
    doc.build(story)

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="boleta_{pedido.id}.pdf"'
    return response
@login_required
@user_passes_test(lambda u: u.is_superuser)
def estadisticas_productos(request):
    estadisticas = EstadisticasVentas.objects.all().order_by('-cantidad_vendida')
    return render(request, 'productos/estadisticas_productos.html', {'estadisticas': estadisticas})
@login_required
@user_passes_test(lambda u: u.is_superuser)
def ventas_diarias(request):
    hoy = timezone.now().date()
    ventas = Pedido.objects.filter(fecha__date=hoy).aggregate(total_ventas=Sum('total_compras'))
    return render(request, 'ventas_diarias.html', {'total_ventas': ventas['total_ventas']})
@login_required
@user_passes_test(lambda u: u.is_superuser)
def ventas_semanales(request):
    hoy = timezone.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    ventas = Pedido.objects.filter(fecha__date__range=[inicio_semana, fin_semana]).aggregate(total_ventas=Sum('total_compras'))
    return render(request, 'ventas_semanales.html', {'total_ventas': ventas['total_ventas']})
@login_required
@user_passes_test(lambda u: u.is_superuser)
def ventas_mensuales(request):
    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)
    fin_mes = (inicio_mes + timedelta(days=31)).replace(day=1) - timedelta(days=1)
    ventas = Pedido.objects.filter(fecha__date__range=[inicio_mes, fin_mes]).aggregate(total_ventas=Sum('total_compras'))
    return render(request, 'ventas_mensuales.html', {'total_ventas': ventas['total_ventas']})
@login_required
@user_passes_test(lambda u: u.is_superuser)
def historial_y_estadisticas(request):
    hoy = timezone.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    inicio_mes = hoy.replace(day=1)
    fin_mes = (inicio_mes + timedelta(days=31)).replace(day=1) - timedelta(days=1)
    
    ventas_diarias = Pedido.objects.filter(fecha__date=hoy).aggregate(total_ventas=Sum('total_compras'))
    ventas_semanales = Pedido.objects.filter(fecha__date__range=[inicio_semana, fin_semana]).aggregate(total_ventas=Sum('total_compras'))
    ventas_mensuales = Pedido.objects.filter(fecha__date__range=[inicio_mes, fin_mes]).aggregate(total_ventas=Sum('total_compras'))
    historial_ventas = Pedido.objects.all()

    context = {
        'ventas_diarias': ventas_diarias['total_ventas'],
        'ventas_semanales': ventas_semanales['total_ventas'],
        'ventas_mensuales': ventas_mensuales['total_ventas'],
        'historial_ventas': historial_ventas,
    }
    return render(request, 'productos/historial_y_estadisticas.html', context)
@login_required
@user_passes_test(lambda u: u.is_superuser)
def detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    return render(request, 'productos/detalle_pedido.html', {'pedido': pedido})
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import OfertaCarruselForm
from .models import OfertaCarrusel

@login_required
@user_passes_test(lambda u: u.is_superuser)
def agregar_oferta_carrusel(request):
    if request.method == 'POST':
        form = OfertaCarruselForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('agregar_oferta_carrusel')  # Redirige a la misma página
    else:
        form = OfertaCarruselForm()

    ofertas = OfertaCarrusel.objects.all()
    return render(request, 'productos/agregar_oferta_carrusel.html', {
        'form': form,
        'ofertas': ofertas
    })

def carrusel_ofertas(request):
    ofertas = OfertaCarrusel.objects.filter(esta_activa=True)
    return render(request, 'productos/carrusel_ofertas.html', {'ofertas': ofertas})


@login_required(login_url='/mostrar-alerta/')
def pagina_protegida(request):
    # Lógica de la página
    return render(request, 'pagina_protegida.html')

def mostrar_alerta(request):
    return render(request, 'productos/mostrar_alerta.html')
def verificar_autenticacion(request):
    if request.user.is_authenticated:
        return JsonResponse({'autenticado': True})
    else:
        return JsonResponse({'autenticado': False})
    
def productos_lista(request):
    # Obtener el término de búsqueda
    query = request.GET.get('q', '')
    min_precio = request.GET.get('min_precio', None)
    max_precio = request.GET.get('max_precio', None)
    orden = request.GET.get('orden', 'asc')

    # Filtrar productos por búsqueda y precio
    productos = Producto.objects.filter(nombre__icontains=query)
    if min_precio:
        productos = productos.filter(precio__gte=min_precio)
    if max_precio:
        productos = productos.filter(precio__lte=max_precio)

    # Ordenar los productos según el parámetro de orden
    if orden == 'desc':
        productos = productos.order_by('-precio')
    else:
        productos = productos.order_by('precio')

    return render(request, 'productos/productos_lista.html', {
        'productos': productos
    })
def search_products(request):
    query = request.GET.get('query', '')
    min_price = request.GET.get('min_price', '0')
    max_price = request.GET.get('max_price', '1000000')  # Valor alto para simular infinito
    order_by = request.GET.get('order_by', 'nombre')

    try:
        min_price = Decimal(min_price)
        max_price = Decimal(max_price)
    except (ValidationError, ValueError):
        min_price = Decimal('0')
        max_price = Decimal('1000000')  # Valor alto para simular infinito

    # Filtrar productos según la búsqueda
    productos = Producto.objects.filter(
        nombre__icontains=query,
        precio__gte=min_price,
        precio__lte=max_price
    ).order_by(order_by)

    return render(request, 'productos/search_results.html', {'productos': productos})

def filter_products(request):
    query = request.GET.get('query', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    order_by = request.GET.get('order_by', 'nombre')

    # Definir valores predeterminados para min_price y max_price
    default_min_price = Decimal('0')
    default_max_price = Decimal('1000000')  # Valor alto para simular infinito

    try:
        if min_price:
            min_price = Decimal(min_price)
        else:
            min_price = default_min_price
        
        if max_price:
            max_price = Decimal(max_price)
        else:
            max_price = default_max_price

    except (ValidationError, ValueError, InvalidOperation) as e:
        min_price = default_min_price
        max_price = default_max_price
        print(f"Error converting price values: {e}")

    # Construir la consulta base con el filtro de búsqueda
    productos_query = Producto.objects.all()

    if query:
        productos_query = productos_query.filter(nombre__icontains=query)

    # Aplicar filtros de precio
    productos_query = productos_query.filter(
        precio__gte=min_price,
        precio__lte=max_price
    )

    # Aplicar ordenamiento
    if order_by == 'price_asc':
        productos_query = productos_query.order_by('precio')
    elif order_by == 'price_desc':
        productos_query = productos_query.order_by('-precio')
    else:
        productos_query = productos_query.order_by(order_by)

    return render(request, 'productos/search_results.html', {'productos': productos_query})

def aplicar_cupon(request):
    if request.method == 'POST':
        codigo_cupon = request.POST.get('codigo_cupon', '').strip()
        try:
            cupon = Cupon.objects.get(nombre=codigo_cupon)
        except Cupon.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Cupón no válido.'})

        pedido = get_object_or_404(Pedido, usuario=request.user, estado='carrito')

        if cupon.tipo == 'unico' and cupon.cantidad_usuarios <= 0:
            return JsonResponse({'success': False, 'message': 'El cupón ha sido usado por todos los usuarios permitidos.'})

        # Calcular el total con el descuento
        total_carrito = calcular_total_carrito(request.user)
        descuento = cupon.descuento
        total_con_descuento = total_carrito - (total_carrito * (descuento / 100))

        # Actualizar el pedido con el descuento aplicado
        pedido.descuento = descuento
        pedido.total_compras = total_con_descuento
        pedido.save()

        # Guardar el total con descuento en la sesión (convertir a miles)
        total_con_descuento_miles = int(round(total_con_descuento / 1))  # Convertir a miles
        request.session['total_con_descuento'] = total_con_descuento_miles

        return JsonResponse({
            'success': True,
            'message': f'Cupón aplicado: {cupon.nombre}',
            'descuento': descuento,
            'total': f"${total_con_descuento:,.0f}"  # Mostrar en pesos chilenos
        })
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})
from django.views.decorators.http import require_GET
@csrf_exempt
@login_required
@require_GET
def get_cart_item_count(request):
    try:
        items = Carrito.objects.filter(usuario=request.user)
        total_count = sum(item.cantidad for item in items)
        return JsonResponse({'cart_item_count': total_count})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

from django.shortcuts import render, redirect
from transbank.webpay.webpay_plus.transaction import Transaction


def retorno_pago(request):
    token = request.GET.get('token_ws')

    tx = Transaction()
    response = tx.commit(token=token)
    
    if response['status'] == 'AUTHORIZED':
        # Pago exitoso, procesar la orden aquí
        return redirect('estado_pedido')
    else:
        # Manejar el error de pago aquí
        return render(request, 'productos/error_pago.html', {'response': response})




from django.shortcuts import redirect
from django.contrib import messages

def actualizar_metodo_pago(request):
    if request.method == 'POST':
        # Lógica para actualizar el método de pago
        pedido = Pedido.objects.get(usuario=request.user, estado='en_proceso')
        pedido.metodo_pago = request.POST.get('metodo_pago')
        pedido.save()
        return redirect('ver_carrito')  # Asegúrate de que 'ver_carrito' esté definida correctamente en tus URLs

    return redirect('ver_carrito')

import logging
from django.shortcuts import redirect, render
from django.conf import settings
from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.options import WebpayOptions
from transbank.common.integration_type import IntegrationType
def iniciar_pago(request, order_id):
    # Obtener el total con descuento de la sesión
    total_con_descuento_miles = request.session.get('total_con_descuento', None)

    if total_con_descuento_miles is not None:
        # Eliminar el valor de la sesión después de usarlo
        del request.session['total_con_descuento']
    else:
        # Calcular el total del carrito sin descuento si no hay en la sesión
        total_carrito = calcular_total_carrito(request.user)
        total_con_descuento_miles = int(round(total_carrito / 1))  # Convertir a miles
    
    # Configurar las opciones para Transbank
    tx = Transaction(WebpayOptions(
        commerce_code=settings.TRANSBANK_COMMERCE_CODE,
        api_key=settings.TRANSBANK_API_KEY,
        integration_type=settings.TRANSBANK_ENVIRONMENT
    ))

    buy_order = f"ORDER-{order_id}"
    session_id = str(request.user.id)
    return_url = request.build_absolute_uri('/webpay-plus/commit/')

    try:
        # Crear la transacción
        response = tx.create(buy_order, session_id, total_con_descuento_miles, return_url)

        # Verificar la respuesta de Transbank
        if 'token' in response and 'url' in response:
            return redirect(response['url'] + '?token_ws=' + response['token'])
        else:
            logging.error("La respuesta de Transbank no contiene los campos esperados: %s", response)
            return render(request, 'productos/error.html', {
                'message': 'Error al iniciar transacción con Transbank',
                'response': response
            })

    except Exception as e:
        logging.error("Error al procesar el pago con Transbank: %s", str(e))
        return render(request, 'productos/error.html', {'message': f'Error: {str(e)}'})


def pago_exitoso(request):
    token = request.GET.get('token_ws')

    # Confirma la transacción con Transbank
    response = Transaction.commit(token=token)

    if response['status'] == 'AUTHORIZED':
        # Marca el pedido como pagado
        pedido = Pedido.objects.get(id=response['buy_order'])
        pedido.estado = 'pagado'
        pedido.save()

        # Redirige al usuario al estado del pedido
        return redirect('estado_pedido')
    else:
        return redirect('pago_fallido')
    
def pago_fallido(request):
    return render(request, 'productos/pago_fallido.html')

def confirmar_pago(request):
    # Asegúrate de que el token esté presente en la solicitud
    token_ws = request.GET.get('token_ws', None)

    if token_ws is None:
        logging.error("El token de Transbank no se encuentra en la solicitud.")
        return render(request, 'productos/error.html', {
            'message': 'El token de Transbank no fue proporcionado en la respuesta.'
        })

    # Configura las opciones para Transbank
    tx = Transaction(WebpayOptions(
        commerce_code=settings.TRANSBANK_COMMERCE_CODE,
        api_key=settings.TRANSBANK_API_KEY,
        integration_type=settings.TRANSBANK_ENVIRONMENT
    ))

    try:
        # Confirmar la transacción con el token proporcionado
        response = tx.commit(token_ws)

        # Log para depuración
        logging.info("Response from Transbank commit transaction: %s", response)

        # Verificar si la transacción fue exitosa
        if response.get('response_code', None) == 0:
            # Aquí es donde podemos realizar el pedido
            pedido_id = realizar_pedido(request)
            if pedido_id:
                # Redirigir al usuario a la vista del pedido realizado
                return redirect('estado_pedido', pedido_id=pedido_id)
            else:
                logging.error("Error al crear el pedido.")
                return render(request, 'productos/error.html', {
                    'message': 'Error al crear el pedido.'
                })

        else:
            # Manejo de errores cuando la transacción no es exitosa
            logging.error("Error en la transacción de Transbank: Código de respuesta %s", response.get('response_code'))
            return render(request, 'productos/error.html', {
                'message': f'Error en la transacción: {response.get("response_code")}',
                'response': response
            })

    except Exception as e:
        # Manejo de errores
        logging.error("Error al confirmar el pago con Transbank: %s", str(e))
        return render(request, 'productos/error.html', {'message': f'Error: {str(e)}'})
    

def realizar_pedido(request):
    carrito_items = Carrito.objects.filter(usuario=request.user)
    
    if carrito_items:
        tipo_envio = request.POST.get('tipo_envio', 'domicilio_registro')
        direccion_envio = request.user.direccion if tipo_envio == 'domicilio_registro' else ''
        
        pedido = Pedido.objects.create(
            usuario=request.user,
            estado='preparacion',
            tipo_envio=tipo_envio,
            direccion_envio=direccion_envio
        )

        total_compras = 0
        descuento_aplicado = 0
        for item in carrito_items:
            precio_con_descuento = item.producto.precio_con_descuento()
            subtotal_item = precio_con_descuento * item.cantidad
            total_compras += subtotal_item

            # Calcular descuento aplicado
            if item.producto.descuento:
                descuento_item = item.producto.precio * (item.producto.descuento / 100) * item.cantidad
                descuento_aplicado += descuento_item

            PedidoProducto.objects.create(pedido=pedido, producto=item.producto, cantidad=item.cantidad)
            item.producto.stock -= item.cantidad
            item.producto.save()

            # Crear entradas en HistorialVentas
            Venta.objects.create(
                usuario=request.user,
                producto=item.producto,
                cantidad=item.cantidad
            )
            
            # Actualizar estadísticas de ventas
            estadisticas, created = EstadisticasVentas.objects.get_or_create(producto=item.producto)
            estadisticas.cantidad_vendida += item.cantidad
            estadisticas.total_ventas_diarias += subtotal_item
            estadisticas.total_ventas_semanales += subtotal_item
            estadisticas.total_ventas_mensuales += subtotal_item
            estadisticas.save()
        
        # Aplicar el descuento total al total del pedido
        total_con_descuento = total_compras - descuento_aplicado

        pedido.total_compras = total_con_descuento
        pedido.descuento_aplicado = descuento_aplicado
        pedido.save()
        
        carrito_items.delete()

        return pedido.id  # Retorna el ID del pedido para redirección

    return None  # Si no hay productos en el carrito, retorna None

def carrito(request):
    if not request.user.is_authenticated:
        return render(request, 'productos/aviso_no_logueado.html')
    # Código para usuarios logueados
    return render(request, 'productos/carrito.html')
from .forms import ConfiguracionDisenoForm
from .models import ConfiguracionDiseno

@user_passes_test(lambda u: u.is_superuser)
def editar_configuracion_diseno(request):
    configuracion, created = ConfiguracionDiseno.objects.get_or_create(nombre='default')

    if request.method == 'POST':
        form = ConfiguracionDisenoForm(request.POST, request.FILES, instance=configuracion)
        if form.is_valid():
            form.save()
            return redirect('previsualizar_configuracion_diseno')  # Cambia esto al nombre correcto de tu vista de previsualización
    else:
        form = ConfiguracionDisenoForm(instance=configuracion)

    return render(request, 'productos/editar_configuracion_diseno.html', {'form': form})



def escanear_codigo_qr(request):
    """
    Vista para escanear un código QR y validar el estado del pedido asociado.
    """
    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        if codigo:
            # Buscar el pedido utilizando el código escaneado
            pedido = get_object_or_404(Pedido, codigo=codigo)
            return render(request, 'verificar_pedido.html', {'pedido': pedido})
        else:
            # Si no se proporciona un código, mostrar un mensaje de error
            return render(request, 'error.html', {'message': 'No se ha proporcionado un código válido.'})
    
    # Renderiza la página de escaneo de código QR
    return render(request, 'productos/escanear_codigo_qr.html')


def verificar_pedido(request):
    pedido = None
    error = None
    
    # Obtener el ID del pedido o el código de la URL
    pedido_id = request.GET.get('pedido_id')
    codigo = request.GET.get('codigo')
    
    if pedido_id:
        try:
            pedido = Pedido.objects.get(id=pedido_id)
        except Pedido.DoesNotExist:
            error = f"No se encontró un pedido con el ID {pedido_id}"
    elif codigo:
        try:
            pedido = Pedido.objects.get(codigo=codigo)
        except Pedido.DoesNotExist:
            error = f"No se encontró un pedido con el código {codigo}"
    
    if pedido:
        return render(request, 'productos/verificar_pedido.html', {'pedido': pedido})
    else:
        return render(request, 'productos/buscar_pedido.html', {'error': error})
    

from .forms import ActualizarUsuarioForm

@login_required
def actualizar_perfil(request):
    if request.method == 'POST':
        form = ActualizarUsuarioForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil ha sido actualizado con éxito.')
            return redirect('actualizar_perfil')  # Cambia 'perfil' por el nombre de tu vista del perfil del usuario
    else:
        form = ActualizarUsuarioForm(instance=request.user)
    
    return render(request, 'productos/actualizar_perfil.html', {'form': form})

def vista_previa_carrito(request):
    # Obtener todos los elementos del carrito para el usuario
    carrito_items = Carrito.objects.filter(usuario=request.user)
    
    # Calcular el total del carrito usando el precio con descuento si aplica
    total_carrito = sum(item.producto.precio_con_descuento() * item.cantidad for item in carrito_items)

    # Crear una lista de artículos del carrito con detalles necesarios
    carrito_items_data = [
        {
            'producto': {
                'nombre': item.producto.nombre,
                'imagen': item.producto.imagen.url,
                'precio_con_descuento': item.producto.precio_con_descuento(),
            },
            'cantidad': item.cantidad
        } for item in carrito_items
    ]

    # Contar el número total de artículos en el carrito
    cart_item_count = carrito_items.count()

    return JsonResponse({
        'carrito_items': carrito_items_data,
        'total_carrito': total_carrito,
        'cart_item_count': cart_item_count
    })

@require_POST
def update_cart_item(request, item_id):
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 0))
        if quantity < 0:
            raise ValueError("La cantidad no puede ser negativa.")
        
        carrito_item = Carrito.objects.get(id=item_id, usuario=request.user)
        if quantity == 0:
            carrito_item.delete()
        else:
            carrito_item.cantidad = quantity
            carrito_item.save()
        
        return JsonResponse({'success': True})
    except (Carrito.DoesNotExist, ValueError) as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def remove_cart_item(request, item_id):
    if request.method == 'POST':
        try:
            item = Carrito.objects.get(id=item_id)
            item.delete()
            return JsonResponse({'success': True})
        except Carrito.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Artículo no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def fetch_comunas(request):
    response = requests.get('https://apis.digital.gob.cl/dpa/comunas/')
    return JsonResponse(response.json())




def comprar_como_invitado(request):
    if request.method == 'POST':
        form = CompraInvitadoForm(request.POST)
        if form.is_valid():
            # Crear un nuevo pedido como invitado
            pedido = Pedido.objects.create(
                nombre=form.cleaned_data['nombre'],
                apellido=form.cleaned_data['apellido'],
                rut=form.cleaned_data['rut'],
                telefono=form.cleaned_data['telefono'],
                region=form.cleaned_data['region'],
                comuna=form.cleaned_data['comuna'],
                direccion=form.cleaned_data['direccion'],
                email=form.cleaned_data['email'],
                tipo_envio=form.cleaned_data['tipo_envio'],
                metodo_pago=form.cleaned_data['metodo_pago'],
                estado='pendiente',
            )

            # Verificar si existe una sesión para el carrito
            if not request.session.session_key:
                request.session.create()

            # Asignar productos al pedido
            carrito_items = Carrito.objects.filter(sesion_id=request.session.session_key, usuario=None)
            for item in carrito_items:
                pedido.productos.add(item.producto, through_defaults={'cantidad': item.cantidad})
                item.delete()  # Eliminar los elementos del carrito después de añadirlos al pedido

            pedido.save()

            # Redirigir a la página de confirmación o pago según el método de pago seleccionado
            if form.cleaned_data['metodo_pago'] == 'transbank':
                return redirect('procesar_pago_transbank', pedido_id=pedido.id)
            elif form.cleaned_data['metodo_pago'] == 'transferencia':
                return redirect('instrucciones_transferencia', pedido_id=pedido.id)

            messages.success(request, 'Pedido realizado con éxito.')
            return redirect('estado_pedido', pedido_id=pedido.id)
    else:
        form = CompraInvitadoForm()

    return render(request, 'productos/compra_invitado.html', {'form': form})


def instrucciones_transferencia(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    if request.method == 'POST':
        comprobante = request.FILES.get('comprobante')
        if comprobante:
            pedido.comprobante_transferencia = comprobante
            pedido.save()
            messages.success(request, 'Comprobante de transferencia subido con éxito.')
            return redirect('estado_pedido', pedido_id=pedido.id)
        else:
            messages.error(request, 'Debe subir un comprobante.')

    return render(request, 'productos/instrucciones_transferencia.html', {'pedido': pedido})


def seleccionar_opcion(request):
    producto_id = request.session.get('producto_id')
    return render(request, 'productos/seleccionar_opcion.html', {'producto_id': producto_id})


@require_POST
def compra_invitado(request):
    form = CompraInvitadoForm(request.POST)
    if form.is_valid():
        # Procesar la compra como invitado
        # Crear un nuevo pedido y guardar la información del invitado
        data = form.cleaned_data
        pedido = Pedido.objects.create(
            nombre=data['nombre'],
            apellido=data['apellido'],
            rut=data['rut'],
            telefono=data['telefono'],
            region=data['region'],
            comuna=data['comuna'],
            direccion=data['direccion'],
            email=data['email'],
            tipo_envio=data['tipo_envio'],
            metodo_pago=data['metodo_pago'],
            # otros campos del pedido
        )
        # Redirigir al usuario a una página de confirmación o al carrito
        return redirect('confirmacion_compra')  # Reemplaza con tu URL de confirmación
    else:
        # Manejar errores de validación
        return render(request, 'productos/carrito.html', {'compra_invitado_form': form})