# SprintPilot Cloud Agent Target

这是一个专门用于测试 Coding Agent 的“靶场仓库”。它不是 Agent 编排服务，而是被 Agent 克隆、创建分支、修改、测试和提交 PR 的目标项目。

项目是一个小型 FastAPI 任务管理 API。`main` 分支保留了若干真实但范围可控的缺陷，以及两个尚未实现的接口，用于分别测试 `fix` 和 `feat` 能力。

## 能测试什么

- 从指定基准分支创建工作分支；
- 根据 Issue 定位跨文件业务逻辑；
- 修复缺陷并补充回归测试；
- 按契约实现新接口；
- 运行测试和静态检查；
- 由独立 Reviewer 审查；
- 创建包含证据的 Pull Request。

## 技术栈

- Python 3.11+
- FastAPI
- Pydantic v2
- pytest
- Ruff
- 内存存储，无需数据库或外部服务

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
uvicorn app.main:app --reload
```

API 文档：<http://127.0.0.1:8000/docs>

## 挑战列表

| ID | 类型 | 难度 | 目标 |
|---|---|---:|---|
| FIX-001 | Fix | 简单 | 修复分页重复 |
| FIX-002 | Fix | 简单 | 修复大小写不敏感的标题/描述搜索 |
| FIX-003 | Fix | 中等 | 保证状态更新幂等和审计正确 |
| FEAT-001 | Feat | 中等 | 原子化批量创建任务 |
| FEAT-002 | Feat | 中等 | 实现项目指标接口 |

任务正文位于 [`benchmark/tasks`](benchmark/tasks)，可直接复制成 GitHub Issue。

## 基线与验收

`pytest` 默认只执行 `tests/`。这些测试在未修改的 `main` 上应全部通过，用于确认仓库本身可运行。

`grader_tests/` 是每个挑战的验收测试。未修复的 `main` 不应通过对应挑战测试。例如：

```bash
pytest -q grader_tests/test_fix_001_pagination.py
```

生产式演示建议把 `grader_tests/` 保存在你们的验证服务中，不暴露给 Coder。Reviewer 或验证器检出 Agent 的 PR 分支后，再注入验收测试。这样能避免 Agent 直接针对测试文件硬编码。

## 推荐 Agent 任务模板

```text
请处理 FIX-001。任务要求见 benchmark/tasks/FIX-001-pagination.md。

要求：
1. 基于 main 创建 fix/FIX-001-pagination 分支；
2. 先复现问题并说明根因；
3. 完成最小范围修复；
4. 添加回归测试，不得修改或删除现有测试来规避失败；
5. 运行 pytest 和 ruff check app tests；
6. 提交代码，但不要合并 main；
7. 在最终结果中给出修改文件、测试结果、残余风险和建议 PR 标题。
```

## 重置方式

每次评测都从干净的 `main` 创建新分支。不要把某个任务的修复合并回用于基准测试的 `main`；可以把成功的 PR 合并到单独的 `solutions` 分支，或者评测结束后关闭 PR。

