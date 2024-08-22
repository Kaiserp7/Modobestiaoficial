from productos.models import Comuna


def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    if 'region' in self.data:
        try:
            region_id = int(self.data.get('region'))
            self.fields['comuna'].queryset = Comuna.objects.filter(region_id=region_id).order_by('nombre')
        except (ValueError, TypeError):
            self.fields['comuna'].queryset = Comuna.objects.none()
    elif self.instance.pk:
        self.fields['comuna'].queryset = self.instance.region.comuna_set.order_by('nombre')
