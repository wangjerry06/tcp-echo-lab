#!/usr/bin/env python3
"""M2 select 并发版 TCP echo server（学习示范）

对应学习清单目标：把阻塞版改造成单线程 + select 的并发版
API 顺序：socket -> bind -> listen -> select(rlist) -> accept/recv/send -> close

关键概念注释（背下来）：
- listening fd：也放进 select 的读集合，可读 = 内核握手队列里有新连接
- connfd：accept() 取出的连接，同样放进读集合，可读 = 有数据（或 EOF）
- recv 返回空 = EOF = 对端关闭，此时必须 close 并从集合里摘掉该 fd
  （忘摘 = select 每轮立刻返回 + recv 空 = 空转打满 CPU，新手 bug 重灾区！）
"""

import select
import socket
import sys

HOST = "127.0.0.1"


def serve(host: str = HOST, port: int = 0, backlog: int = 8) -> None:
    # 与 M1 相同的启动四件套
    lfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lfd.bind((host, port))
    lfd.listen(backlog)

    actual_port = lfd.getsockname()[1]
    print(f"[server-select] listening on {host}:{actual_port}", flush=True)

    # fd 集合 = {listening fd} ∪ {connfds}，select 每轮都盯着这一整锅
    readable = [lfd]

    while True:
        # select(rlist) 阻塞，直到任一 fd 可读；返回的是"本轮就绪"的子集
        rlist, _, _ = select.select(readable, [], [])

        # 就绪后先查 listening fd：可读 = 有新连接在排队
        for sock in rlist:
            if sock is lfd:
                connfd, addr = lfd.accept()
                print(f"[server-select] connfd accepted from {addr}", flush=True)
                readable.append(connfd)  # 新连接入伙，下轮开始被 select 盯着
                continue

            # 再查各 connfd：可读 = 有数据到达，或对端关闭（EOF）
            data = sock.recv(4096)
            if not data:  # recv 返回空 = EOF = 对端关闭
                # 三连：close + 从集合摘掉 fd（漏了这步 = 空转打满 CPU！）
                readable.remove(sock)
                sock.close()
                print("[server-select] connfd closed", flush=True)
                continue

            sock.sendall(data)  # 来什么回什么


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 0  # 默认随机端口
    serve(port=port)
