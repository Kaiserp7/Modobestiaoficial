document.addEventListener('DOMContentLoaded', function() {
    // Función para mostrar alertas
    const showAlerts = (messages) => {
        if (messages && messages.length > 0) {
            messages.forEach(message => {
                if (message.icon === 'warning' && !message.redirect) {
                    Swal.fire({
                        icon: message.icon,
                        title: message.title,
                        text: message.text,
                        confirmButtonText: 'Ahora no',
                        showCancelButton: true,
                        cancelButtonText: 'Registrarse',
                        cancelButtonColor: '#007bff',
                    }).then((result) => {
                        if (result.isDismissed) {
                            // Usuario elige 'Ahora no', no hacer nada
                        } else if (result.isConfirmed) {
                            // Usuario elige 'Registrarse'
                            window.location.href = '/registro/'; // Ajusta la URL según sea necesario
                        }
                    });
                } else {
                    Swal.fire({
                        icon: message.icon,
                        title: message.title,
                        text: message.text,
                        confirmButtonText: 'Aceptar'
                    }).then(result => {
                        if (result.isConfirmed && message.redirect) {
                            window.location.href = message.redirect;
                        }
                    });
                }
            });
        }
    };

    // Obtener mensajes del HTML para carrito y realizar pedido
    const messagesElement = document.getElementById('messages');
    if (messagesElement) {
        const messages = JSON.parse(messagesElement.dataset.messages || '[]');
        showAlerts(messages);
    }

    // Función para obtener el CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Función para agregar un producto al carrito
    function agregarAlCarrito(productId) {
        fetch(`/agregar-al-carrito/${productId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ cantidad: 1 })  // Puedes cambiar la cantidad según lo necesites
        })
        .then(response => response.json())
        .then(data => {
            showAlerts(data.messages);
            if (data.success) {
                updateCartCount();
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }

    // Función para eliminar un producto del carrito
    function eliminarProducto() {
        document.querySelectorAll('.eliminar-producto').forEach(button => {
            button.addEventListener('click', function() {
                const url = this.getAttribute('data-url');
                fetch(url, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                })
                .then(response => response.json())
                .then(data => {
                    Swal.fire({
                        icon: data.success ? 'success' : 'error',
                        title: data.success ? 'Eliminado' : 'Error',
                        text: data.message,
                        confirmButtonText: 'Aceptar'
                    }).then(result => {
                        if (result.isConfirmed && data.success) {
                            window.location.reload();
                        }
                    });
                })
                .catch(error => console.error('Error:', error));
            });
        });
    }

    // Función para modificar la cantidad de un producto en el carrito
    function modificarCantidad() {
        document.querySelectorAll('.modificar-cantidad-form').forEach(form => {
            form.addEventListener('submit', function(event) {
                event.preventDefault();
                const url = this.getAttribute('data-url');
                const formData = new FormData(this);

                fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                    },
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    Swal.fire({
                        icon: data.success ? 'success' : 'error',
                        title: data.success ? 'Actualizado' : 'Error',
                        text: data.message,
                        confirmButtonText: 'Aceptar'
                    }).then(result => {
                        if (result.isConfirmed && data.success) {
                            window.location.reload();
                        }
                    });
                })
                .catch(error => console.error('Error:', error));
            });
        });
    }

    // Actualizar contador del carrito
    const cartCountElement = document.getElementById('cart-count');

    function updateCartCount() {
        fetch('/get-cart-item-count/')
            .then(response => response.json())
            .then(data => {
                cartCountElement.textContent = data.cart_item_count;
            });
    }

    // Llama a la función para actualizar el contador al cargar la página
    updateCartCount();

    // Llamar a las funciones
    eliminarProducto();
    modificarCantidad();


    
});
