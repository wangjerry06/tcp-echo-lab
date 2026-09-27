#!/usr/bin/env python3
"""M1 阻塞版 TCP echo client（学习示范）

API 顺序：socket -> connect -> send/recv -> close
用法：echo "hello" | python3 client.py [host] [port]
"""

import socket
import sys


def main() -> None:
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9000

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))  # 客户端只要两步：socket -> connect
    print(f"[client] connected to {host}:{port}", flush=True)

    for line in sys.stdin:  # 从标准输入逐行读，发给服务器，再收回显
        s.sendall(line.encode("utf-8"))
        reply = s.recv(4096)
        if not reply:  # 服务器关闭了
            print("[client] server closed connection", flush=True)
            break
        print(f"[client] echo: {reply.decode('utf-8', errors='replace')}", end="")

    s.close()
    print("[client] bye", flush=True)


if __name__ == "__main__":
    main()
