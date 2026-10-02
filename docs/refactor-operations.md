# 重构操作手册

面向执行者，按阶段列出可直接敲的命令与文件改动。每阶段结束必须能通过验证项，再进入下一阶段。

前置约定：

- 所有命令在项目根目录 `D:\git_release\TelegramBot` 下、`.venv` 激活后执行。
- 每阶段完成后先跑 `ruff check src` + `ruff format --check src`，再跑该阶段的验证脚本。
- 不确定的地方停下来问，不要猜着改。
- 本手册只覆盖阶段 0～6（P0 + P1 核心），阶段 7～11 待核心落地后再补。

## 阶段 0 · 护栏

目标：装工具、写分层契约、同步 lint 配置。**不改任何业务代码**。

### 0.1 安装依赖

```powershell
pip install aiosqlite import-linter
```

### 0.2 pyproject.toml 加 aiosqlite

打开 `pyproject.toml`，在 `dependencies` 列表里加一行：

```toml
"aiosqlite>=0.20,<1.0",
```

位置随意，建议按字母序插在 `aiohttp-socks` 之后。

### 0.3 ruff.toml 同步新包名

打开 `ruff.toml`，找到 `[lint.isort]` 段，把 `known-first-party` 改成：

```toml
[lint.isort]
known-first-party = ["plugins", "utils", "core", "data", "services", "adapters", "bot"]
```

原因：现有只列了 `plugins` 和 `utils`，新增的四个包不加进去的话，ruff 会把它们的 import 排到第三方库组里，后续每阶段都会报排序错误。

### 0.4 分层契约：`.importlinter`

契约配置放项目根的 `.importlinter`（INI），**不进 pyproject**——开发工具配置不污染项目元数据。契约按阶段渐进启用：每条契约在它所约束的层落地时才写进文件。阶段 0 就写死全部契约会让 `plugins 不依赖 aiogram` 当场把未迁移的 `welcome` / `help` / `AI` 全部标红（实测 12 处违规），闸门失去基线意义。

阶段 0 的最终文件内容（当前仓库里已是这份，跑出来 `2 kept, 0 broken`）：

```ini
[importlinter]
root_packages =
    core
    data
    services
    adapters
    plugins
    utils
    bot
    exceptions
    gui
    messages
include_external_packages = True

[importlinter:contract:core-zero-deps]
name = core zero external dependencies
type = forbidden
source_modules =
    core
forbidden_modules =
    aiogram
    PySide6
    aiosqlite
    httpx
    playwright
    tenacity
    markdown
    PIL
    cv2
    numpy

[importlinter:contract:data-adapters-isolation]
name = data and adapters isolation
type = forbidden
source_modules =
    data
forbidden_modules =
    adapters
```

要点：

- `root_packages` 用裸顶层包名，与代码里 `from core import ...` 的 import 前缀一致。`root_package = src` 经实测也能工作（`src/__init__.py` 存在且 CWD 在路径上），但裸包名与运行时口径统一，不再改回。
- `include_external_packages = True` 不能少：`forbidden_modules` 里出现 aiogram 这类第三方包时，缺这行 lint-imports 直接报错退出。
- 契约名用英文：configparser 按系统编码读文件，中文契约名依赖 `PYTHONUTF8=1`（你用户环境变量已设）。英文命名则不依赖任何环境变量，换机器、进 CI 都不会崩。
- 改这个文件别用 PowerShell 的 `Set-Content -Encoding utf8`——PS 5.1 会写 BOM，configparser 报 `File contains no section headers`（实测踩过）。编辑器保存为"UTF-8 无 BOM"。

后续阶段追加的契约段落（到达对应阶段时整段贴进文件）：

| 阶段 | 追加契约 | 生效前提 |
| :--- | :--- | :--- |
| 2 | `adapters 不依赖 data`（source=adapters, forbidden=data） | data 层落地 |
| 3+4 | `services 不依赖 data 与 adapters` | services 开始被插件引用 |
| 5 | `plugins 不依赖 adapters`（先不禁 aiogram） | handler 签名改造完成 |
| 7 | `plugins 不依赖平台 SDK 与适配层` | 全部插件迁移完 |

### 0.5 验证

```powershell
# 项目根执行。新开的非登录 shell 可能没继承 PYTHONUTF8，保险起见显式设置
$env:PYTHONUTF8 = '1'
lint-imports

# lint 基线确认（此时不应引入新错误）
ruff check src
ruff format --check src
```

预期输出 `Contracts: 2 kept, 0 broken`。空壳包（core/data 等）0 imports 属正常。若新增包后报 PackageNotFound，说明 editable 安装的 .pth 没挂上新目录，补跑一次 `pip install -e ".[dev]"`。

**未来新增插件的姿势**：`plugins/` 下建目录 + `_PLUGIN_ORDER` 白名单加一行，契约对包生效、不改配置。平台独有能力写进 `adapters/` 实现，插件里 import 到会撞阶段 5/7 启用的契约——闸门替你守住"插件保持平台无关"这条线。

### 0.6 提交

```
git add pyproject.toml ruff.toml .importlinter
git commit -m "chore: 添加 aiosqlite、import-linter 与分层契约"
```

---

## 阶段 1 · core 层骨架

目标：建 `core/` 全部类型与抽象，**无实现、无第三方导入**。

### 1.1 建目录结构

```powershell
mkdir src\core\dto, src\core\domain, src\core\ports
```

### 1.2 创建文件清单

按以下顺序逐个创建，每个文件的内容见 `docs/refactor-design.md` 第三章对应小节。这里只列文件名与对应的文档章节号：

| 文件 | 文档章节 | 内容摘要 |
| :--- | :--- | :--- |
| `src/core/__init__.py` | — | 空门面，后续按需导出 |
| `src/exceptions/_domain.py` | — | 领域异常族，继承现有 `AIError`：`MessageVanishedError`、`TaskAbortedError`、`PrincipalNotFoundError`（异常基类 `BotError` 已有，禁止新建第二套） |
| `src/core/domain/__init__.py` | — | 空门面 |
| `src/core/domain/_platform.py` | 3.1 | `Platform`、`ChatScope` 命名空间类 |
| `src/core/domain/_task_meta.py` | 3.3 | `TaskKind`、`TaskStatus`、`TaskPriority` |
| `src/core/domain/_capability.py` | 4.5 | `AdapterCapability` 能力位（8 个，不含 STREAM_DRAFT） |
| `src/core/domain/_steps.py` | 5.5 | 多步会话步骤枚举（`IdentityStep`、`SystemInjectStep`） |
| `src/core/dto/__init__.py` | — | 门面，导出全部 DTO |
| `src/core/dto/_identity.py` | 3.1 | `PrincipalDTO`、`MessageRefDTO` |
| `src/core/dto/_content.py` | 3.2 | `ContentKind`、`ContentDTO` |
| `src/core/dto/_event.py` | 3.2 | `InboundEventDTO`、`CallbackEventDTO` |
| `src/core/dto/_session.py` | 3.3 | `MessageDTO`、`SessionDTO`、`SessionPatchDTO` |
| `src/core/dto/_task.py` | 3.3 | `TaskDTO`、`TaskRequestDTO`、`TaskPatchDTO` |
| `src/core/dto/_interaction.py` | 3.2 | `OutboundMedia`、`MenuSpecDTO`、`MenuActionDTO` |
| `src/core/ports/__init__.py` | — | 空门面 |
| `src/core/ports/_adapter.py` | 3.4 | `InteractionPort`、`BaseAdapter`（含 `begin_status`/`finish_status`，不含 `show_thinking`） |
| `src/core/ports/_repository.py` | 3.4 | 六个 Repository 抽象 + `UnitOfWork` |
| `src/core/ports/_queue.py` | 3.5 | `TaskQueuePort` |
| `src/core/ports/_store.py` | 3.4 | `ConversationStateStore` |
| `src/core/ports/_lifecycle.py` | 3.4 | `ConnectionLifecycle` |

### 1.3 编写要点

- 所有 DTO 用 `@dataclass(frozen=True, slots=True)`，容器字段用 `tuple`。
- 所有端口用 `ABC` + `@abstractmethod`，方法签名严格按文档 3.4/3.5 节。
- **禁止**在任何 `core/` 文件里 `import aiogram`、`import PySide6`、`import aiosqlite` 或任何其他第三方库。只允许标准库。
- docstring 首行标题不带标点、不带括号解释，详情用 `-` 起头。数字字面量提为顶部私有常量。
- 文件名带 `_` 前缀（包内实现），`__init__.py` 不带。

### 1.4 验证

```powershell
# 分层契约：core 必须全部 PASSED
lint-imports

# 类型检查（严格模式）
pyright src/core

# lint
ruff check src/core
ruff format --check src/core
```

`pyright` 若未安装：`pip install pyright`。严格模式下不应有类型错误。

### 1.5 提交

```
git add src/core/ src/exceptions/_domain.py
git commit -m "feat(core): 添加 DTO、端口与领域值对象骨架"
```

---

## 阶段 2 · data 层 + 迁移基础设施

目标：SQLite Repository 实现 + 建表 + 迁移运行器 + 备份与降级保护。**不改业务代码**。

### 2.1 建目录

```powershell
mkdir src\data\_sqlite, src\data\_migrations
```

### 2.2 连接管理

创建 `src/data/_sqlite/_connection.py`：

- 提供 `get_connection()` 异步上下文管理器，返回 `aiosqlite.Connection`。
- 连接参数：`database="data/bot.db"`，WAL 模式（`PRAGMA journal_mode=WAL`），外键开启（`PRAGMA foreign_keys=ON`）。
- per-loop 缓存连接，同一事件循环复用，不同循环各自独立。
- 数据库文件不存在时自动创建（`aiosqlite.connect` 默认行为）。

### 2.3 建表脚本

创建 `src/data/_migrations/_0001_baseline.py`：

- 内容：一个 `async def apply(conn: aiosqlite.Connection) -> None` 函数。
- 按 `docs/refactor-design.md` 5.6 节的八张表 DDL 逐条执行（principal、session_message、task、media_asset、blacklist、conversation_state、menu_action、schema_version）。
- 每条 DDL 用 `await conn.execute(...)`，全部包在一个事务里。
- 执行完毕后写入 `schema_version(version=1, applied_at=time.time(), checksum=<脚本内容sha256>)`。

### 2.4 迁移运行器

创建 `src/data/_migrations/_runner.py`：

- `async def run_migrations() -> None`：
  1. 获取连接。
  2. 查 `schema_version` 表最大 version（表不存在视为 0）。
  3. 对每个 > 当前版本的迁移脚本，按序执行 `apply(conn)`。
  4. 每个脚本执行前备份 `data/bot.db` → `data/backups/bot-{YYYYMMDD-HHmmss}.db`，保留最近 3 份。
  5. 备份失败则中止迁移、抛异常。
  6. 脚本执行成功后写入 `schema_version`。
- `SUPPORTED_SCHEMA = 1` 常量，写在文件顶部。
- `async def check_schema_compatible() -> bool`：查 DB 最大 version，若 > `SUPPORTED_SCHEMA` 返回 False。

### 2.5 Repository 实现

按 `docs/refactor-design.md` 3.4 节的六个 Repository 抽象，逐个在 `src/data/_sqlite/` 下创建实现文件：

| 文件 | 对应抽象 |
| :--- | :--- |
| `_principal.py` | `PrincipalRepository` |
| `_session.py` | `SessionRepository` |
| `_task.py` | `TaskRepository` |
| `_media.py` | `MediaRepository` |
| `_blacklist.py` | `BlacklistRepository` |
| `_state.py` | `ConversationStateStore` |

每个实现类：

- 构造函数接收 `aiosqlite.Connection`（或通过 `get_connection()` 获取）。
- 方法签名与抽象完全一致。
- SQL 语句用参数化查询，禁止字符串拼接。
- 写操作包在事务里。

### 2.6 UnitOfWork 实现

创建 `src/data/_sqlite/_unit_of_work.py`：

- `SqliteUnitOfWork` 实现 `UnitOfWork` 抽象。
- 持有连接引用，`commit()` 调 `conn.commit()`，`rollback()` 调 `conn.rollback()`。

### 2.7 门面

创建 `src/data/__init__.py`：

- 导出 `build_repositories(conn) -> dict` 工厂函数，返回各 Repository 实例。
- 导出 `run_migrations`、`check_schema_compatible`、`SUPPORTED_SCHEMA`。
- 不导出任何 `_sqlite/` 内部类。

### 2.8 验证脚本

创建 `scripts/verify_data_layer.py`（临时脚本，验证完可删）：

```python
"""data 层验证脚本

- 验证建表、CRUD、事务回滚、状态机拒绝、dedupe 索引、备份与降级保护
"""
import asyncio
import shutil
from pathlib import Path

# ... 具体验证逻辑按以下清单实现：
# 1. run_migrations() 成功，schema_version 有 version=1 的记录
# 2. PrincipalRepository.upsert + find_by_key 往返一致
# 3. SessionRepository.apply_patch 追加消息后 load 能看到
# 4. TaskRepository.insert 同 dedupe_key 第二次返回既有任务
# 5. TaskRepository.patch(status="running") 后再 patch(status="pending") 被拒绝（状态机）
# 6. 手动把 schema_version 改为 999，check_schema_compatible() 返回 False
# 7. data/backups/ 下有备份文件且不超过 3 个
# 8. 删除 data/bot.db 重跑 run_migrations()，幂等无报错
```

```powershell
python scripts/verify_data_layer.py
```

全部通过后删除脚本。

### 2.9 集成到 InitializationManager

打开 `src/bot/_managers/_initialization.py`，在 `_init_files()` 之后、`execute()` 返回之前，加入：

```python
from data import check_schema_compatible, run_migrations

# ... 在 _execute 中：
await run_migrations()
if not await check_schema_compatible():
    raise RuntimeError(
        "数据库版本高于当前代码支持版本，请升级程序或从 data/backups 恢复备份"
    )
```

注意：此时业务代码还没改，DB 是空的，迁移只是建表。这步的目的是让迁移基础设施就位，后续阶段 3+4 才会真正写入数据。

### 2.10 验证

```powershell
lint-imports          # data 层契约应全部 PASSED
ruff check src/data src/bot/_managers/_initialization.py
ruff format --check src/data src/bot/_managers/_initialization.py
python -m bot         # 应正常启动，data/bot.db 被创建，schema_version 有记录
```

启动后检查 `data/bot.db` 存在且八张表齐全。关闭程序。

### 2.11 提交

```
git add src/data/ src/bot/_managers/_initialization.py
git commit -m "feat(data): SQLite Repository、迁移运行器与降级保护"
```

---

## 阶段 3+4 · Principal 切换 + 会话收口 + 落盘改异步

这两个阶段合并为一个发布版本（都产生 schema 变更，合并避免用户连续两次不可回滚升级）。

### 3+4.1 Principal 替换 get_name

**改动文件**：`src/plugins/AI/utils.py`

- 新增 `resolve_principal(message: Message) -> PrincipalDTO` 函数，替代 `get_name`。
- 逻辑：从 `message.chat.type` 推断 `ChatScope`，从 `message.chat.id` 和 `message.from_user.id` 提取 ID，platform 固定 `"telegram"`。
- `get_name` 保留但标记 `deprecated`，内部委托给 `resolve_principal().key`，供过渡期使用。

**改动文件**：以下 8 处调用点逐个替换 `get_name(message)` → `resolve_principal(message)`：

| 文件 | 行号 |
| :--- | :--- |
| `src/plugins/AI/core/_chat_context.py` | 59 |
| `src/plugins/AI/handlers/_auth.py` | 24, 41 |
| `src/plugins/AI/handlers/_history.py` | 36, 55, 69 |
| `src/plugins/AI/handlers/_identity.py` | 86, 123 |
| `src/plugins/AI/services/_ai_chat.py` | 46 |

每改一处，把后续的 `user_sessions[user]` 字典访问暂时保留（阶段 4 才替换），只换 key 的来源。

### 3+4.2 SessionService 实现

创建 `src/services/_session.py`：

- `SessionService` 类，构造函数接收 `SessionRepository` 和 `PrincipalRepository`。
- 实现 `docs/refactor-design.md` 4.3 节的全部方法：`snapshot`、`history_for_model`、`append_exchange`、`inject_system`、`reset`、`touch`、`purge_stale`。
- `history_for_model` 内部把 `MessageDTO` 转为 `dict[str, str]`（`{"role": ..., "content": ...}`），转换收在此一处。

创建 `src/services/__init__.py`：

- 导出 `sessions`、`principals`、`tasks`、`media`、`blacklist`、`ai` 等服务实例占位（此时只有 `sessions` 和 `principals` 有真实实现，其余为 `None` 或 stub）。

### 3+4.3 替换裸 user_sessions 访问

逐个改造以下位置，把 `user_sessions[user].xxx` 换成 `SessionService` 方法调用：

| 原代码 | 位置 | 替换为 |
| :--- | :--- | :--- |
| `user_sessions[user].message.append(build_message("system", ...))` | `_identity.py:89,124` | `await sessions.inject_system(principal.key, text)` |
| `session.message.extend([...])` | `_worker.py:229` | `await sessions.append_exchange(principal.key, user_text, reply_text)` |
| `user_sessions[user].message = list(ai_config.init)` | `_history.py:57` | `await sessions.reset(principal.key)` |
| `user_sessions[user].md_status` | `_history.py:72`、`_worker.py:206` | 删除，无替代字段；渲染判定下沉到消息级（见设计文档 4.3） |
| `session.is_active = True/False` | `_ai_chat.py:70`、`_monitor.py:40,84` | 由 TaskScheduler 内部统管，插件不再直接改 |
| `user_sessions[user].last_active = time.time()` | `_chat_context.py:81` | `await sessions.touch(principal.key)` |

`session_guard` 装饰器退役：

- 删除 `_chat_context.py` 中的 `session_guard` 函数及其导出。
- 删除所有 handler 上的 `@session_guard` 装饰器。
- 会话初始化改由 `SessionPreload` 中间件承担（阶段 8 实现），过渡期在 handler 入口手动调 `await sessions.touch(principal.key)`。

### 3+4.4 同步落盘改异步

**改动文件**：`src/plugins/AI/services/_worker.py`

`_save_conversation_record` 函数（约 61-86 行）里的两个同步 `open` + `write`：

```python
# 改前
with open(rec_dir / f"staged/{user}.txt", "a", encoding="utf8") as f:
    f.write(wrt)
with open(rec_dir / f"temp/{user}.md", "a", encoding="utf8") as f:
    f.write(wrt)
```

```python
# 改后
import asyncio

await asyncio.to_thread(
    (rec_dir / f"staged/{user}.txt").write_text, wrt, encoding="utf8"
)
await asyncio.to_thread(
    (rec_dir / f"temp/{user}.md").write_text, wrt, encoding="utf8"
)
```

注意：原文是 append 模式，`write_text` 是覆盖。需改用自定义辅助函数：

```python
async def _append_text(path: Path, text: str, encoding: str = "utf8") -> None:
    """异步追加文本"""
    def _sync_append() -> None:
        with open(path, "a", encoding=encoding) as f:
            f.write(text)
    await asyncio.to_thread(_sync_append)
```

**改动文件**：`src/plugins/AI/core/_chat_context.py`

`session_guard` 里的系统提示词写文件（约 73 行）同样改 `to_thread`。但 `session_guard` 已在 3+4.3 退役，此处随之一并删除。

### 3+4.5 旧数据导入脚本

创建 `src/data/_migrations/_0002_legacy_import.py`：

- `async def apply(conn: aiosqlite.Connection) -> None`。
- 扫 `data/blacklists/blacklist.txt`，每行作为一个 principal key 插入 blacklist 表。
- 扫 `data/ai_records/temp/*.md` 与 `data/ai_records/staged/*.txt`，按固定格式反解出会话消息（格式：`时间\n\n用户：...\n\nAI思考：...\n\nAI回复：...\n\n\n\n\n`），插入 session_message 表。
- 旧 key（`u_xxx` / `g_xxx_xxx`）按映射规则转新 Principal key。
- 幂等：已存在的 principal 跳过，不重复插入。
- 执行完毕后写入 `schema_version(version=2, ...)`。

更新 `src/data/_migrations/_runner.py` 的 `SUPPORTED_SCHEMA = 2`。

### 3+4.6 验证

```powershell
lint-imports
ruff check src
ruff format --check src
python -m bot         # 应正常启动，旧黑名单与会话记录被导入
```

启动后检查：

- `data/bot.db` 的 `schema_version` 有 version=2 记录。
- `blacklist` 表行数与原 `blacklist.txt` 非空行数一致。
- `session_message` 表有数据（如果之前有过对话记录）。
- 私聊发一条消息，AI 正常回复，`session_message` 表新增 user + assistant 两条记录。
- `/clear` 命令正常清除记忆。
- `/history` 导出的文件内容与改造前一致。

### 3+4.7 CHANGELOG

在 `CHANGELOG.md` 的 `[Unreleased]` 下新增：

```markdown
### ⚠️ Breaking Changes

- **会话与任务数据落库**：从此版本起会话、黑名单、任务存入 `data/bot.db`，旧 txt 文件保留为 `.migrated` 后缀。降级到旧版需从 `data/backups` 恢复备份。
```

### 3+4.8 提交

```
git add src/services/ src/plugins/AI/ src/data/_migrations/_0002_legacy_import.py
git commit -m "feat: Principal 切换、会话收口、落盘改异步、旧数据导入"
```

---

## 阶段 5 · InteractionPort + Telegram Adapter

目标：把 aiogram 耦合收拢进 `adapters/telegram/`，业务层只调端口方法。

### 5.1 建目录

```powershell
mkdir src\adapters\base, src\adapters\telegram
```

### 5.2 BaseAdapter 与 InteractionPort 的 TG 实现

创建 `src/adapters/telegram/_interaction.py`：

- `TelegramInteractionPort(InteractionPort)` 类。
- 构造函数接收 `aiogram.Bot`。
- 实现全部端口方法：
  - `send_text` → `bot.send_message`
  - `reply_to_message` → `bot.send_message(reply_to_message_id=...)`
  - `edit_message` → `bot.edit_message_text`，捕获 `TelegramAPIError` 翻译为 `MessageVanishedError`
  - `delete_message` → `bot.delete_message`
  - `send_media` → `bot.send_document` / `bot.send_photo`
  - `begin_status` → `bot.send_message` 发占位 + `reply_markup`，返回 `MessageRefDTO`
  - `finish_status` → `bot.edit_message_text` 改写占位为最终回答 + 完整键盘
  - `direct_to_user` → 正文内嵌 `tg://user?id=` 深链
  - `mention_fragment` → 返回 markdown 深链字符串
  - `probe_exists` → 用 `bot.get_chat` 或轻量 API 探测，**不再用 dummy edit**
  - `send_inline_menu` → 本轮只留骨架，返回 `None`
  - `send_document` → `bot.send_document`

关键：原 `TelegramTaskItem` 里的 `TelegramAPIError` 字符串匹配（`"message to edit not found"` 等）全部下沉到此文件，翻译成 `MessageVanishedError` / `TaskAbortedError`。业务层再也见不到平台异常类型。

### 5.3 TelegramAdapter

创建 `src/adapters/telegram/_adapter.py`：

- `TelegramAdapter(BaseAdapter)` 类。
- `platform` 返回 `"telegram"`。
- `capabilities` 返回 `INLINE_MENU | EDIT_MESSAGE | DELETE_MESSAGE | MENTION_LINK | CALLBACK_QUERY | REPLY_QUOTE | SEND_DOCUMENT | FSM_NATIVE`。
- `interaction` 返回 `TelegramInteractionPort` 实例。
- `start` / `stop` 封装现有 `BotService` 的启停逻辑。

### 5.4 HandlerContext

创建 `src/services/_context.py`：

- `HandlerContext` frozen dataclass，字段按 `docs/refactor-design.md` 4.1 节。
- `reply`、`answer`、`direct_to`、`mention_fragment`、`send_menu` 便捷方法委托给 `interaction` 端口。

**它必须在 `services/` 而不是 `adapters/base/`**：handler 签名 `(event, ctx)` 要求插件 import `HandlerContext`，放适配层就撞上阶段 5 加的"plugins 不依赖 adapters"契约；放服务层则完全合法（插件本就允许依赖 core + services）。它持有的 `InteractionPort` 是 core 抽象，不引入任何 aiogram 依赖。

### 5.5 handler 签名改造

逐个改造 `src/plugins/AI/handlers/` 下的 handler：

- 签名从 `(message: Message, bot: Bot, state: FSMContext)` 改为 `(event: InboundEventDTO, ctx: HandlerContext)`。
- 内部 `message.answer(...)` → `await ctx.answer(...)`。
- `message.reply(...)` → `await ctx.reply(...)`。
- `Command(...)` 过滤器 → 由 `_normalize.py` 在事件归一化时解析，handler 读 `event.command_name`。
- `FSMContext` → 由 `ConversationStateStore` 替代（阶段 6 接线，本阶段先传 `None` 或 stub）。

**注意**：本阶段只改 AI 插件的 handler。`welcome.py` 和 `help/` 留到阶段 7。

### 5.6 事件归一化

创建 `src/adapters/telegram/_normalize.py`：

- `normalize_update(update: Update) -> InboundEventDTO | None` 函数。
- 从 `update.message` 提取 `PrincipalDTO`、`ContentDTO`、`MessageRefDTO`。
- 解析命令：`message.text` 以 `/` 开头时设 `is_command=True`、`command_name`、`command_args`。
- 解析回复：`message.reply_to_message` 非空时设 `reply_to`。
- 解析提及：检测 `message.entities` 中的 `mention` / `text_mention`。

### 5.7 验证

```powershell
lint-imports
ruff check src
ruff format --check src
python -m bot
```

TG 端全功能回归：

- 私聊发消息 → AI 正常回复
- 群聊触发词 → AI 正常回复
- 长消息分段发送正常
- 删除自己的消息 → 生成中断
- `/history`、`/clear`、`/on`、`/off` 正常
- 日志无 `TelegramAPIError` 泄漏到业务层

### 5.8 提交

```
git add src/adapters/ src/plugins/AI/handlers/
git commit -m "feat(adapters): Telegram Adapter、InteractionPort、handler 签名改造"
```

---

## 阶段 6 · 任务队列重写

目标：`TaskService` / `TaskScheduler` / `_HotQueue` 上线，命令包装为 Task，并发闸就位。

### 6.1 建目录

```powershell
mkdir src\services\tasks, src\services\tasks\_handlers
```

### 6.2 HotQueue

创建 `src/services/tasks/_hot_queue.py`：

- 内存优先级堆，排序键 `(priority, sequence)`。
- `push(task)`、`pop() -> TaskDTO | None`、`remove(task_id)`、`bump_to_front(task_id)`。
- `asyncio.Lock` 保护。

### 6.3 TaskRegistry

创建 `src/services/tasks/_registry.py`：

- `_handlers: dict[str, TaskHandler]` 注册表。
- `register(kind: str, handler: TaskHandler)` 装配期调用。
- `get(kind: str) -> TaskHandler | None` 运行时查询。

### 6.4 TaskHandler 实现

创建 `src/services/tasks/_handlers/_chat.py`：

- 把现有 `worker_loop` 的逻辑迁入，签名改为 `async def handle_chat(task: TaskDTO, ctx: TaskRunContext) -> None`。
- 内部调 `ctx.sessions`、`ctx.interaction`，不再直接访问全局容器。

创建 `_history.py`、`_clear.py`、`_md.py`：

- 把现有 `/history`、`/clear`、`/md` handler 的业务逻辑迁入。
- 这些命令现在走 Task 派发，自动获得排队、优先级、取消、持久化能力。

### 6.5 TaskScheduler

创建 `src/services/tasks/_scheduler.py`：

- 每 principal 一个消费协程（取代现 `monitor_loop`）。
- 全局 `asyncio.Semaphore(_MAX_CONCURRENT_TASKS)` 卡并发，默认 4。
- 单主体上限 1（维持现有队列语义）。
- pop → patch(status=RUNNING) → 查 registry 派发 handler → 结束 patch(status=SUCCEEDED/FAILED/CANCELLED)。
- `recover()` 启动时从 `TaskRepository.list_unfinished()` 重建热队列。

### 6.6 TaskService

创建 `src/services/tasks/_service.py`：

- 实现 `docs/refactor-design.md` 4.4 节全部方法。
- `enqueue` 内部：插 DB → push 热队列 → 唤醒对应 principal 的消费协程。
- `clear` 内部：DB 批量 patch CANCELLED → 热队列 remove → 向 RUNNING 任务发中断信号。

### 6.7 接线

- 在 `src/services/__init__.py` 里初始化 `TaskService`、`TaskScheduler`，注册四个 handler。
- 删除 `src/plugins/AI/core/_tasks.py` 的 `TaskQueue` 类。
- 删除 `src/plugins/AI/services/_monitor.py` 的 `monitor_loop`。
- 删除 `src/plugins/AI/state.py` 的 `user_locks`。
- 删除 `src/plugins/AI/core/_chat_context.py` 的 `active_tasks`、`task_queues`。
- 更新 `src/plugins/AI/core/__init__.py` 的 `__all__`，移除已删符号。

### 6.8 验证

```powershell
lint-imports
ruff check src
ruff format --check src
python -m bot
```

验证项：

- 私聊连发三条相同消息 → 只建一个任务（dedupe）
- `/history` 命令入队执行，结果与改造前一致
- `/clear` 命令入队执行，记忆清除正常
- 手动 kill 进程 → 重启后 `recover()` 重建队列，未完成任务继续执行
- 并发闸：把 `_MAX_CONCURRENT_TASKS` 临时改为 1，开五个用户同时提问，确认同一时刻只有一个 RUNNING

### 6.9 提交

```
git add src/services/tasks/ src/plugins/AI/core/ src/plugins/AI/services/ src/plugins/AI/state.py
git commit -m "feat(tasks): TaskService、Scheduler、并发闸、命令包装为 Task"
```

---

## 阶段间检查清单

每阶段完成后过一遍：

- [ ] `lint-imports` 全部 PASSED
- [ ] `ruff check src` 零错误
- [ ] `ruff format --check src` 零差异
- [ ] `python -m bot` 正常启动、正常对话
- [ ] CHANGELOG Unreleased 已更新（仅阶段 3+4 需要 Breaking 标注）
- [ ] git commit 信息符合 `docs/release-workflow.md` 格式

## 待定项提醒

开始阶段 3+4 前需确认 D10：`reasoning_content` 只砍展示还是连记录一起砍。

- 只砍展示：`_handle_ai_message` 保留 `reasoning_content` 分支，`final_think` 仍写入记录。
- 连记录一起砍：删除 `reasoning_content` 分支，`_save_conversation_record` 不再接收 `final_think` 参数。

两者工作量都小，但影响 `/history` 导出内容。确认后在阶段 3+4 一并处理。
