# FEAT-002：项目任务指标

## 用户故事

作为项目负责人，我希望获取项目的任务概况，用于展示仪表盘。

## API

`GET /projects/{project_id}/metrics`

## 响应字段

- `total`：任务总数。
- `by_status`：必须包含 `todo`、`in_progress`、`done` 三个键，即使数量为 0。
- `overdue`：截止时间早于当前 UTC 时间、且状态不是 `done` 的任务数。
- `completion_rate`：`done / total`；空项目返回 `0.0`。

## 验收标准

- 项目不存在时返回 404。
- 已完成任务即使超过截止时间也不计入 overdue。
- 不修改现有任务接口。

## 验收命令

```bash
pytest -q grader_tests/test_feat_002_metrics.py
```

