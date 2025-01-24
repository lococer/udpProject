from typing import List
import socket
import ipaddress
import threading

REQUEST = 1
ALLOW = 2
DENY = 3
DATA = 4
ACK = 5
RETS = 6

# 最大传输编号
MAXID = 1000


class Frame:

    def __init__(self):
        self.frame = None

    def setFrame(self, bytes: bytes):
        assert (len(bytes) >= 20)
        self.frame = bytes

    def getFrame(self) -> bytes:
        assert (self.frame is not None)
        return self.frame

    def calculateCheckCode(self) -> bytes:
        '''
        忽略校验位计算校验码
        输入为bytes
        使用奇偶校验
        TODO 换成哈希
        '''
        assert (self.frame is not None)
        result = 0
        for i in self.data:
            result ^= i
        for i in self.data[12:16]:
            result ^= i
        return result.to_bytes(4, 'little')

    def verifyCheckCode(self, data):
        '''
        验算校验码是否正确
        '''
        assert (self.frame is not None)
        checkCode = data[12:16]
        return calculateCheckCode(data) == checkCode

    def getRequestCode(self) -> bytes:
        assert (self.frame is not None)
        return BtoInt(self.data[4:8])

    def getId(self) -> int:
        assert (self.frame is not None)
        return BtoInt(self.data[0:4])

    def getSize(self) -> int:
        assert (self.frame is not None)
        return BtoInt(self.data[16:20])

    def getData(self) -> str:
        assert (self.frame is not None)
        return self.data[20:20 + self.getSize()].decode('utf-8')


def BtoInt(bytes: bytes) -> int:
    '''
    将4B转为int
    '''
    return int.from_bytes(bytes, 'little')


def myEncode(id: int, requestCode: int, data: int = 0) -> bytes:
    '''
    实现编码部分，自定义格式，用于非数据编码
    4B 传输编号 id 
    4B 请求码 requestCode 
    4B 序列号 sequence
    4B 校验码 checkCode
    4B 数据长度 dataSize
        数据 data
    输入为 传输编号id, 请求码 requestCode, 数据data
    输出为构造好的byte
    '''
    encodeData = None

    # 传输id
    idBytes = (id.to_bytes(4, 'little'))

    #请求码
    requestCodeBytes = ((requestCode).to_bytes(4, 'little'))

    #序列号
    sequenceBytes = data.to_bytes(4, 'little')

    #校验码
    checkCodeBytes = b'\x00\x00\x00\x00'

    #数据长度
    dataSizeBytes = b'\x00\x00\x00\x00'

    #数据
    dataBytes = bytes()

    frameBytes = idBytes + requestCodeBytes + sequenceBytes + checkCodeBytes + dataSizeBytes + dataBytes

    frameByteArray = bytearray(frameBytes)

    frameByteArray[12:16] = calculateCheckCode(frameBytes)

    frameBytes = bytes(frameByteArray)

    return frameBytes


def myEncodeData(id: int, requestCode: int, data: List[bytes]) -> List[bytes]:
    '''
    实现编码部分，自定义格式，仅用于编码数据
    4B 传输编号 id 
    4B 请求码 requestCode 
    4B 序列号 sequence
    4B 校验码 checkCode
    4B 数据长度 dataSize
        数据 data
    输入为 传输编号id, 请求码 requestCode, 数据data
    输出为构造好的list
    '''
    encodeData = []

    # 传输id
    idBytes = (id.to_bytes(4, 'little'))

    #请求码
    requestCodeBytes = ((requestCode).to_bytes(4, 'little'))

    for index, value in enumerate(data):
        # 序列号
        sequenceBytes = index.to_bytes(4, 'little')

        # 校验码
        checkCodeBytes = b'\x00\x00\x00\x00'

        # 数据长度
        dataSizeBytes = len(value).to_bytes(4, 'little')

        # 数据
        dataBytes = value

        frameBytes = idBytes + requestCodeBytes + sequenceBytes + checkCodeBytes + dataSizeBytes + dataBytes

        frameByteArray = bytearray(frameBytes)

        frameByteArray[12:16] = calculateCheckCode(frameBytes)

        frameBytes = bytes(frameByteArray)

        assert verifyCheckCode(frameBytes)

        encodeData.append(frameBytes)

    return encodeData


def calculateCheckCode(data):
    '''
    忽略校验位计算校验码
    输入为bytes
    使用奇偶校验
    TODO 换成哈希
    '''
    assert type(data) is bytes

    result = 0
    for i in data:
        result ^= i

    for i in data[12:16]:
        result ^= i

    return result.to_bytes(4, 'little')


def verifyCheckCode(data):
    '''
    验算校验码是否正确
    '''
    assert type(data) is bytes

    checkCode = data[12:16]

    return calculateCheckCode(data) == checkCode


def BtoInt(bytes: bytes) -> int:
    '''
    将4B转为int
    '''
    return int.from_bytes(bytes, 'little')


def getRequestCode(data: bytes) -> bytes:
    return BtoInt(data[4:8])


def getId(data: bytes) -> int:
    return BtoInt(data[0:4])


def getSize(data: bytes) -> int:
    return BtoInt(data[16:20])


def getData(data: bytes) -> str:
    return data[20:20 + getSize(data)].decode('utf-8')


def sendUdpTo(mySocket: socket, ip: str, port: int, frameBytes: bytes):
    '''
    使用mySocket发送UDP到ip:port
    '''
    # 校验 IP 地址格式
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        raise ValueError(f"Invalid IP address: {ip}")

    # 校验端口号范围
    if not (0 <= port <= 65535):
        raise ValueError(
            f"Invalid port number: {port}. Port must be between 0 and 65535.")

    # 校验 frameBytes 类型
    if not isinstance(frameBytes, bytes):
        raise TypeError("frameBytes must be of type bytes.")

    # 校验 frameBytes 长度
    if len(frameBytes) > 65507:
        raise ValueError(
            "frameBytes is too large. UDP datagrams should not exceed 65507 bytes."
        )

    try:
        mySocket.sendto(frameBytes, (ip, port))
    except socket.error as e:
        raise socket.error(
            f"Failed to send UDP packet to {ip}:{port}. Error: {e}")


class FrameHandler:

    def __init__(self, ):
        self.mySocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def sendUdp(self, ip: str, port: int, frameBytes: bytes):
        '''
        使用mySocket发送UDP到ip:port
        '''
        # 校验 IP 地址格式
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            raise ValueError(f"Invalid IP address: {ip}")

        # 校验端口号范围
        if not (0 <= port <= 65535):
            raise ValueError(
                f"Invalid port number: {port}. Port must be between 0 and 65535."
            )

        # 校验 frameBytes 类型
        if not isinstance(frameBytes, bytes):
            raise TypeError("frameBytes must be of type bytes.")

        # 校验 frameBytes 长度
        if len(frameBytes) > 65507:
            raise ValueError(
                "frameBytes is too large. UDP datagrams should not exceed 65507 bytes."
            )

        try:
            self.mySocket.sendto(frameBytes, (ip, port))
        except socket.timeout as e:
            raise e
        except socket.error as e:
            raise socket.error(
                f"Failed to send UDP packet to {ip}:{port}. Error: {e}")

    def receiveUdp(self) -> tuple[Frame, any]:
        try:
            data, address = self.mySocket.recvfrom(10240)
            frame = Frame()
            frame.setFrame(data)
            return frame, address
        except socket.timeout as e:
            raise e
        except socket.error as e:
            socket.error(f"socket error: {e}")

    def myEncode(self,
                 id: int,
                 requestCode: int,
                 data1: int = 0,
                 data2: int = 0) -> bytes:
        '''
        实现编码部分，自定义格式，用于非数据编码
        4B 传输编号 id 
        4B 请求码 requestCode 
        4B 序列号 sequence
        4B 校验码 checkCode
        4B 数据长度 dataSize
            数据 data
        输入为 传输编号id, 请求码 requestCode, 数据data
        输出为构造好的byte
        '''
        encodeData = None

        # 传输id
        idBytes = (id.to_bytes(4, 'little'))

        #请求码
        requestCodeBytes = ((requestCode).to_bytes(4, 'little'))

        #序列号
        sequenceBytes = data1.to_bytes(4, 'little')

        #校验码
        checkCodeBytes = b'\x00\x00\x00\x00'

        #数据长度
        dataSizeBytes = b'\x00\x00\x00\x00'

        #数据
        dataBytes = bytes()

        frameBytes = idBytes + requestCodeBytes + sequenceBytes + checkCodeBytes + dataSizeBytes + dataBytes

        frameByteArray = bytearray(frameBytes)

        frameByteArray[12:16] = calculateCheckCode(frameBytes)

        frameBytes = bytes(frameByteArray)

        return frameBytes

    def myEncodeData(self, id: int, requestCode: int,
                     data: List[bytes]) -> List[bytes]:
        '''
        实现编码部分，自定义格式，仅用于编码数据
        4B 传输编号 id 
        4B 请求码 requestCode 
        4B 序列号 sequence
        4B 校验码 checkCode
        4B 数据长度 dataSize
            数据 data
        输入为 传输编号id, 请求码 requestCode, 数据data
        输出为构造好的list
        '''
        encodeData = []

        # 传输id
        idBytes = (id.to_bytes(4, 'little'))

        #请求码
        requestCodeBytes = ((requestCode).to_bytes(4, 'little'))

        for index, value in enumerate(data):
            # 序列号
            sequenceBytes = index.to_bytes(4, 'little')

            # 校验码
            checkCodeBytes = b'\x00\x00\x00\x00'

            # 数据长度
            dataSizeBytes = len(value).to_bytes(4, 'little')

            # 数据
            dataBytes = value

            frameBytes = idBytes + requestCodeBytes + sequenceBytes + checkCodeBytes + dataSizeBytes + dataBytes

            frameByteArray = bytearray(frameBytes)

            frameByteArray[12:16] = calculateCheckCode(frameBytes)

            frameBytes = bytes(frameByteArray)

            assert verifyCheckCode(frameBytes)

            encodeData.append(frameBytes)

        return encodeData


if __name__ == '__main__':
    print(1)
