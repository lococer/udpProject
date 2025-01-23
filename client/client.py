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


def send_with_timeout(client_socket,
                      server_ip,
                      server_port,
                      encodeData,
                      timeout=5,
                      max_retries=3):
    """
    发送数据并处理超时重传
    :param client_socket: 客户端套接字
    :param server_ip: 服务器 IP 地址
    :param server_port: 服务器端口号
    :param encodeData: 要发送的数据列表
    :param timeout: 超时时间（秒）
    :param max_retries: 最大重试次数
    """
    client_socket.settimeout(timeout)  # 设置套接字超时时间

    for i in range(len(encodeData)):
        retries = 0
        while retries < max_retries:
            print(f"传输 {i}")
            common.sendUdpTo(client_socket, server_ip, server_port,
                             encodeData[i])
            try:
                response, _ = client_socket.recvfrom(10240)  # 尝试接收响应
                print(f"收到响应: {response}")
                break  # 成功接收到响应，跳出重试循环
            except socket.timeout:
                print(f"超时，正在重试 {retries + 1}/{max_retries}")
                retries += 1
        else:
            print(f"传输 {i} 失败，达到最大重试次数")
            # 可以在这里处理失败情况，例如记录日志或抛出异常


# 示例使用
if __name__ == "__main__":

    data = readFile("./client/bible.txt", 800 + 600)
    # print(data)
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
    response = client_socket.recvfrom(10240)
    transmitId = common.getId(response[0])
    print(f"从服务器收到响应: {transmitId}")

    encodeData = common.myEncodeData(transmitId, common.DATA, data)

    print(f"总大小:{len(encodeData)},正在传输...")

    # 调用发送函数
    send_with_timeout(client_socket, server_ip, server_port, encodeData)

    print("传输完成")
