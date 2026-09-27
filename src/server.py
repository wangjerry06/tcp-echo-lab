#!/usr/bin/env python3
"""M1 阻塞版 TCP echo server（学习示范）

对应学习清单目标：徒手写阻塞版 echo server
API 顺序：socket -> bind -> listen -> accept -> recv/send -> close

关键概念注释（背下来）：
- listening fd：服务器启动时创建，只接待新连接，不传数据
- connfd：accept() 从内核握手队列取出的连接，真正的数据端点
- recv 返回 b"" = EOF = 对端关闭，此时必须 close(connfd)
"""

import socket
import sys

HOST = "127.0.0.1"


def serve(host: str = HOST, port: int = 0, backlog: int = 8) -> None:
    # socket() 三参数：domain=AF_INET(IPv4), type=SOCK_STREAM(TCP), protocol=0(默认)
    # 参数是我填的订单，返回值是内核发的凭证（fd）
    lfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 防 Address already in use：允许重启时立刻复用处于 TIME_WAIT 的端口
    lfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lfd.bind((host, port))
    lfd.listen(backlog)  # 扳成被动模式 + 开门摆排队椅（backlog = 队列长度）

    actual_port = lfd.getsockname()[1]
    print(f"[server] listening on {host}:{actual_port}", flush=True)

    while True:
        # accept() 阻塞，直到内核完成一次握手并从队列取出连接
        connfd, addr = lfd.accept()
        print(f"[server] connfd accepted from {addr}", flush=True)
        handle(connfd)  # 阻塞版：伺候完一个才接下一个（iterative server）


def handle(connfd: socket.socket) -> None:
    """伺候单个客户端：来什么回什么，直到对端关闭。"""
    while True:
        data = connfd.recv(4096)
        if not data:  # recv 返回空 = EOF = 对端关闭
            break
        connfd.sendall(data)
    connfd.close()  # 服务端检测到 EOF 后自己 close，两端都关才真正落幕
    print("[server] connfd closed", flush=True)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 0  # 默认随机端口
    serve(port=port)
