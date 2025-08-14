import pika
import ssl
import json

def monitor_rabbitmq_queue(queue_name, host='localhost', port=5672, username='guest', password='guest', use_ssl=False):
    received_data = None  # Variável para guardar o webhook
    
    def callback(ch, method, properties, body):
        nonlocal received_data  # Acessa a variável de fora
        received_data = body.decode('utf-8')
        print(f"Mensagem recebida: {received_data}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        ch.stop_consuming()  # Para após receber a primeira mensagem
    
    try:
        credentials = pika.PlainCredentials(username, password)
        
        if use_ssl:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connection_params = pika.ConnectionParameters(
                host=host, port=port, credentials=credentials,
                ssl_options=pika.SSLOptions(ssl_context),
                heartbeat=600, blocked_connection_timeout=300
            )
        else:
            connection_params = pika.ConnectionParameters(
                host=host, port=port, credentials=credentials,
                heartbeat=600, blocked_connection_timeout=300
            )
        
        print(f"Conectando ao RabbitMQ em {host}:{port}")
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        
        # Declarar a fila
        channel.queue_declare(queue=queue_name, durable=True)
        channel.basic_consume(queue=queue_name, on_message_callback=callback)
        
        print(f"Aguardando mensagem da fila '{queue_name}'...")
        channel.start_consuming()  # Fica esperando até receber uma mensagem
        
        connection.close()
        return received_data  # Retorna o que foi recebido
        
    except KeyboardInterrupt:
        print("Parando...")
        if 'channel' in locals():
            channel.stop_consuming()
        if 'connection' in locals():
            connection.close()
        return None
    except Exception as e:
        print(f"Erro de conexão: {e}")
        return None


if __name__ == '__main__':
    # Uso:
    monitor_rabbitmq_queue('santa-casa', host='rabbitmq.itech360.com.br', port=5672, username='admin', password='admin')
