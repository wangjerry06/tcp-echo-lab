"""M2 select 并发版验收测试（零依赖，标准库 unittest）

跑法：在项目根目录执行
    python3 -m unittest discover -s tests -v
"""

import socket
import subprocess
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "src" / "server_select.py"
HOST = "127.0.0.1"


def free_port() -> int:
    """向内核借一个空闲端口（bind port=0 再查实际分配值）。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, 0))
    port = s.getsockname()[1]
    s.close()
    return port


class SelectServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = free_port()
        cls.proc = subprocess.Popen(
            [sys.executable, str(SERVER), str(cls.port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        # 轮询等待服务器就绪，最多 5 秒
        for _ in range(50):
            try:
                probe = socket.create_connection((HOST, cls.port), timeout=0.2)
                probe.close()
                break
            except OSError:
                time.sleep(0.1)
        else:
            cls.proc.kill()
            raise RuntimeError("server 没能在 5 秒内启动")

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(timeout=5)

    def test_01_two_clients_interleave(self):
        """两个客户端同时连着、交替发消息，互不卡死（M2 核心验收点）。

        M1 阻塞版在这里会挂：client-1 不发消息时，服务器被 handle() 卡死，
        client-2 的消息永远轮不到伺候。select 版必须两个都正常回显。
        """
        c1 = socket.create_connection((HOST, self.port), timeout=2)
        c2 = socket.create_connection((HOST, self.port), timeout=2)
        try:
            # 交替发：证明单线程也在同时伺候两路
            for round_ in range(3):
                for sock, msg in ((c1, f"c1-r{round_}\n"), (c2, f"c2-r{round_}\n")):
                    sock.sendall(msg.encode())
                    self.assertEqual(sock.recv(4096), msg.encode())
        finally:
            c1.close()
            c2.close()

    def test_02_client_close_then_new_client(self):
        """客户端断开后 fd 被摘掉，服务器不崩且能继续接待新客户端。"""
        s = socket.create_connection((HOST, self.port), timeout=2)
        s.close()  # 突断 -> 服务端 recv 空 -> close + 从 select 集合摘 fd
        self.assertIsNone(self.proc.poll(), "server 进程意外退出了！")
        with socket.create_connection((HOST, self.port), timeout=2) as s2:
            s2.sendall(b"still alive\n")
            self.assertEqual(s2.recv(4096), b"still alive\n")

    def test_03_mixed_lifecycle(self):
        """先来的先断、后来的还在，一个客户端退出不影响另一个。"""
        early = socket.create_connection((HOST, self.port), timeout=2)
        late = socket.create_connection((HOST, self.port), timeout=2)
        try:
            late.sendall(b"late-1\n")
            self.assertEqual(late.recv(4096), b"late-1\n")
        finally:
            early.close()
        # early 已断，late 必须仍能正常收发
        late.sendall(b"late-2\n")
        self.assertEqual(late.recv(4096), b"late-2\n")
        late.close()


if __name__ == "__main__":
    unittest.main()
