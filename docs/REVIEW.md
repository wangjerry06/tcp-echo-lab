# M3 复盘 —— 从阻塞到 select，病历、药方与遗留问题

> 2026-09-27。M1（阻塞版）→ M2（select 并发版）全流程复盘，对照《网络编程-socket与fd-学习清单》。

## 一、fd 表活体标本（lsof 实测）

双客户端连着 M2 服务器（端口 56123）时，`lsof -p <pid>` 的 socket 相关行：

```
COMMAND     PID     USER   FD   TYPE  DEVICE SIZE/OFF NODE NAME
python3.1  73815 wangjian   5u  IPv4 0xab86...  0t0      TCP localhost:56123 (LISTEN)
python3.1  73815 wangjian   8u  IPv4 0xee69...  0t0      TCP localhost:56123->localhost:59067 (ESTABLISHED)
python3.1  73815 wangjian   9u  IPv4 0x1a93...  0t0      TCP localhost:56123->localhost:59068 (ESTABLISHED)
```

读法（对照清单第一节）：

- **FD 0/1/2**：stdin/stdout/stderr（进程标配，上面被过滤掉了）；
- **FD 5u：LISTEN** = listening fd——迎宾，`socket→bind→listen` 的产物，永不传数据；
- **FD 8u/9u：ESTABLISHED** = 两个 connfd——服务员，`accept()` 生、`close()` 死，各自对应一个客户端的 TCP 连接；
- 注意 **fd 编号不连续**（5 → 8）：内核 fd 号会复用但不保证连续，"fd 是索引不是意义"。

## 二、病历与药方

**病历（M1）**：iterative server 单线程，`handle()` 里 `recv()` 焊死在 client 1 身上（"client 1 吃午饭"），accept 无暇接客，client 2 在内核握手队列里干等。

**药方（M2）**：单线程 + select 事件循环，每轮三件事：

1. **重建集合**：`{listening fd} ∪ {connfds}` 每轮现做（C 里 select 会覆写传入的 fd_set，集合是"一次性传单"）
2. **阻塞等待**：`select()` 拷进内核，线程睡着，任一 fd 就绪才醒
3. **扫描处理**：listening fd 可读 → `accept()` 入伙；connfd 可读 → `recv()` 回显；**recv 空 → 摘 fd + close**

## 三、两大经典 bug（面试分岔口）

| Bug | 机制 | 症状 | 记忆锚 |
|---|---|---|---|
| 漏摘 fd（EOF 不移除） | 死 fd 永远"可读"，select 秒回，recv 恒空 | **忙等空转，CPU 100%** | 多动症 |
| 漏重建集合 | 集合被覆写后缩水，listening fd 掉出监视名单 | **半聋半瞎：新客进不来、老客被无视**，CPU 正常 | 失忆症 |

排障口诀：select 服务器异常，先看 CPU——高，查"假就绪没摘"；不高但装死，查"集合缩水"。

## 四、threading vs select（清单第 7 条自查）

| 维度 | threading | select/poll |
|---|---|---|
| 并发模型 | 一客一线程，阻塞转移 | 单线程盯一堆 fd，事件分发 |
| 可读性 | 直观，像 M1 的自然延伸 | 循环 + 状态管理，心智负担高 |
| 竞态 | 有（共享状态要加锁） | 无（单线程天然串行） |
| 开销 | 线程栈 ~MB 级，切换贵 | 每轮重建集合 + 全量拷内核 + O(n) 扫描 |
| 上限 | 千级线程就喘 | FD_SETSIZE=1024 焊死 select 的监视范围 |

**优缺点互为镜像**——没有免费午餐，只有不同的账单。

## 五、进化链（远期方向）

select 的三宗罪（每轮重建、全量拷贝、O(n) 扫描）正是 **epoll 逐条改进的对象**：fd 注册一次（epoll_ctl）、内核只递就绪事件（epoll_wait 返回就绪列表）、无 1024 上限。M4 可选：epoll/kqueue 版 + LT/ET 对比。

## 六、双 AI 协作复盘（工程线）

- **运转良好的**：WorkBuddy 规划/测试设计/验收/git 治理；CodeBuddy 编辑器内写码+自补测试；老大提示词下达 + 自测三连 + 双终端实验；
- **踩过的坑**：客户端参数 `host:port` 冒号连写 → gaierror（argv 以空格分隔，一个萝卜一个坑）；
- **沉淀**：本项目全套流程（规划文档 → Craft 实现 → WorkBuddy 验收 → 小步提交）可复制到任何项目。
