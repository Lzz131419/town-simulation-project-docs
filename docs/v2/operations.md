# 本地运行、观测与备份

## 运行约束

只启动一个FastAPI worker。SQLite本地文件是`.local/town.db`；已有世界不删除重建。模型配置密钥位于`.local/secret.key`或环境变量，迁移数据库时须另行保留。当前没有发布外部云服务。

`TOWN_TICK_SECONDS`默认2；`TOWN_STARTUP_TIMEOUT`默认30。启动初始化超时会取消启动等待，但需先等待同步工作结束才退出，未ready不会接流量；不是强制中断线程的硬截止时间。`TOWN_DATABASE_TIMEOUT`默认3秒（SQLite锁等待或PostgreSQL连接超时，不是所有SQL的执行时限）；`TOWN_HEALTH_TIMEOUT`默认2秒。修改`backend/config/game.json`后重启加载，非法数值会在启动时拒绝，不做静默修正。市场价格/行动配方仍在catalog/actions，尚未全部抽入配置。

## 可观测性

- `/api/health/live`：进程可响应时返回200，不访问数据库。
- `/api/health`、`/api/health/ready`：数据库探测通过，世界时钟任务存活、最近一轮无失败，且成功tick距今不超过`max(5秒, 3×tick间隔)`时返回200，否则503；首次tick前以启动时间计算。返回`checks.database`和`checks.world_clock`。数据库探测超时仅取消等待，底层只读线程可能稍后完成；这不是模型供应商健康检查。
- `/metrics`：Prometheus文本；`town_online_players`、`town_ticks_total`、`town_tick_failures_total`、`town_tick_seconds_{sum,count,last}`、`town_transaction_seconds_{sum,count,last}`、`town_ws_{packets,bytes,coalesced,send_failures}_total`、`town_llm_calls{status=...}`。时长为累计/次数/最近值，不是百分位直方图。计数在首次事件后出现，LLM状态数来自数据库；其他指标在进程重启后重置。
- API响应含`X-Request-ID`，JSON日志记录请求ID、方法、路径、状态和耗时；不记录请求正文、密钥和留言。此为本进程请求关联，不是完整分布式追踪。
- tick失败回滚并记录异常堆栈；监控应同时观察失败计数和最近tick时间，不能只看HTTP健康。

## SQLite 备份与结构升级

用项目虚拟环境执行以下命令。脚本以只读方式打开源库，通过SQLite备份API获得一致性副本；创建第二份副本用于迁移，不修改源库。

```sh
.venv/bin/python scripts/verify_sqlite_migration.py --source .local/town.db
```

输出目录为`.local/schema-rehearsal-*`，包含原始`backup.db`、演练`migrated.db`与摘要`report.json`。检查全部原有表行数/内容摘要、重复升级、schema与模型一致、integrity及外键。私密数据保留在本地备份；加密密钥须另外保留。脚本适用于当前采用的加性迁移，未来故意转换数据的迁移需要专门的数据校验器。

演练通过后正常停止本项目后端，**停服状态再做一次备份**，然后升级并检查：

```sh
.venv/bin/alembic -c backend/alembic.ini upgrade head
.venv/bin/alembic -c backend/alembic.ini check
.venv/bin/python backend/run.py
```

普通启动也会执行`upgrade head`，但这不能代替发布前的备份演练。命令须在仓库根目录运行；用`TOWN_DATABASE_URL`选择隔离库。`0001`接管检查必要列/主键，不承诺自动修复任意人工改造的库；`0002`允许接管定义完全一致的已有索引，冲突时报错。`downgrade 0001`只回退索引，基础表禁止降级删除。需要数据回滚时，停服后恢复已验证的备份与对应代码版本，不能用删除数据库重新初始化代替回滚。

`npm run test:coverage`执行后端测试并要求语句覆盖率至少90%；CI增加空库升级、Alembic模型差异检查和覆盖率报告上传。覆盖率不等于生产容量验证。

## PostgreSQL 定时备份配方

`compose.yaml`包含独立`backup`服务，数据库健康后开始执行，每86400秒备份一次，成功备份保留约7天。自定义格式先写`.partial`，`pg_restore --list`检查目录后重命名为`.dump`，失败保留旧归档并写日志；健康检查使用上次成功时间。目录检查不等于完整恢复验收。备份卷为`town-backups`，不会包含模型加密密钥，也不是异地备份。

在使用Compose部署的环境手动生成一次：

```sh
docker compose run --rm -e BACKUP_ONCE=1 backup
docker compose logs backup
```

恢复演练应使用**新数据库**。以下命令中的归档文件名须替换为实际存在的文件，不覆盖运行中的town库：

```sh
docker compose exec db createdb -U town town_restore_check
docker compose run --rm --entrypoint pg_restore backup --host=db --username=town --dbname=town_restore_check --no-owner /backups/town-实际时间.dump
```

恢复后检查表、世界revision、资金守恒、会话/归档可读性，再在隔离实例做登录与行动回归。只有这些通过才能认定恢复可用；不能仅依据文件存在或`--list`成功。

本轮只验证Compose结构、shell语法及使用stub命令的成功/失败文件保留逻辑，**没有启动真实PostgreSQL备份和恢复演练**。不改变当前SQLite运行方式。
