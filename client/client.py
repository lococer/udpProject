import socket
from common import common
import random
from typing import List

server_ip = "47.98.224.148"  # 服务器的 IP 地址
server_port = 12345  # 服务器的端口号


def send_udp_message(server_ip, server_port, message):
    """
    向指定的服务器发送 UDP 消息
    :param server_ip: 服务器的 IP 地址
    :param server_port: 服务器的端口号
    :param message: 要发送的字符串消息
    """
    # 创建一个 UDP 套接字
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        # message_bytes = order.to_bytes(4, 'little') + message
        message_bytes = message

        # 发送消息到服务器
        client_socket.sendto(message_bytes, (server_ip, server_port))
        print(f"消息已发送到 {server_ip}:{server_port} - 内容: {message}")

        # 接收服务器的响应
        response, _ = client_socket.recvfrom(1024)  # 假设响应不超过 1024 字节
        print(f"从服务器收到响应: {response}")

    finally:
        # 关闭套接字
        client_socket.close()


def readFile(path, size):
    result = []
    with open(path, "rb") as f:
        while True:
            content = f.read(size)

            if not content:
                break

            result.append(content)

            # print(f"read: {content}")
    return result


# 示例使用
if __name__ == "__main__":

    data = readFile("./client/example.txt", 2)
    print(data)
    encodeData = common.myEncodeData(random.randint(0, 1000), common.DATA,
                                     data)
    # print(encodeData, hex)
    # for i in encodeData:
    #     for byte in i:
    #         print(f"{byte:02x}", end=" ")
    #     print()

    encodeRequest = common.myEncode(random.randint(0, 1000), common.REQUEST,
                                    10)
    # for byte in encodeRequest:
    #     print(f"{byte:02x}", end=' ')
    # print()

    # 创建一个 UDP 套接字
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    common.sendUdpTo(client_socket, server_ip, server_port, encodeRequest)
    print(f"已发送: {encodeRequest}")
