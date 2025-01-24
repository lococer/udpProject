import socket
from common import common
import random
from typing import List
import threading, time, hashlib

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


class Client(common.FrameHandler):

    def __init__(self, server_ip, server_port, timeout=2, max_retries=3):
        super().__init__()
        self.__server_ip = server_ip
        self.__server_port = server_port
        self.timeout = timeout
        self.mySocket.settimeout(self.timeout)
        self.max_retries = max_retries
        self.file = None
        self.windowStart = 0  # 滑动窗口的起点
        self.windowSize = 1  # 滑动窗口的大小

    def readFile(self, path, size) -> List[bytes]:
        reslut = []
        try:
            with open(path, "rb") as f:
                while True:
                    content = f.read(size)
                    if not content:
                        break
                    reslut.append(content)
        except:
            print("No such file!")

        self.fileMd5 = self.get_file_md5(path)
        self.file = reslut

    def get_file_md5(self, file_path):
        """计算文件的 MD5 哈希值"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.digest()
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def requestSend(self):
        '''
        请求发送文件,确保已经读过文件
        '''
        assert self.file is not None
        tries = 0
        while tries < self.max_retries:
            request = self.myEncode(0, common.REQUEST, len(self.file),
                                    self.fileMd5)
            self.sendUdp(self.__server_ip, self.__server_port, request)
            try:
                response, address = self.receiveUdp()
                if response.getRequestCode is common.ALLOW:
                    try:
                        self.Id = response.getId()
                        self.fileSend()
                    except Exception as e:
                        print(e)
                elif response.getRequestCode is common.DENY:
                    print(f"Server denied")
                    return
                else:
                    raise Exception(
                        f"Except an ALLOW or DENY, but a {response.getRequestCode}"
                    )

            except socket.timeout as e:
                tries += 1
                continue
            except socket.error as e:
                socket.error(f"socket error: {e}")
        else:
            print(f"Can't connect to server")
            return

    def listenACK(self):
        '''
        监听ACK,更新滑动窗口
        '''
        tries = 0
        while self.windowStart < len(self.fileBytes):
            tries += 1
            if tries >= self.max_retries * 10:  # 发文件宽松点
                raise Exception("long time don't receive response from server")

            try:
                response, address = self.receiveUdp()
            except socket.timeout as e:
                continue

            if response.getRequestCode is not common.ACK:  # 忽略非ACK
                continue

            currentACK = response.getData

            if (currentACK < self.windowStart
                    or currentACK >= self.windowStart + self.windowSize):
                continue

            tries = 0  # 接收到有效ACK
            self.receivedACK.add(currentACK)
            while (self.windowStart in self.receivedACK):  # 更新窗口位置
                self.windowStart += 1
                if self.windowStart >= len(self.fileBytes): break  # 中止条件

    def sendWindow(self):
        '''
        定时发送window里的所有数据
        '''
        while True:
            with self.lock:  # 锁发送区间
                l = self.windowStart
                r = min(l + self.windowSize, len(self.fileBytes))

            if l >= len(self.fileBytes): return  # 中止条件

            for i in range(l, r):
                self.sendUdp(self.__server_ip, self.__server_port,
                             self.fileBytes[i])
                time.sleep(0.001)  # 两个间隔1ms

            time.sleep(0.01)  # 两次发送间隔10ms

    def fileSend(self):
        self.receivedACK = set()
        self.fileBytes = self.myEncodeData(self.Id, common.DATA, self.file)
        self.lock = threading.Lock()
        thread1 = threading.Thread(self.listenACK)
        thread2 = threading.Thread(self.sendWindow)

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # 清理工作
        self.file = None
        del self.receivedACK
        del self.fileBytes
        del self.lock


# 示例使用
if __name__ == "__main__":

    client = Client(server_ip, server_port)

    client.readFile("./client/bible.txt", 1200)

    client.requestSend()

    print("程序结束")
