import socket

class Socket:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def sendto(self, DATA, HOST = '127.0.0.1', PORT = 50007):
        result = str(DATA)
        self.client.sendto(result.encode('utf-8'),(HOST,PORT))