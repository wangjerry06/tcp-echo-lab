# tcp-echo-lab

网络编程第一个实战项目：从阻塞版 echo server 进化到 select 并发版。
配套《网络编程-socket与fd-学习清单》，规划与分工见 [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md)。

## 目录结构

```
tcp-echo-lab/
├── src/
│   ├── server.py        # M1: 阻塞版 echo server（带概念注释，背诵友好）
│   └── client.py        # M1: echo client
├── tests/
│   └── test_echo.py     # 验收测试（零依赖，标准库 unittest）
├── docs/
│   └── PROJECT_PLAN.md  # 里程碑、分工、验收标准、决策记录
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

## 接下来（M2）：把它改造成 select 并发版

用 CodeBuddy 的 Craft 模式（⌘+I），把 `docs/PROJECT_PLAN.md` 里 M2 的任务描述发给它，
建议的第一句话：

> 读一下 docs/PROJECT_PLAN.md 的 M2 部分，参照 src/server.py 的风格，新建
> src/server_select.py：单线程 + select 并发，fd 集合 = {listening fd} ∪ {connfds}，
> 注意 recv 返回空时要 close 并从集合里摘掉 fd。写完跑 python3 -m unittest 确认全绿。

## 学习对照表（写完 M2 你应该能回答）

1. `socket()` 三参数各是什么？返回值代表什么？
2. listening fd 和 connfd 的分工与生死？
3. 为什么 M1 版两个客户端会互相卡死？（"client 1 吃午饭"病历）
4. select 循环每一轮做了哪三件事？
5. recv 返回 `b""` 时漏做哪一步会烧掉整个进程？（fd 焊死在集合里 → 忙循环）
