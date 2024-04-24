# #!/usr/bin/env python
# import pika

# connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
# channel = connection.channel()

# channel.queue_declare(queue='hello')

# def callback(ch, method, properties, body):
#     print(" [x] Received %r" % body)

# channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)

# print(' [*] Waiting for messages. To exit press CTRL+C')
# channel.start_consuming()









# import pika
# import mysql.connector
# config = {
#  'user': 'root',
#  'password': 'password',
#  'host': '127.0.0.1',
#  'database': 'store',
#  'port': 3006
# }
# # Connect to the MySQL database
# cnx = mysql.connector.connect(**config)
# cursor = cnx.cursor()
# cursor.close()
# # # Re-open the cursor for subsequent queries
# # cursor = cnx.cursor()

# def callback(ch, method, properties, body):
#     print(f" [x] Received '{body.decode()}'")
#     body=body.decode()
#     values_list = body.split(',')
#     item, total  = values_list
#     total=int(total)
#     cursor = cnx.cursor()
#     cursor.execute(f"UPDATE mystore SET total_available = {total} WHERE item_name = '{item}';")
#     cnx.commit()
#     cursor.close()
#     #channel2.basic_publish(exchange='topic_logs', routing_key='topic5', body=message)
#     print(f"workdone")

# connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
# channel = connection.channel()
# # channel2 = connection.channel()

# channel.exchange_declare(exchange='topic_logs', exchange_type='topic')
# # channel2.exchange_declare(exchange='topic_logs', exchange_type='topic')

# # Declare a queue with a random name
# result = channel.queue_declare('', exclusive=True)
# queue_name = result.method.queue

# # Bind the queue to the exchange with routing keys
# channel.queue_bind(exchange='topic_logs', queue=queue_name, routing_key='topic1')
# # channel2.queue_declare(queue='topic5')

# print(' [*] Waiting for messages. To exit press CTRL+C')

# channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

# channel.start_consuming()



import pika
import mysql.connector
import threading
import time
print("11111111111111111111111111111111")
config = {
    'user': 'root',
    'password': 'password',
    'host': 'mysql',
    'database': 'store',
    'port': 3306
}
# Connect to the MySQL database
cnx = mysql.connector.connect(**config)
cursor = cnx.cursor()
cursor.close()

def callback(ch, method, properties, body):
    print(f" [x] Received '{body.decode()}'")
    body = body.decode()
    values_list = body.split(',')
    item, total = values_list
    total = int(total)
    try:
        cursor = cnx.cursor()
        cursor.execute(f"UPDATE mystore SET total_available = {total} WHERE item_name = '{item}';")
        cnx.commit()
        cursor.close()
    except:
        print("cannot set total improper entries")
    print(f"workdone")

def send_heartbeat():
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    channel.exchange_declare(exchange='topic_logs', exchange_type='topic')
    while True:
        # Send heartbeat message
        channel.basic_publish(exchange='topic_logs', routing_key='topic5', body='Heartbeat_1')
        print("Heartbeat sent")
        # Sleep for 5 seconds before sending the next heartbeat
        time.sleep(5)

# Start the heartbeat thread
heartbeat_thread = threading.Thread(target=send_heartbeat)
heartbeat_thread.start()

# Setup RabbitMQ consumer
print("11111111111111111111111111111111")
connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
channel = connection.channel()
channel.exchange_declare(exchange='topic_logs', exchange_type='topic')
result = channel.queue_declare('', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange='topic_logs', queue=queue_name, routing_key='topic1')
print(' [*] Waiting for messages. To exit press CTRL+C')
channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
channel.start_consuming()
