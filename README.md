# tcp-echo-lab

网络编程第一个实战项目：从阻塞版 echo server 进化到 select 并发版。
配套《网络编程-socket与fd-学习清单》，规划与分工见 [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md)。

## 目录结构

```
tcp-echo-lab/
├── src/
│   ├── server.py        # M1: 阻塞版 echo server（带概念注释，背诵友好）
│   ├── server_select.py # M2: select 并发版（单线程 + 事件循环）
│   └── client.py        # M1: echo client
├── tests/
│   ├── test_echo.py     # M1 验收测试（零依赖，标准库 unittest）
│   └── test_select.py   # M2 并发验收测试
├── docs/
│   ├── PROJECT_PLAN.md  # 里程碑、分工、验收标准、决策记录
│   └── REVIEW.md        # M3 复盘：fd 表标本、两大 bug、threading vs select
└── README.md
```

## 跑起来

终端 1 —— 起服务器（不指定端口则随机分配并打印）：

```bash
python3 src/server.py            # 随机端口
python3 src/server.py 9000       # 固定 9000
```

终端 2 —— 起客户端，输入什么就被原样弹回什么，Ctrl+D 结束：

```bash
python3 src/client.py 127.0.0.1 9000
```

## 跑测试

```bash
python3 -m unittest discover -s tests -v
```

4 个用例覆盖：回显正确性、多客户端排队、客户端突断服务器不崩、64KB 大数据块。

## M2 已完成 ✅：select 并发版在 `src/server_select.py`

启动方式同 M1（`python3 src/server_select.py [端口]`）。双客户端交替发消息互不卡死。
复盘与 fd 表实测见 [docs/REVIEW.md](docs/REVIEW.md)。

## 学习对照表（写完 M2 你应该能回答）

1. `socket()` 三参数各是什么？返回值代表什么？
2. listening fd 和 connfd 的分工与生死？
3. 为什么 M1 版两个客户端会互相卡死？（"client 1 吃午饭"病历）
4. select 循环每一轮做了哪三件事？
5. recv 返回 `b""` 时漏做哪一步会烧掉整个进程？（fd 焊死在集合里 → 忙循环）
