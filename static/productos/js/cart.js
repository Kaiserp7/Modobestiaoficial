function updateCartPreview() {
    fetch('/vista-previa-carrito/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        const contentType = response.headers.get('Content-Type');
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        } else {
            return response.text().then(text => {
                throw new Error('Respuesta del servidor no es JSON: ' + text);
            });
        }
    })
    .then(data => {
        console.log('Datos del carrito:', data); // Depuración
        const cartPreviewBody = document.getElementById('cartPreviewBody');
        const cartItemCount = document.getElementById('cartItemCount');
        
        // Actualiza el contador del carrito sumando todas las cantidades de los productos
        const totalItems = data.carrito_items.reduce((total, item) => total + item.cantidad, 0);
        cartItemCount.textContent = totalItems;
        
        // Limpia el contenido actual del preview
        cartPreviewBody.innerHTML = '';

        if (data.carrito_items.length > 0) {
            data.carrito_items.forEach(item => {
                const subtotal = item.producto.precio_con_descuento * item.cantidad;
                const itemElement = document.createElement('div');
                itemElement.className = 'cart-item d-flex align-items-center mb-3 border-bottom pb-3';
                itemElement.innerHTML = `
                    <img src="${item.producto.imagen}" alt="${item.producto.nombre}" class="img-fluid rounded" style="max-width: 80px; height: auto;">
                    <div class="ms-3 w-100">
                        <h6 class="fw-bold text-truncate">${item.producto.nombre}</h6>
                        <p class="mb-1 d-flex justify-content-between align-items-center">
                            <span>$${item.producto.precio_con_descuento} x ${item.cantidad}</span>
                            <span class="text-muted">Subtotal: $${subtotal.toFixed(2)}</span>
                        </p>
                    </div>
                `;
                cartPreviewBody.appendChild(itemElement);
            });
            const totalElement = document.createElement('div');
            totalElement.className = 'fw-bold mt-3 text-end';
            totalElement.innerHTML = `<strong>Total del Carrito: $${data.total_carrito.toFixed(2)}</strong>`;
            cartPreviewBody.appendChild(totalElement);
        } else {
            cartPreviewBody.innerHTML = '<p class="text-center">Tu carrito está vacío.</p>';
        }
    })
    .catch(error => console.error('Error al actualizar la vista previa del carrito:', error));
}

document.addEventListener('DOMContentLoaded', function() {
    updateCartPreview();
});
