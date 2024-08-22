$(document).ready(function() {
    // Cargar el archivo JSON con regiones y comunas
    $.getJSON("{% static 'productos/js/comunas-regiones.json' %}", function(data) {
        const regiones = data.regiones;

        // Poblar el selector de regiones
        $('#id_region').empty().append(new Option('Seleccione una región', ''));
        regiones.forEach(function(region) {
            $('#id_region').append(new Option(region.region, region.region));
        });

        // Manejar el cambio de región para cargar las comunas
        $('#id_region').change(function() {
            const regionNombre = $(this).val();
            $('#id_comuna').empty().append(new Option('Seleccione una comuna', ''));

            if (regionNombre) {
                const regionSeleccionada = regiones.find(region => region.region === regionNombre);
                if (regionSeleccionada) {
                    regionSeleccionada.comunas.forEach(function(comuna) {
                        $('#id_comuna').append(new Option(comuna, comuna));
                    });
                }
            }
        });
    }).fail(function() {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se pudo cargar la información de regiones y comunas.'
        });
    });
});
