# Agent benchmark

`tasks/` 中的 Markdown 文件可以直接复制为 GitHub Issue，或作为 Cloud Agent 的任务提示。

建议每次只选择一个任务，并始终从未修改的 `main` 分支创建新分支：

```text
main
├── fix/FIX-001-pagination
├── fix/FIX-002-search
├── fix/FIX-003-status-idempotency
├── feat/FEAT-001-bulk-create
└── feat/FEAT-002-project-metrics
```

普通测试：

```bash
pytest
```

任务验收测试：

```bash
pytest -q grader_tests/test_fix_001_pagination.py
```

为了更接近盲测，可以由编排后端保存 `grader_tests/`，推送到 GitHub 前从靶场仓库中移除该目录；Agent 完成后，再由独立验证环境检出 PR 分支并注入对应测试。

