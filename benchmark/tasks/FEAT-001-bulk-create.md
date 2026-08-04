# FEAT-001：批量创建任务

## 用户故事

作为项目经理，我希望一次创建最多 50 个任务，避免逐条调用接口。

## API

`POST /projects/{project_id}/tasks/bulk`

请求示例：

```json
{
  "tasks": [
    {"title": "Design API", "priority": 4},
    {"title": "Write docs", "priority": 2}
  ]
}
```

## 验收标准

- 成功时返回 201 和创建后的任务数组，顺序与输入一致。
- 每批至少 1 条、最多 50 条。
- 继续沿用单条创建的字段校验和项目内标题唯一约束。
- 标题唯一性不区分大小写、忽略首尾空格。
- 如果任意一条无效或重复，整批不能创建任何任务。
- 项目不存在时返回 404。

## 验收命令

```bash
pytest -q grader_tests/test_feat_001_bulk_create.py
```

