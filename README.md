# API Test Framework

基于 **Python + pytest + requests** 的接口自动化测试框架：分层封装、数据驱动、环境切换、失败现场回溯、HTML 报告与 GitHub Actions CI，并附一套 Locust 性能场景。

![CI](https://github.com/auroramcy/api-test-framework/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 特性

- **分层设计**：配置层 / 请求封装层 / 业务接口层 / 用例层，职责清晰，新增接口只改两层
- **数据驱动**：用例数据放在 YAML，一份代码覆盖正常 / 边界 / 非法输入三类输入
- **环境切换**：`--env dev|test|prod` 或 `TEST_ENV`，地址与超时按环境聚合在一处
- **请求封装**：session 复用、超时控制、幂等重试、请求响应日志
- **失败现场**：用例失败时把本次的 HTTP 往来挂进终端与 HTML 报告，不用再翻日志
- **性能场景**：Locust 压测与接口用例共用同一份环境配置和接口路径
- **CI 集成**：GitHub Actions 每次 push 自动执行，报告作为 artifact 上传

## 目录结构

```
api-test-framework/
├── config/
│   ├── environments.yaml      # 环境配置：base_url / 超时 / 重试 / headers
│   └── setting.py             # 读取环境配置，Settings 单例
├── utils/
│   ├── request_util.py        # 请求封装：session / 超时 / 重试 / 日志 / 记录
│   ├── recorder.py            # 请求响应记录器（失败时挂到报告）
│   └── assertions.py          # 通用断言：状态码 / 字段类型 / 业务规则 / 正则
├── api/                       # 业务接口层，一个模块一个类
│   ├── user_api.py
│   └── post_api.py
├── data/
│   └── user.yaml              # 正常 / 边界 / 非法输入
├── testcases/
│   ├── test_user.py
│   └── test_post.py
├── perf/
│   └── locustfile.py          # 性能场景（与接口用例同源配置）
├── docs/
│   ├── report.png             # 报告截图
│   └── bug-cases.md           # 三个缺陷定位复盘
├── conftest.py                # 环境切换、日志目录、公共 fixture、失败挂载
├── pytest.ini
├── requirements.txt
└── requirements-perf.txt
```

## 快速开始

```bash
pip install -r requirements.txt

pytest                       # 全量执行
pytest -m smoke              # 只跑冒烟
pytest -m boundary           # 只跑边界与非法输入
pytest --env prod            # 切到 prod 环境
TEST_ENV=dev pytest          # 用环境变量切
```

- HTML 报告：`reports/report.html`（自包含，可直接归档或发人）
- 运行日志：`logs/run.log`（同时输出到控制台）

## 测试报告

![report](docs/report.png)

失败时报告里会多出一节 **HTTP 往来（本次用例）**，可直接看到请求参数、状态码、耗时与完整响应体。

## 性能测试

```bash
pip install -r requirements-perf.txt

# 无界面快速验证
locust -f perf/locustfile.py --headless -u 10 -r 2 -t 30s --only-summary

# 打开 Web UI 调并发
locust -f perf/locustfile.py

# 导出报告
locust -f perf/locustfile.py --headless -u 20 -r 5 -t 60s --html reports/perf.html
```

场景设计与接口用例同源：host 和 headers 从 `config/environments.yaml` 取（`PERF_ENV` 指定环境），
请求路径与 `api/*_api.py` 一致，随机 id 用 `name=` 聚合成一行统计，不会把报表打散。

## 用例设计说明

| 场景 | 用例 | 断言点 |
|---|---|---|
| 用户列表 | `test_list_users` | 200 + 非空 + 每条都带 id（不写死条数） |
| 按 ID 查询 | `test_get_user` | 200 + 8 个字段的类型 + id 回显 + email 格式（数据驱动 3 组） |
| 不存在 | `test_get_user_not_found` | 404 |
| **边界值** | `test_get_user_invalid_input` | id=0 / 11 / 999999999 → 404 且不返回数据 |
| **非法输入** | `test_get_user_invalid_input` | id=-1 / abc / 1.5 → 404 且不返回数据 |
| 创建资源 | `test_create_post` | 201 + 标题与 userId 回显 |
| **业务规则** | `test_list_posts_filtered_by_user` | 按 userId 过滤后，每条都属于该用户 |
| **业务规则** | `test_comments_belong_to_post` | 按 postId 过滤后，每条都挂在对应文章下 |
| 删除 | `test_delete_post` | 200 |
| 删除不存在 | `test_delete_non_existent_is_lenient` | 锁定演示接口当前行为（见「已知限制」） |

只断言 `status_code` 说明不了问题：接口返回 200 但数据是错的，测试照样绿。
所以上表中带「业务规则」的两条，校验的是接口承诺的业务约束，而不只是"通不通"。

## 缺陷定位案例

[`docs/bug-cases.md`](docs/bug-cases.md) 记录了三个定位过程：

1. **账单金额与流水不一致** —— 表象是漏单，根因是账期字段口径不一致（支付时间 vs 回调时间跨天）
2. **退款后状态未回滚导致重复退款** —— 根因是事务边界缺失 + 幂等键设计错误
3. **店员账号可越权查看其他门店** —— 根因是只做了功能权限、没做数据权限

## 设计取舍

- **为什么分层**：接口地址和断言散在用例里，接口一改就要全改；分层后只动 api 层
- **为什么用 YAML 不用 Excel**：数据能进 Git、能 diff、能 review
- **为什么不一开始上 Allure**：先把「跑通 + 有报告」做出来，再补展示层
- **为什么失败要挂 HTTP 往来**：断言失败时最缺的不是堆栈，是"实际返回了什么"；
  把现场直接贴在报告上，省掉「重跑 + 加 print」这一轮
- **为什么性能场景要共用配置**：功能测试改环境、压测忘了改，是这类仓库最容易出现的裂缝
- **为什么参数化 ID 用 ASCII**：pytest 会把中文 ID 转义成 `\u6b63\u5e38`，
  报告里不可读；所以 ID 用 ASCII，中文说明写进日志

## 已知限制

- **测试对象是 JSONPlaceholder 演示 API**：它没有登录、订单、金额、状态流转这些业务语义，
  因此本仓库能证明的是「框架能力」与「用例设计思路」，
  业务深度请看 [`docs/bug-cases.md`](docs/bug-cases.md)。
- **演示 API 校验宽松**：`POST /posts` 传空对象也返回 201，`DELETE` 不存在的 id 也返回 200。
  后者已写成 boundary 用例锁定现状——真实系统这里应当是 404。
- **未接数据库断言**：校验止于接口返回，没有做「接口与落库双向核对」。

## 后续可扩展

- 接入 Allure 报告，补充步骤与附件
- 增加 token 鉴权与用例级依赖编排
- 增加数据库断言层，做接口与落库的双向校验
- 性能场景纳入 CI（手动触发，设 P95 阈值）
