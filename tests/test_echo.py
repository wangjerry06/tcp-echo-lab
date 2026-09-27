"""M1 echo server 验收测试（零依赖，标准库 unittest）

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
SERVER = ROOT / "src" / "server.py"
HOST = "127.0.0.1"


def free_port() -> int:
    """向内核借一个空闲端口（bind port=0 再查实际分配值）。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, 0))
    port = s.getsockname()[1]
    s.close()
    return port


class EchoServerTest(unittest.TestCase):
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

    def test_01_echo_roundtrip(self):
        """发什么收什么。"""
        with socket.create_connection((HOST, self.port), timeout=2) as s:
            s.sendall(b"hello tcp\n")
            self.assertEqual(s.recv(4096), b"hello tcp\n")

    def test_02_multiple_sequential_clients(self):
        """iterative server：多个客户端排队，一个伺候完再接下一个。"""
        for i in range(3):
            with socket.create_connection((HOST, self.port), timeout=2) as s:
                msg = f"client-{i}\n".encode()
                s.sendall(msg)
                self.assertEqual(s.recv(4096), msg)

    def test_03_server_survives_client_close(self):
        """客户端突然断开（不发数据就 close），服务器不能崩。"""
        s = socket.create_connection((HOST, self.port), timeout=2)
        s.close()  # 立刻关闭 -> 服务端 recv 返回空 -> 走 close(connfd) 分支
        # 服务器必须还活着，且能继续接待新客户端
        self.assertIsNone(self.proc.poll(), "server 进程意外退出了！")
        with socket.create_connection((HOST, self.port), timeout=2) as s:
            s.sendall(b"still alive\n")
            self.assertEqual(s.recv(4096), b"still alive\n")

    def test_04_large_payload_echo(self):
        """一次 sendall 大块数据，验证 recv 循环读全。"""
        payload = b"x" * 65536
        with socket.create_connection((HOST, self.port), timeout=5) as s:
            s.sendall(payload)
            received = b""
            while len(received) < len(payload):
                chunk = s.recv(65536)
                if not chunk:
                    break
                received += chunk
            self.assertEqual(received, payload)


if __name__ == "__main__":
    unittest.main()
