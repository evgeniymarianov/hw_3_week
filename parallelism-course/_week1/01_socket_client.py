import socket


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as producer_socket:
    producer_socket.connect(("127.0.0.1", 9271))
    producer_socket.send(b"user_id:2")
    response = producer_socket.recv(2)
    print(f"{response=}")
