from transbank.webpay.webpay_plus.transaction import Transaction

# Configuración en modo de prueba
Transaction.commerce_code = '597055555532'
Transaction.api_key = '597055555532'
Transaction.environment = 'INTEGRACION'  # Modo de integración para pruebas
