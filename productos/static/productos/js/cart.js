function updateCartPreview() {
    fetch('/vista-previa-carrito/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        const cartPreviewBody = document.getElementById('cartPreviewBody');
        const cartItemCount = document.getElementById('cartItemCount');
        const cartTotalElement = document.getElementById('cartTotal');

        // Limpia el contenido actual del preview
        cartPreviewBody.innerHTML = '';

        if (data.carrito_items.length > 0) {
            data.carrito_items.forEach(item => {
                const subtotal = item.producto.precio_con_descuento * item.cantidad;
                const itemElement = document.createElement('div');
                itemElement.className = 'cart-item';
                itemElement.innerHTML = `
                    <img src="${item.producto.imagen}" alt="${item.producto.nombre}">
                    <div class="cart-item-details">
                        <h6>${item.producto.nombre}</h6>
                        <p>$${item.producto.precio_con_descuento.toFixed(2)} cantidad: ${item.cantidad}</p>
                        <p>Subtotal: $${subtotal.toFixed(2)}</p>
                    </div>
                `;
                cartPreviewBody.appendChild(itemElement);
            });
            cartTotalElement.textContent = `Total: $${data.total_carrito.toFixed(2)}`;
        } else {
            cartPreviewBody.innerHTML = '<p class="text-center">Tu carrito está vacío.</p>';
            cartTotalElement.textContent = '';
        }

        // Actualiza el contador del carrito
        const totalItems = data.carrito_items.reduce((total, item) => total + item.cantidad, 0);
        cartItemCount.textContent = totalItems;
    })
    .catch(error => console.error('Error al actualizar la vista previa del carrito:', error));
}

document.addEventListener('DOMContentLoaded', function() {
    updateCartPreview();
});
