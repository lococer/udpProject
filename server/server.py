import socket
import random
from common import common

server_ip = "0.0.0.0"  # 服务器的 IP 地址
server_port = 12345  # 服务器的端口号
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# 绑定服务器地址和端口
server_socket.bind((server_ip, server_port))
print(f"UDP 服务器已启动，监听 {server_ip}:{server_port}")

activateId = set()


def udp_listen():
    try:
        while True:
            # 接收客户端发送的数据
            data, address = server_socket.recvfrom(
                10240)  # 假设接收的数据不超过 10240 字节

            requestCode = common.getRequestCode(data)
            if (requestCode == 1):  #建立连接
                newId = random.randint(0, common.MAXID)
                while newId in activateId:
                    newId = random.randint(0, common.MAXID)
                activateId.add(newId)
                print(f"创建新传输编号{newId}")
                print(address)
                allowedFrame = common.myEncode(newId, common.ALLOW)
                common.sendUdpTo(server_socket, address[0], address[1],
                                 allowedFrame)
            elif requestCode == 4:
                id = common.getId(data)
                # if id not in activateId:
                #     print("not allowed")
                # else:
                #     print("allowed")

                # print(common.getData(data))
                with open("./server/received.txt", "a") as f:
                    f.write(common.getData(data))

                ackFrame = common.myEncode(id, common.ACK)
                common.sendUdpTo(server_socket, address[0], address[1],
                                 ackFrame)

    except KeyboardInterrupt:
        print("服务器已关闭")

    finally:
        server_socket.close()


def udp_server(server_ip, server_port):
    """
    创建一个 UDP 服务器，监听指定的 IP 地址和端口
    :param server_ip: 服务器的 IP 地址
    :param server_port: 服务器的端口号
    """
    # 创建一个 UDP 套接字

    try:

        while True:
            # 接收客户端发送的数据
            data, address = server_socket.recvfrom(1024)  # 假设接收的数据不超过 1024 字节
            # message = data.decode('utf-8')
            message = data
            print(f"从 {address} 收到消息: {message}")

            with open("received.txt", "ab") as f:
                f.write(message)

            print("已写")
            server_socket.sendto((1).to_bytes(4, 'little'), address)
            print("已响应")

    except KeyboardInterrupt:
        print("服务器已关闭")

    finally:
        # 关闭套接字
        server_socket.close()


# 示例使用
if __name__ == "__main__":
    # udp_server(server_ip, server_port)
    udp_listen()
