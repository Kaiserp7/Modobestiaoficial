from django.contrib import admin
from .models import Usuario, Categoria, Producto, Venta, HistorialVentas, Oferta
from .models import OfertaCarrusel
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'stock', 'categoria', 'es_oferta', 'descuento', 'fecha_inicio_oferta', 'fecha_fin_oferta')
    list_filter = ('categoria', 'es_oferta')
    search_fields = ('nombre', 'descripcion')
    fieldsets = (
        (None, {
            'fields': ('nombre', 'descripcion', 'sabor', 'sabor_secundario', 'precio', 'stock', 'imagen', 'imagen_secundaria', 'categoria')
        }),
        ('Oferta', {
            'fields': ('es_oferta', 'descuento', 'fecha_inicio_oferta', 'fecha_fin_oferta', 'imagen_oferta'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if not obj or not obj.es_oferta:
            return ('descuento', 'fecha_inicio_oferta', 'fecha_fin_oferta', 'imagen_oferta')
        return super().get_readonly_fields(request, obj)

admin.site.register(Producto, ProductoAdmin)
admin.site.register(Categoria)
admin.site.register(Oferta)
admin.site.register(Usuario)
admin.site.register(Venta)
admin.site.register(HistorialVentas)
admin.site.register(OfertaCarrusel)