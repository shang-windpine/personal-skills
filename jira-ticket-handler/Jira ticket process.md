# Jira Ticket 处理流程（Agent Guide）

> 本文档面向 AI coding agent，定义处理 Jira ticket 的标准流程。放置于项目仓库 `.trellis/spec/` 下，由 Trellis 自动注入到每个 session。

## 权限边界（硬性规则，优先级最高）

1. **禁止任何线上环境操作**（包括线上开发环境、生产环境）。所有需要在线上环境执行的动作（复现、查数据、重启服务等），必须停下来列出具体步骤，由我人工执行并回传结果。
2. **不主动进行任何 Jira 写操作**（改状态、加评论、关联 PR 等）。Jira skill 仅用于读取 ticket 内容。
3. **修复方案 / 实施方案必须先与我确认**，确认通过后才能开始改代码。
4. **执行 `run-unit-test` 和 `run-integration-test` 两个 skill 之前必须先征得我的确认**，不得自行触发。
5. **最终验收由我人工完成**。agent 的验证（自查 diff、跑测试）不能替代人工验证，完成实施后停下来等我验证结果。

## 通用流程（所有 ticket 类型）

每个 Jira ticket 对应一个 Trellis task，流程映射到 Trellis 的三阶段：

### Plan 阶段
1. 通过 Jira skill 读取 ticket 全文（描述、附件、评论、日志链接）。
2. 判断 ticket 类型：Bug/Issues 或 需求类（feature / improvement / task / subtask），按下文对应章节执行分析。
3. 用 `python3 .trellis/scripts/task.py create "<ticket-key>-<简述>"` 创建 task，将分析结论写入该 task 的 `prd.md`：
   - Bug 类：复现步骤（或候选链路入口列表）、日志分析结论、根因假设、修复方案。
   - 需求类：需求要点、方案设计、涉及的模块与改动面、风险点。
4. 将分析中定位到的相关文件写入 `implement.jsonl` / `check.jsonl`，作为后续子代理的上下文。
5. **将方案提交给我确认，未确认不得进入 Execute。**

### Execute 阶段
按确认后的方案实施。遇到方案之外的必要改动，停下来说明并等我反馈，不要擅自扩大改动面。

### Finish 阶段
1. 自查 diff 是否符合方案与项目 spec（trellis-check）。
2. 需要回归测试时，向我申请执行 `run-unit-test` / `run-integration-test`，确认后运行并修复失败项（修正错误 → 再次验收，循环至通过）。
3. 停下来交由我人工验证。验证不通过则回到 Execute 修正。
4. 通过后：将本次排查/实施中的关键结论写入 `.trellis/workspace/` journal；若发现可复用的通用规律（如某类日志模式对应某类错因），用 update-spec 提炼进 `.trellis/spec/`；最后归档 task（`task.py archive`）。

## 工具入口

| 工具 | 用途 | 使用方式 |
| --- | --- | --- |
| Jira skill | 读取 ticket（只读） | 已配置，直接使用 |
| `sumologic-log-search` skill | 查询 Sumo Logic 日志 | 用于按 ticket 中的线索检索日志；若该 skill 尚未安装，则只使用 ticket 中直接附带的日志文本 |
| graphify | 代码库知识图谱，用于链路分析 | 见下方说明 |
| `run-unit-test` / `run-integration-test` skill | 回归测试 | **执行前必须经我确认** |

### graphify 用法

graphify 已在本地安装（[Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify)），将代码库通过 AST 解析为可查询的知识图谱，产物位于项目根目录的 `graphify-out/graph.json`。

- 使用前先检查 `graphify-out/graph.json` 是否存在；不存在则先构建：`/graphify .`（纯代码可用 `graphify extract . --code-only`，本地 AST 解析，无 API 开销）。代码变动较大后可用 `/graphify . --update` 增量刷新。
- 核心查询命令：
  - `graphify explain "<类名>"`：查看某个类的定义位置、调用方与被调用方（谁 imports / calls 它）。
  - `graphify path "<类A>" "<类B>"`：追踪两个类之间的调用/依赖路径。
  - `graphify query "<自然语言问题>"`：按问题返回相关子图，例如 "what calls OrderService and handles payment errors"。
- **Bug 排查中的典型用法**：从异常堆栈的 `Caused by` 链中提取应用侧类名，用 `explain` 反查其所有调用方，逐层向上追溯，收敛出可能的链路入口；用 `path` 验证"入口 → 报错点"的链路假设是否成立。
- 注意图中边带有置信标签：`EXTRACTED`（源码中显式存在）可直接采信；`INFERRED`（工具推断）需回到源码核实后再写入结论。

## Bug / Issues

背景：线上环境均通过 Docker 部署在 AWS 上。Bug 通常由 QA 在线上测试或生产环境发现，**本地无法复现不影响 bug 的真实性**，不得以"本地无法复现"为由关闭分析。

### 可复现

QA 通常会在 ticket 中写明复现步骤和复现环境：

1. 在本地开发环境按复现步骤尝试复现。
2. 本地无法复现时，整理出需要在线上开发环境执行的复现步骤，**交由我人工操作**并回传结果（agent 不得操作线上环境）。
3. 仍无法复现的，转入 [无复现步骤和复现环境](#无复现步骤和复现环境)。

复现成功即打通了处理 bug 的链路（入口和出口）：沿复现步骤梳理该请求/操作的完整执行链路（可借助 graphify 的 `path` / `explain`），定位错因，进入下方"定位后的修复流程"。

### 无复现步骤和复现环境

无法按步骤复现、或 ticket 中没有复现步骤时，转为日志驱动分析：

1. 获取日志：优先用 `sumologic-log-search` skill 按 ticket 中的时间、关键字、trace id 检索；skill 不可用时使用 ticket 附带的日志文本。
2. 从日志中的异常堆栈提取 `Caused by` 链上的应用侧类，用 graphify 反查调用关系，推断错误发生的位置与传播路径。
3. 目标是**尽可能找到链路入口**，回归到"可复现"情况的处理方法。无法确定唯一入口时，列出候选入口清单（按可能性排序，附判断依据），写入 `prd.md` 供我判断。
4. 排查过程（已验证/已排除的假设、候选入口）随时记入 workspace journal，保证跨 session 可续。

### 定位后的修复流程

1. 编写修复方案（根因、改动点、影响面、回归风险），写入 task 的 `prd.md`。
2. **与我确认方案**，确认后执行修复。
3. 修复完成后，向我申请执行 `run-unit-test` / `run-integration-test` 做回归。
4. 测试通过后停下来，**由我人工验证**。Jira 状态更新等由我处理，agent 不操作。

## 需求类（feature / improvement / task / subtask）

Bug/Issues 之外的 ticket 统一归为需求类，按通用流程（阅读需求文档 → 设计方案 → 确认 → 落地执行 → 修正错误 → 验收，循环至彻底完成）处理。两种子类型的额外要求：

### new feature

- 特别关注需求文档的完整性：对新功能可能涉及、但文档未提及的细节或改动（边界情况、错误处理、与现有功能的交互等），**不要自行假设，主动列出并让我判断和反馈**，结论补入 `prd.md`。

### improvement

- 在进入方案设计之前，必须先理解已有功能的设计、架构与执行链路：用 trellis-research 子代理（配合 graphify）梳理现状，产出写入 task 目录，再基于现状设计改动方案，避免 improvement 造成 regression。
- 方案中需明确列出可能受影响的既有行为，作为 Finish 阶段回归测试的重点。
