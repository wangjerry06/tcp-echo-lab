# PROJECT_PLAN —— tcp-echo-lab

> 本文档是「WorkBuddy 负责规划」的示范产物：需求拆解、里程碑、分工。
> 每完成一项就打勾 + 记录 commit hash，git 历史与文档对得上，这就是最小可用的项目治理。

## 一、项目目标

配合《网络编程学习清单》第二节"必须动手掌握的"任务，亲手经历一条完整的进阶路线：

**阻塞 echo → select 并发改造 → （远期）epoll**

同时作为第一个"WorkBuddy + CodeBuddy 双 AI 协作"的流程演练项目。

## 二、分工原则（双 AI 协作章程）

| 环节 | WorkBuddy（规划/验收位） | CodeBuddy（编辑器/执行位） | 老大（拍板位） |
|---|---|---|---|
| 规划 | 写 PRD/计划、拆任务、定验收标准 | 补充实现细节建议 | 审批计划 |
| 编码 | 出接口设计、写关键注释思路 | 在 VS Code 里写代码、看着它改 | 验收代码风格 |
| 测试 | 设计测试用例清单、跑命令验收 | 补测试、跑 unittest | 确认行为符合预期 |
| Git | 审 commit 信息、检查 diff | 小步提交、智能 commit message | 决定何时合并/打 tag |
| 交付 | 写 README/总结、沉淀笔记 | 一键部署（如需） | 最终验收 |

## 三、里程碑与任务拆解

### M1 阻塞版 echo（本次已由 WorkBuddy 搭好骨架）✅

- [x] src/server.py：socket→bind→listen→accept→recv/send→close，带概念注释
- [x] src/client.py：socket→connect→send/recv→close
- [x] tests/test_echo.py：回显 / 多客户端排队 / 客户端突断服务器不崩 / 大数据块
- [x] 全部测试通过（4/4）
- [x] git 初始提交

**验收标准（Definition of Done）**：`python3 -m unittest discover -s tests -v` 全绿。

### M2 select 并发版（⬜ 待做 —— 这就是你在 CodeBuddy 里的第一个任务）

- [ ] 新建 src/server_select.py：单线程 + select，fd 集合 = {listening fd} ∪ {connfds}
- [ ] 就绪后先查 listening fd（新连接），再查各 connfd（数据）
- [ ] recv 返回空时：close 并**从 select 集合摘掉该 fd**（新手 bug 重灾区！）
- [ ] 迁移/复用 tests，新增并发测试：两个客户端同时连着、交替发消息互不卡死
- [ ] 对比实验：开两个终端各跑一个 client，M1 版会互相卡（演示"client 1 吃午饭"病历），M2 版不会

**验收标准**：并发测试全绿 + 你能口头讲清 select 循环每一轮在干什么。

### M3 复盘交付（⬜）

- [ ] 写对比总结：threading vs select 优缺点（对着清单第一节第 7 条自查）
- [ ] `lsof -p <pid>` 观察 server 进程的 fd 表，截图存 docs/
- [ ] README 更新，tag v0.1.0

## 四、Git 约定

- 小步提交：一个任务一个 commit
- 信息格式：`M1: xxx` / `M2: xxx`，一句话说清做了什么
- 测试不过不提交（红过再绿，中间不许 commit）

## 五、决策记录

- 2026-09-27：选 Python 而非 C 作为 M1/M2 载体——socket API 与 BSD 接口一一对应，概念无损迁移；零第三方依赖，unittest 直接跑。C 版留作 M4 可选挑战。
