import socket


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener_socket:
    listener_socket.bind(("127.0.0.1", 9271))
    listener_socket.listen()
    connection, client_address = listener_socket.accept()
    print(f"{client_address=}")
    with connection:
        incoming_data = connection.recv(10)
        print(f"{incoming_data=}")
        connection.send(b"OK")
