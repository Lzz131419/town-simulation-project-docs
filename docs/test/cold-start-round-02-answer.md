系统应拒绝执行，返回完整 Result：

```json
{
  "ok": false,
  "error": {
    "code": "INSUFFICIENT_TREASURY",
    "message": "公库119镇币，维修需120镇币，还差1镇币"
  },
  "events": []
}
```

议案保持 `APPROVED`，公库保持119镇币；清水、信任、externalSpent、rngState及世界事件均不变。可在独立的会话 diagnostics 中记录错误。

因为执行要求公库至少120镇币，当前缺1镇币，且失败必须保证原子性，不能部分扣款或产生维修效果。之后通过正常交易补足公库，可重试执行。
