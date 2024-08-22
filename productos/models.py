from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from decimal import Decimal
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum, F
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
# Modelo extendido de Usuario
class Region(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Comuna(models.Model):
    nombre = models.CharField(max_length=100)
    region = models.ForeignKey(Region, related_name='comunas', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombre} ({self.region.nombre})"

class Usuario(AbstractUser):
    es_administrador = models.BooleanField(default=False)
    nombre = models.CharField(max_length=50, default='Nombre')
    apellido = models.CharField(max_length=50, default='Apellido')
    rut = models.CharField(max_length=12, default='12345678-9')
    telefono = models.CharField(max_length=15, default='123456789')
    direccion = models.CharField(max_length=100, default='Dirección')
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    comuna = models.ForeignKey(Comuna, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.username

# Modelo de Categoría
class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='categorias/')

    def __str__(self):
        return self.nombre

class OfertaCarrusel(models.Model):
    nombre_oferta = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    imagen_promocional = models.ImageField(upload_to='ofertas_carrusel/')

    def __str__(self):
        return self.nombre_oferta

    def esta_activa(self):
        ahora = timezone.now()
        return self.fecha_inicio <= ahora <= self.fecha_fin

# Modelo de Producto
class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    sabor = models.CharField(max_length=100)
    sabor_secundario = models.CharField(max_length=100, blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.ImageField(upload_to='productos/')
    imagen_secundaria = models.ImageField(upload_to='productos/', blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField()
    es_oferta = models.BooleanField(default=False)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fecha_inicio_oferta = models.DateTimeField(null=True, blank=True)
    fecha_fin_oferta = models.DateTimeField(null=True, blank=True)
    imagen_oferta = models.ImageField(upload_to='ofertas/', null=True, blank=True)

    def __str__(self):
        return self.nombre

    def precio_con_descuento(self):
        now = timezone.now()
        if self.es_oferta and self.descuento and self.fecha_inicio_oferta and self.fecha_fin_oferta:
            if self.fecha_inicio_oferta <= now <= self.fecha_fin_oferta:
                return self.precio * (1 - self.descuento / 100)
        return self.precio

# Modelo de Venta
class Venta(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Venta de {self.cantidad} x {self.producto.nombre} a {self.usuario.username}'

# Modelo de Carrito de Compras

# Modelo de Pedido
class Pedido(models.Model):
    ESTADOS = [
        ('aceptado', 'Compra Aceptada'),
        ('rechazado', 'Compra Rechazada'),
        ('preparacion', 'Pedido en Preparación'),
        ('enviado', 'Pedido Enviado'),
        ('recibido', 'Compra Recibida por el Cliente'),
        ('local', 'Pedido Tomado para Retiro Local'),
    ]

    TIPO_ENVIO_CHOICES = [
        ('domicilio_registro', 'A domicilio (Usar dirección de registro)'),
        ('retiro_sucursal', 'Retiro en sucursal (Modo bestia Los Ángeles CHILE Galeria Colon Calle Valdivia Frente al Mall)'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADOS)
    fecha = models.DateTimeField(auto_now_add=True)
    total_compras = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tipo_envio = models.CharField(max_length=50, choices=TIPO_ENVIO_CHOICES, default='domicilio_registro')
    direccion_envio = models.CharField(max_length=255, blank=True, null=True)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    descuento_aplicado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    aprobado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="pedidos_aprobados") # Añadido

    def save(self, *args, **kwargs):
        if self.tipo_envio == 'domicilio_registro':
            self.direccion_envio = self.usuario.direccion
        else:
            self.direccion_envio = None
        super().save(*args, **kwargs)

    def valor_total(self):
        return Decimal(sum(item.producto.precio_con_descuento() * item.cantidad for item in self.productos.all())).quantize(Decimal('0.01'))

    def total_con_descuento(self):
        total = self.valor_total()
        return total - (total * (self.descuento / 100))

    def __str__(self):
        return f'Pedido {self.id} - {self.usuario.username}'
    
    def get_absolute_url(self):
        return reverse('detalle_pedido', args=[str(self.id)])

# Signal para revertir stock cuando se elimina un pedido
@receiver(post_delete, sender=Pedido)
def revert_stock_on_order_delete(sender, instance, **kwargs):
    """Revertir el stock de los productos cuando se elimina un pedido."""
    for item in instance.productos.all():
        item.producto.stock += item.cantidad
        item.producto.save()
    

# Modelo de Historial de Ventas
class HistorialVentas(models.Model):
    fecha = models.DateField()
    total_ventas = models.DecimalField(max_digits=10, decimal_places=2)
    ganancia_total = models.DecimalField(max_digits=10, decimal_places=2)
    perdida_total = models.DecimalField(max_digits=10, decimal_places=2)
    detalle_ventas = models.TextField(default='Detalles de la venta')

    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)

    def __str__(self):
        return f"Registro de Ventas del {self.fecha}"

    def save(self, *args, **kwargs):
        if not self.pk:
            try:
                self.pedido = Pedido.objects.latest('id')
            except Pedido.DoesNotExist:
                pass
        super().save(*args, **kwargs)

# Modelo de Estadísticas de Ventas
class EstadisticasVentas(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad_vendida = models.PositiveIntegerField(default=0)
    total_ventas_diarias = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_ventas_semanales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_ventas_mensuales = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def actualizar_estadisticas(self):
        ahora = timezone.now()
        inicio_dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
        inicio_semana = ahora - timezone.timedelta(days=ahora.weekday())
        inicio_mes = ahora.replace(day=1)

        # Ventas diarias
        ventas_diarias = Venta.objects.filter(
            fecha__gte=inicio_dia,
            producto=self.producto
        ).aggregate(total=Sum('cantidad') * F('producto__precio_con_descuento'))['total'] or 0

        # Ventas semanales
        ventas_semanales = Venta.objects.filter(
            fecha__gte=inicio_semana,
            producto=self.producto
        ).aggregate(total=Sum('cantidad') * F('producto__precio_con_descuento'))['total'] or 0

        # Ventas mensuales
        ventas_mensuales = Venta.objects.filter(
            fecha__gte=inicio_mes,
            producto=self.producto
        ).aggregate(total=Sum('cantidad') * F('producto__precio_con_descuento'))['total'] or 0

        self.total_ventas_diarias = ventas_diarias
        self.total_ventas_semanales = ventas_semanales
        self.total_ventas_mensuales = ventas_mensuales
        self.save()

# Modelo de Relación entre Pedido y Producto
class PedidoProducto(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='productos', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def save(self, *args, **kwargs):
        if not self.pk:  # Solo asignar precio_unitario cuando se crea el objeto
            self.precio_unitario = self.producto.precio_con_descuento()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Producto {self.producto.nombre} en Pedido {self.pedido.id}'
    
    

# Modelo de Oferta
class Oferta(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    descuento = models.DecimalField(max_digits=5, decimal_places=2)  # % de descuento
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()

    def __str__(self):
        return f'Oferta para {self.producto.nombre}'

    def esta_activa(self):
        ahora = timezone.now()
        return self.fecha_inicio <= ahora <= self.fecha_fin


# Modelo de Slider
class Slider(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='sliders')
    productos = models.ManyToManyField(Producto)
    imagen_slider = models.ImageField(upload_to='sliders/')
    imagen_decorativa = models.ImageField(upload_to='decorativas/', blank=True, null=True)
    url_imagen_decorativa = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Slider para {self.categoria.nombre}"    
class Cupon(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    cantidad_usuarios = models.PositiveIntegerField()
    tipo = models.CharField(max_length=50, choices=[('permanente', 'Permanente'), ('unico', 'Único')])
    descuento = models.DecimalField(max_digits=5, decimal_places=2)  # Hasta 999.99 de descuento
    fecha_creacion = models.DateTimeField(auto_now_add=True)  # Solo auto_now_add
    fecha_expiracion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.nombre

    def es_valido(self):
        """Verifica si el cupón es válido (no ha expirado)"""
        ahora = timezone.now()
        return self.fecha_expiracion is None or self.fecha_expiracion > ahora

    def aplicar_descuento(self, monto):
        """Aplica el descuento al monto dado"""
        if self.tipo == 'unico' and self.cantidad_usuarios <= 0:
            return monto
        if not self.es_valido():
            return monto
        return monto * (1 - self.descuento / 100)

class Carrito(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    sabor = models.CharField(max_length=50, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)   # Asegúrate de que este campo está definido
    
    def __str__(self):
        return f"{self.usuario.username if self.usuario else 'Invitado'} - {self.producto.nombre} ({self.cantidad})"
    

class HistorialPago(models.Model):
    pedido = models.ForeignKey('Pedido', on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20)
    fecha_transaccion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago {self.id} - Estado: {self.estado}"
    
class ConfiguracionDiseno(models.Model):
    nombre = models.CharField(max_length=255, default='default')
    color_principal = models.CharField(max_length=7, default='#000000')  # Usaremos valores HEX para los colores
    color_secundario = models.CharField(max_length=7, default='#FFFFFF')
    fuente = models.CharField(max_length=255, default='Arial')
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    imagen_fondo = models.ImageField(upload_to='fondos/', blank=True, null=True)
    # Puedes añadir más campos si lo necesitas

    def __str__(self):
        return self.nombre