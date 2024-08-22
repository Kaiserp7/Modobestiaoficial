document.addEventListener('DOMContentLoaded', function() {
    // Función para mostrar alertas de stock
    const showStockAlert = (message) => {
        const alertElement = document.createElement('div');
        alertElement.className = 'alert alert-danger';
        alertElement.textContent = message;
        document.body.prepend(alertElement);

        setTimeout(() => {
            alertElement.remove();
        }, 3000); // La alerta se eliminará después de 3 segundos
    };

    // Manejo del evento de agregar al carrito
    document.querySelectorAll('.add-to-cart-form').forEach(form => {
        form.addEventListener('submit', function(event) {
            const cantidadInput = this.querySelector('input[name="cantidad"]');
            const stock = parseInt(cantidadInput.getAttribute('max'), 10);
            const cantidad = parseInt(cantidadInput.value, 10);

            if (cantidad > stock) {
                event.preventDefault();
                showStockAlert('No hay suficiente stock disponible.');
            }
        });
    });

    // Manejo del evento de actualización del carrito
    document.querySelectorAll('.update-cart-form').forEach(form => {
        form.addEventListener('submit', function(event) {
            const cantidadInput = this.querySelector('input[name="cantidad"]');
            const stock = parseInt(cantidadInput.getAttribute('max'), 10);
            const cantidad = parseInt(cantidadInput.value, 10);

            if (cantidad > stock) {
                event.preventDefault();
                showStockAlert('No hay suficiente stock disponible.');
            }
        });
    });

    // Manejo del evento de eliminación de un producto del carrito
    document.querySelectorAll('.delete-from-cart-form').forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!confirm('¿Estás seguro de que deseas eliminar este producto del carrito?')) {
                event.preventDefault();
            }
        });
    });

    // Manejo del evento de modificación de la cantidad
    document.querySelectorAll('.modify-quantity-form').forEach(form => {
        form.addEventListener('submit', function(event) {
            const cantidadInput = this.querySelector('input[name="cantidad"]');
            const stock = parseInt(cantidadInput.getAttribute('max'), 10);
            const cantidad = parseInt(cantidadInput.value, 10);

            if (cantidad > stock) {
                event.preventDefault();
                showStockAlert('No hay suficiente stock disponible.');
            }
        });
    });

    // Mostrar alertas si hay mensajes en el template
    const alertMessages = document.querySelectorAll('.alert');
    alertMessages.forEach(alert => {
        const message = alert.textContent;
        showStockAlert(message);
    });
});
