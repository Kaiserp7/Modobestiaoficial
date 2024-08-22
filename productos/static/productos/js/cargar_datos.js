$(document).ready(function() {
    // Verifica que jQuery está disponible
    if (typeof $ === 'undefined') {
        console.error('jQuery no está definido');
        return;
    }

    // Cargar las regiones desde la API de Ubigeo
    $.ajax({
        url: 'https://www.ajgallego.com/ubigeo/api/regiones/',
        method: 'GET',
        dataType: 'json',
        success: function(data) {
            console.log("Regiones cargadas:", data); // Verifica que las regiones se carguen correctamente
            if (data && data.length > 0) {
                data.forEach(function(region) {
                    $('#id_region').append(new Option(region.nombre, region.codigo));
                });
            } else {
                Swal.fire({
                    icon: 'info',
                    title: 'Información',
                    text: 'No se encontraron regiones.'
                });
            }

            // Manejar el cambio de región para cargar las comunas
            $('#id_region').change(function() {
                let regionCodigo = $(this).val();
                $('#id_comuna').empty().append(new Option('Seleccione una comuna', ''));

                if (regionCodigo) {
                    $.ajax({
                        url: 'https://www.ajgallego.com/ubigeo/api/regiones/' + regionCodigo + '/municipios/',
                        method: 'GET',
                        dataType: 'json',
                        success: function(comunas) {
                            console.log("Comunas cargadas para la región " + regionCodigo + ":", comunas); // Verifica que las comunas se carguen correctamente
                            if (comunas && comunas.length > 0) {
                                comunas.forEach(function(comuna) {
                                    $('#id_comuna').append(new Option(comuna.nombre, comuna.codigo));
                                });
                            } else {
                                Swal.fire({
                                    icon: 'info',
                                    title: 'Información',
                                    text: 'No se encontraron comunas para esta región.'
                                });
                            }
                        },
                        error: function(xhr, status, error) {
                            console.error("Error al cargar las comunas:", status, error);
                            Swal.fire({
                                icon: 'error',
                                title: 'Error',
                                text: 'Error al cargar las comunas. Inténtalo de nuevo más tarde.'
                            });
                        }
                    });
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error al cargar las regiones:", status, error);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'Error al cargar las regiones. Inténtalo de nuevo más tarde.'
            });
        }
    });
});
