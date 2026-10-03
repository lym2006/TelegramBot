# 重构设计方案

数据层持久化 + 跨平台适配层解耦。本文只定架构与接口契约，不含实现代码。

状态：待确认。确认后按第七节分阶段落地。

## 一、现状评估

### 1.1 可直接保留的资产

| 资产 | 位置 | 保留理由 |
| :--- | :--- | :--- |
| `BaseManager` 模板方法 | `src/bot/_managers/_base.py` | `_execute()` 契约干净，与平台无关 |
| `GUIBridge` + `SafeSignal` | `src/gui/mediator.py` | 信号按流向分组、防重连包装、跨线程屏障，设计成熟 |
| `error_guard` 分级路由 | `src/bot/error_guard.py` | fatal / 配置错误双路由 + 字段级标红，平台无关 |
| 插件白名单顺序加载 + 逐项报告 | `src/utils/plugins_register.py` | 顺序即优先级、失败不中断整体，是跨平台插件系统的好底子 |
| `_` 前缀私有 + 门面最小导出 | 全项目 | 规范执行力强，DTO 私有化顺着这套走 |
| `session_guard` 统一初始化思路 | `src/plugins/AI/core/_chat_context.py:53` | 思路对，位置错，下沉到服务层即可 |

### 1.2 阻塞性问题

按严重度排序，标注是否为跨平台硬阻塞。

**P0 · 用户标识无平台维度（硬阻塞）**

`src/plugins/AI/utils.py:62` 的 `get_name()` 产出 `u_{id}` / `g_{群}_{id}`，不含平台。QQ 与 Telegram 的 ID 空间相互独立，接入后必然撞键。而这个 key 同时是黑名单条目（`_blacklist.py:17`）、会话记录文件名（`_worker.py:69-84`）、清理循环的删除依据（`_monitor.py:115-126`）。撞键后果不是报错，是**串数据**：A 平台用户读到 B 平台用户的对话记录、被 B 平台的黑名单误伤。

**P0 · 数据所有权完全丢失（DTO 化的核心靶子）**

`src/plugins/AI/core/__init__.py:7-23` 把三个模块级可变容器 `user_sessions`、`task_queues`、`active_tasks` 直接放进 `__all__` 导出。任何插件 `from ..core import user_sessions` 即拿到裸 dict，随后：

- `_identity.py:89` — `user_sessions[user].message.append(...)`
- `_worker.py:229` — `session.message.extend([...])`
- `_history.py:57` — `user_sessions[user].message = list(ai_config.init)` 整体替换
- `_monitor.py:84-85` — 直接改 `session.is_active`、`user_locks.pop(user)`

同一份状态有五个写入方，无一处经过校验或留痕。这是"内部对象暴露出去"最典型的形态，也是持久化迁移必须先堵的口子——容器满天飞时无法确定谁是真相源。

**P0 · 数据载体即平台客户端（硬阻塞）**

`models.py:18` 的 `TaskItem.message` 字段直接持有 `aiogram.types.Message` 活体对象；`_tasks.py:32` 的 `TelegramTaskItem.__init__` 再把 `Bot` 注入自身。后果双重：

1. QQ 端完全无法复用该载体。
2. 队列里存的是活体客户端对象，**不可序列化**，持久化无从下手。要入库必须先把平台对象换成纯数据引用。

**P1 · 任务队列能力不足**

`_tasks.py:120-145` 的 `TaskQueue` 只有 `add_task` / `peek_front` / `pop_front` / `size` 四个方法，`deque` + 单锁。缺：优先级插队、单任务取消、整队清空、按用户查询、状态跟踪、进程重启恢复。目标 1.4 要求的 `priority` / `clear` / `change` 在现有结构上没有任何着力点，属于重写而非扩展。

**P1 · 平台耦合渗入 utils 层**

`utils/` 语义上应当平台无关，实际有两个文件绑死 aiogram：

- `utils/middleware.py:10-12` — `BaseMiddleware`、`Update`、`Message`、`ChatType`、`ContentType`
- `utils/plugins_register.py:11,29` — `Dispatcher`

**P1 · 平台独有能力直接散落在业务层（硬阻塞）**

`_tasks.py:110` 调用 `self.bot.send_message_draft(...)`。该方法是 Telegram 官方 Bot API 能力（9.3 引入，9.5 起对全部聊天类型开放），不是私有 fork，Telegram 端应完整保留。问题在于它被写死在业务层的 `TelegramTaskItem` 里：OneBot v11 标准只有 `send_msg` / `delete_msg`，无草稿也无编辑消息接口，QQ 端没有等价物。这类"某平台独有"的能力必须抽成能力位并由各 Adapter 自行决定有无，业务层不得直接调用。QQ 端思考态的最终形态见 4.6 节。

**P1 · 探测手段有副作用**

`_tasks.py:34-42` 的 `is_deleted()` 用 `edit_message_text(text="dummy", ...)` 探测消息是否存在——探测行为本身就把消息内容改成了 `dummy`，仅靠后续 `safe_edit` 覆盖回来。判据还是字符串匹配 `"message to edit not found"`。QQ 端语义完全不同，须抽成端口方法由各 Adapter 自行实现。

**P2 · 引擎层直接摸平台客户端**

`bot/_service.py:32` 重连判据是 `isinstance(exc, TelegramNetworkError)`；`132/142/146` 三处直接 `self._bot.session.close()`。`bot/_managers/_service.py:48` 直接 `Bot(token=..., session=SSLUnverifiedSession(...))`。引擎与平台客户端须通过连接生命周期端口隔离。

**P2 · 路由热重载 hack**

`plugins_register.py:56` 的 `router._parent_router = None` 动 aiogram 私有属性以支持重复挂载。Adapter 化后应改为每轮构建全新 Router 实例，不复用旧对象，从根上消掉这个 hack。

**P2 · 同域数据散在裸文件**

黑名单（`_blacklist.py:17` 的 txt）、对话记录（`_worker.py:61-86` 的 txt/md/html/png）、清理逻辑（`_monitor.py:115-126` 的 unlink）都是文件态。与本次数据层重构同域，应一并收进 Repository，否则新旧两套存储并存，真相源依旧不唯一。

**P2 · handler 签名绑死平台三元组**

全部 handler 签名形如 `(message: Message, bot: Bot, state: FSMContext)`，内部直接 `message.answer/reply/answer_document/answer_photo`、`Command(...)`、`StateFilter(...)`。`_identity.py:41-50` 的 `_make_mention` 拼 `tg://user?id=` 深链，正是目标 2.3 要改成 `send_message` 的 `mention` 与 `reply_ref` 正交标志的点。

## 二、目标架构

### 2.1 分层与依赖方向

```
                    ┌─────────────────────────┐
                    │   gui / messages /      │   展现与文案
                    │   exceptions            │
                    └────────────┬────────────┘
                                 │
   ┌──────────────┐   ┌──────────▼──────────┐   ┌──────────────┐
   │  adapters/   │   │     services/       │   │    data/     │
   │  telegram    │──▶│  用例编排 队列调度   │◀──│  sqlite      │
   │  onebot      │   │  AI 客户端           │   │  migrations  │
   └──────┬───────┘   └──────────┬──────────┘   └──────┬───────┘
          │                      │                     │
          │            ┌─────────▼─────────┐           │
          └───────────▶│       core/       │◀──────────┘
                       │ DTO · 端口 · 值对象 │
                       └───────────────────┘
                            零第三方依赖
```

依赖铁律：

1. `core/` 不导入任何层，也不导入 aiogram、PySide6、aiosqlite。只允许标准库。
2. `data/` 与 `adapters/` 各自实现 `core/ports/` 定义的抽象，两者互不知晓。
3. `services/` 只依赖 `core/`，通过构造函数注入端口实例，禁止 `import adapters` 或 `import data`。
4. `plugins/` 只依赖 `core/` + `services/` 门面，禁止出现任何平台 SDK 导入。
5. 上层可依赖下层，反向禁止。`core/` 是唯一被所有层依赖的底座。
6. 跨层通信只走 DTO，禁止把 `data/` 的行对象或 `adapters/` 的平台对象传到 `services/` 之上。

违规由 import-linter 契约机器拦截，不靠人工 review。契约按阶段渐进添加：每条契约在它所约束的层落地时才进配置，阶段 0 只上"core 零外部依赖"与"data 与 adapters 互不知晓"两条（详见操作手册 0.4），避免对未迁移代码全量豁免或误报刷屏。

### 2.2 目录结构建议

`_` 前缀规则严格沿用现有规范：包内实现文件带 `_`，对外门面与多消费方符号不带。

```
src/
├── core/                        平台与存储双无关的底座
│   ├── __init__.py
│   ├── dto/                     只读数据契约
│   │   ├── __init__.py          门面，导出全部 *DTO
│   │   ├── _identity.py         PrincipalDTO / MessageRefDTO
│   │   ├── _event.py            InboundEventDTO / CallbackEventDTO
│   │   ├── _content.py          ContentDTO / ContentKind
│   │   ├── _session.py          SessionDTO / MessageDTO
│   │   ├── _task.py             TaskDTO / TaskRequestDTO / TaskPatchDTO
│   │   └── _interaction.py      OutboundContentDTO / MenuSpecDTO / MenuActionDTO
│   ├── domain/                  值对象与枚举
│   │   ├── __init__.py
│   │   ├── _platform.py         Platform / ChatScope
│   │   ├── _task_meta.py        TaskKind / TaskStatus / TaskPriority
│   │   ├── _capability.py       AdapterCapability
│   │   └── _steps.py            多步会话步骤枚举
│   └── ports/                   抽象基类，只有接口没有实现
│       ├── __init__.py
│       ├── _adapter.py          BaseAdapter / InteractionPort
│       ├── _repository.py       各 Repository 抽象
│       ├── _queue.py            TaskQueuePort
│       ├── _store.py            ConversationStateStore
│       └── _lifecycle.py        ConnectionLifecycle
│
├── data/                        存储实现
│   ├── __init__.py              门面，只导出 build_repositories
│   ├── _sqlite/
│   │   ├── _connection.py       连接与事务管理
│   │   ├── _schema.py           建表 DDL 与版本号
│   │   ├── _principal.py
│   │   ├── _session.py
│   │   ├── _task.py
│   │   ├── _media.py            图片定位索引
│   │   ├── _blacklist.py
│   │   └── _state.py            多步会话状态
│   └── _migrations/
│       ├── _runner.py
│       ├── _0001_baseline.py
│       └── _0002_legacy_import.py   旧 txt 黑名单与记录文件导入
│
├── services/                    用例编排，平台无关
│   ├── __init__.py              门面：sessions / tasks / media / ai
│   ├── _session.py              SessionService，收口全部会话读写
│   ├── _identity.py             PrincipalService，身份解析与映射
│   ├── tasks/
│   │   ├── _service.py          TaskService，enqueue/clear/change/cancel
│   │   ├── _scheduler.py        消费调度与优先级仲裁
│   │   ├── _hot_queue.py        内存优先队列（DB 之上的一层）
│   │   ├── _registry.py         TaskKind → Handler 注册表
│   │   └── _handlers/           chat / history / clear / md
│   ├── _media.py                MediaIndexService
│   ├── _blacklist.py            取代现有文件态实现
│   ├── _context.py              HandlerContext 组装
│   └── ai/                      现有 AI 客户端与渲染迁入
│       ├── _client.py
│       └── _render/
│
├── adapters/                    平台适配层
│   ├── __init__.py              门面：build_adapter(platform)
│   ├── base/                    跨平台共用实现
│   │   ├── _middleware.py       EventPipeline，平台无关中间件链
│   │   ├── _access_log.py       访问日志中间件（现 LoggingMiddleware 去平台化）
│   │   ├── _plugin_loader.py    PluginSpec 加载与逐项报告
│   │   ├── _router_bridge.py    平台无关指令 → 平台路由的编译
│   │   ├── _degrade.py          交互降级策略表
│   │   └── _engine.py           事件循环线程，现 BotService 泛化
│   ├── telegram/                现 aiogram 实现全部收拢于此
│   │   ├── _adapter.py          TelegramAdapter
│   │   ├── _normalize.py        Update → InboundEventDTO
│   │   ├── _interaction.py      InteractionPort 实现，含 safe_* 系列
│   │   ├── _inline_menu.py      内联键盘（本轮只留骨架）
│   │   ├── _router.py           aiogram Router 编译产物
│   │   └── _errors.py           TelegramAPIError → 领域异常映射
│   └── onebot/                  QQ 平台
│       ├── _adapter.py          OneBotAdapter
│       ├── _api.py              OneBot HTTP + 反向/正向 WS
│       ├── _normalize.py        OneBot 事件 → InboundEventDTO
│       ├── _interaction.py      InteractionPort 实现，含引用回复降级
│       ├── _menu_fallback.py    内联菜单 → 引用回复命令映射
│       ├── _state.py            多步会话（QQ 无 FSM）
│       └── _segment.py          CQ 码 / 消息段编解码
│
├── plugins/                     平台无关业务插件
│   ├── __init__.py
│   ├── _spec.py                 PluginSpec / CommandSpec 定义
│   ├── ai/                      现 plugins/AI 去平台化后的形态
│   ├── help/
│   └── welcome/
│
├── bot/                         保留原名，装配与生命周期（见 D5）
│   ├── __init__.py
│   ├── __main__.py              入口不动，python -m bot 与启动器硬编码均保留
│   ├── _managers/               保留 BaseManager 与现有管理器
│   ├── _service.py              泛化为 AdapterRuntime，不再绑 aiogram
│   ├── error_guard.py           不动
│   └── _registry.py             新增，多 Adapter 注册与独立启停
│
├── gui/                         骨架不动，仅数据来源换成 DTO
├── messages/                    不动，继续收敛 GUI 文案
├── exceptions/                  保留体系，新增 _domain.py 领域异常族
└── utils/                       平台无关工具，middleware 与 plugins_register 迁出
```

迁移映射（旧 → 新）：

| 现有位置 | 去向 |
| :--- | :--- |
| `plugins/AI/core/models.py` | 拆入 `core/dto/_session.py`、`_task.py`，原文件删除 |
| `plugins/AI/core/_tasks.py` | `TaskQueue` → `services/tasks/`；`TelegramTaskItem` → `adapters/telegram/_interaction.py` |
| `plugins/AI/core/_chat_context.py` | 三个全局容器删除；`session_guard` → `services/_session.py` |
| `plugins/AI/state.py` | `user_locks` → `services/tasks/_scheduler.py` 私有 |
| `plugins/AI/handlers/*` | → `plugins/ai/`，签名改平台无关 |
| `plugins/AI/services/_worker.py` | → `services/tasks/_handlers/_chat.py` |
| `plugins/AI/services/_monitor.py` | `monitor_loop` → `services/tasks/_scheduler.py`；`cleanup_loop` → `services/_session.py` |
| `plugins/AI/services/_blacklist.py` | → `services/_blacklist.py` + `data/_sqlite/_blacklist.py` |
| `plugins/AI/services/_render/` | → `services/ai/_render/` |
| `plugins/AI/utils.py` | `get_name` → `services/_identity.py`；`retry_sending` → `adapters/base/` |
| `utils/middleware.py` | → `adapters/base/_access_log.py` |
| `utils/plugins_register.py` | → `adapters/base/_plugin_loader.py` |
| `bot/_service.py` | 原地泛化为 `AdapterRuntime`，平台细节移入 `adapters/base/_engine.py` |

## 三、核心抽象与 DTO 契约

以下只列签名与字段语义，不含实现体。所有 DTO 一律 `@dataclass(frozen=True, slots=True)`，容器字段用 `tuple` 而非 `list`——`frozen` 只锁顶层绑定，`list` 仍可原地 `append`，`tuple` 才是真正的不可变。

### 3.1 身份值对象

```python
# src/core/domain/_platform.py

class Platform:
    """平台标识"""

    TELEGRAM: ClassVar[str] = "telegram"
    ONEBOT: ClassVar[str] = "onebot"


class ChatScope:
    """会话作用域

    - 平台语义在此归一
    """

    PRIVATE: ClassVar[str] = "private"
    GROUP: ClassVar[str] = "group"
    SUPERGROUP: ClassVar[str] = "supergroup"
    CHANNEL: ClassVar[str] = "channel"
    UNKNOWN: ClassVar[str] = "unknown"
```

`Platform` 与 `ChatScope` 用命名空间类而非 `Enum`，与现有 `RowStatus` 风格一致，且序列化到 SQLite 时不需要 `.value` 转换。

```python
# src/core/dto/_identity.py

@dataclass(frozen=True, slots=True)
class PrincipalDTO:
    """会话主体标识

    - 取代现 get_name 的字符串拼接方案
    """

    platform: str
    scope: str
    chat_id: str
    user_id: str

    @property
    def key(self) -> str:
        """全局唯一键

        - 形如 telegram:group:-100123:456
        """
```

`chat_id` / `user_id` 一律 `str`。QQ 号与 Telegram ID 都能塞进 int，但 OneBot 的群号在部分实现里带前缀，且字符串化后跨平台拼接不会溢出，DB 列类型也统一。

`PrincipalDTO.key` 的格式是 `f"{platform}:{scope}:{chat_id}:{user_id}"`，四段定长分隔，任何一段为空补 `-`。私聊场景 `chat_id == user_id`，仍保留两段以保证格式统一、解析侧无分支。

### 3.2 事件与内容 DTO

```python
# src/core/dto/_content.py

class ContentKind:
    """内容类型

    - 覆盖现 middleware 的全部分支
    """

    TEXT: ClassVar[str] = "text"
    PHOTO: ClassVar[str] = "photo"
    DOCUMENT: ClassVar[str] = "document"
    AUDIO: ClassVar[str] = "audio"
    VOICE: ClassVar[str] = "voice"
    ANIMATION: ClassVar[str] = "animation"
    VIDEO: ClassVar[str] = "video"
    UNKNOWN: ClassVar[str] = "unknown"


@dataclass(frozen=True, slots=True)
class ContentDTO:
    """消息内容

    - 平台载荷归一后的形态
    """

    kind: str
    text: str = ""
    file_name: str = ""
    file_token: str = ""        # 平台侧文件标识，惰性下载
    image_count: int = 0
    raw_ref: MessageRefDTO | None = None
```

```python
# src/core/dto/_identity.py

@dataclass(frozen=True, slots=True)
class MessageRefDTO:
    """消息定位四元组

    - 图片定位接口的寻址依据
    """

    platform: str
    chat_id: str
    user_id: str
    message_id: str

    @property
    def key(self) -> str:
        """四元组联合键"""
```

```python
# src/core/dto/_event.py

@dataclass(frozen=True, slots=True)
class InboundEventDTO:
    """入站事件

    - 中间件与业务层的唯一事件输入
    """

    ref: MessageRefDTO
    principal: PrincipalDTO
    content: ContentDTO
    is_command: bool = False
    command_name: str = ""
    command_args: tuple[str, ...] = ()
    reply_ref: MessageRefDTO | None = None
    is_mention_bot: bool = False
    created_at: float = 0.0
    display_name: str = ""


@dataclass(frozen=True, slots=True)
class CallbackEventDTO:
    """交互回调事件

    - TG 内联按键与 QQ 引用回复命令归一到此
    """

    ref: MessageRefDTO
    principal: PrincipalDTO
    action_id: str
    payload: tuple[tuple[str, str], ...] = ()   # 有序键值对，保持 frozen
    source_message: MessageRefDTO | None = None   # 被引用的菜单消息
```

`CallbackEventDTO` 是目标 2.3 与 2.4 的汇合点：TG 的 `callback_query` 和 QQ 的"引用菜单消息回复序号"最终都归一成这个 DTO，业务层写一份 `handle_callback` 即可。

```python
# src/core/dto/_interaction.py

@dataclass(frozen=True, slots=True)
class OutboundContentDTO:
    """外发内容负载

    - kind 分派文字与媒体两种形态
    - local_path 指本机已落盘文件，仅媒体种类使用
    - file_name 缺省由 Adapter 取 local_path 末段
    - 回复关系由发送方法的 reply_ref 参数表达，不进载荷
    """

    kind: ContentKind
    text: str = ""  # 负载文字时为正文，媒体时为附言
    local_path: str = ""  # 仅媒体种类使用
    file_name: str = ""  # 对外展示文件名，缺省取 local_path 末段


@dataclass(frozen=True, slots=True)
class MenuActionDTO:
    """菜单单个按钮"""

    action_id: str
    label: str


@dataclass(frozen=True, slots=True)
class MenuSpecDTO:
    """内联菜单规格

    - title 为状态行而非动作按钮
    """

    title: str
    rows: tuple[tuple[MenuActionDTO, ...], ...] = ()
```

`file_token` 属入站方向的平台侧标识，不进外发载荷；外发只认本机路径。菜单的 QQ 降级渲染见 4.5。

### 3.3 会话与任务 DTO

```python
# src/core/dto/_session.py

@dataclass(frozen=True, slots=True)
class MessageDTO:
    """单条会话消息

    - 取代现 UserSession.message 里的裸 dict
    """

    role: str                   # system / user / assistant
    content: str
    reasoning: str = ""         # 思考过程，history_for_model 转换时丢弃
    created_at: float = 0.0


@dataclass(frozen=True, slots=True)
class SessionDTO:
    """会话快照

    - 只读投影，禁止原地修改
    """

    principal: PrincipalDTO
    messages: tuple[MessageDTO, ...] = ()
    is_active: bool = False
    last_active: float = 0.0


@dataclass(frozen=True, slots=True)
class SessionPatchDTO:
    """会话增量

    - 修改会话的唯一入参形态
    """

    append: tuple[MessageDTO, ...] = ()
    reset_to_system: bool = False
```

现有 `UserSession.message` 是 `list[dict[str, str]]`，直接喂给 AI 客户端。改造后 `SessionDTO.messages` 是 `tuple[MessageDTO, ...]`，`services/ai/_client.py` 内部再转成 API 需要的 dict 列表——转换点收在客户端一处，不散落到业务层。

```python
# src/core/domain/_task_meta.py

class TaskKind:
    """任务类型

    - 新增 AI 命令在此登记
    """

    CHAT: ClassVar[str] = "chat"
    HISTORY_EXPORT: ClassVar[str] = "history_export"
    CONTEXT_CLEAR: ClassVar[str] = "context_clear"
    MD_RENDER: ClassVar[str] = "md_render"


class TaskStatus:
    """任务状态"""

    PENDING: ClassVar[str] = "pending"
    RUNNING: ClassVar[str] = "running"
    SUCCEEDED: ClassVar[str] = "succeeded"
    FAILED: ClassVar[str] = "failed"
    CANCELLED: ClassVar[str] = "cancelled"


class TaskPriority:
    """任务优先级

    - 数值越小越优先
    """

    IMMEDIATE: ClassVar[int] = 0    # 控制类命令：清队、停止
    HIGH: ClassVar[int] = 10        # 查询类：history、md
    NORMAL: ClassVar[int] = 50      # 普通对话
    LOW: ClassVar[int] = 90         # 后台任务：记录导出等
```

```python
# src/core/dto/_task.py

@dataclass(frozen=True, slots=True)
class TaskDTO:
    """任务只读视图"""

    task_id: str
    principal: PrincipalDTO
    kind: str
    status: str
    priority: int
    source_ref: MessageRefDTO | None = None
    status_ref: MessageRefDTO | None = None    # 对应现 status_id
    payload: tuple[tuple[str, str], ...] = ()
    error_text: str = ""
    created_at: float = 0.0
    started_at: float | None = None
    finished_at: float | None = None


@dataclass(frozen=True, slots=True)
class TaskRequestDTO:
    """任务创建请求

    - enqueue 的唯一入参
    """

    principal: PrincipalDTO
    kind: str
    source_ref: MessageRefDTO | None = None
    content: ContentDTO | None = None
    priority: int = TaskPriority.NORMAL
    payload: tuple[tuple[str, str], ...] = ()
    dedupe_key: str = ""        # 防重复提交，见 5.2


@dataclass(frozen=True, slots=True)
class TaskPatchDTO:
    """任务增量

    - 状态推进与产物回填统一走此
    """

    status: str | None = None
    status_ref: MessageRefDTO | None = None
    priority: int | None = None
    error_text: str | None = None
    finished_at: float | None = None
```

`TaskDTO` 与现 `TaskItem` 的对应关系：`chat_id` / `ori_id` / `type_` 三个字段收进 `principal`；`message: Message` 换成 `source_ref: MessageRefDTO`；`status_id` 换成 `status_ref`；`draft_id` 与 `last_draft_time` 属 TG 私有的草稿机制，不进 DTO，留在 `adapters/telegram/_interaction.py` 内部状态里。

### 3.4 端口抽象

```python
# src/core/ports/_adapter.py

class InteractionPort(ABC):
    """交互端口

    - 业务层表达意图，Adapter 决定实现
    """

    @abstractmethod
    async def send_message(
        self,
        principal: PrincipalDTO,
        content: OutboundContentDTO,
        reply_ref: MessageRefDTO | None = None,
        mention: bool = False,
    ) -> MessageRefDTO | None:
        """发送单条消息

        - kind 分派平台端点，预览家族超平台限制时降级为原样发送
        - reply_ref 与 mention 是正交标志，TG 引用加深链前缀、QQ 拼引用段与 at 段
        - 私聊点名由 Adapter 忽略 at 段，退化为普通送达
        """

    @abstractmethod
    async def edit_message(self, target: MessageRefDTO, text: str) -> bool:
        """编辑已发消息

        - 不支持或失败返回 False，调用方决定降级
        - 媒体不可编辑，编辑面只有文本
        """

    @abstractmethod
    async def delete_message(self, target: MessageRefDTO) -> bool:
        """删除消息"""

    @abstractmethod
    async def probe_existence(self, target: MessageRefDTO) -> bool:
        """探测消息是否仍存在

        - 取代现有 is_deleted 的 dummy 编辑探测
        """

    @abstractmethod
    def mention_fragment(self, principal: PrincipalDTO, user_id: str) -> str:
        """生成提及文本片段

        - TG 返回 markdown 深链，可嵌进长文本
        - QQ 返回纯用户名，真点名靠 at 消息段、字符串表达不了高亮
        - 同步方法，纯字符串拼装不发请求
        """

    @abstractmethod
    async def send_status(
        self,
        principal: PrincipalDTO,
        reply_ref: MessageRefDTO,
        text: str,
        spec: MenuSpecDTO | None = None,
    ) -> MessageRefDTO | None:
        """发送状态占位消息

        - 两端均发，引用 reply_ref 指向的原消息，不点名
        - spec 非空：TG 占位挂内联键盘，QQ 占位文本降级为可操作提示
        - 返回占位 ref，后续状态推进由 TaskScheduler 统管
        - 终态删除占位后经 send_message 新发结果，结果消息不带键盘
        """
```

`send_status` 与 `send_message` 合起来把状态消息生命周期定成两端同构：占位一律发出并引用原消息（不点名），终态一律删除占位再新发结果（引用加点名）。残余差异只剩占位能否原地刷新中间态——TG 用 `edit_message` 刷新（排队到思考），QQ 无编辑能力、中间态保持原文不动，由 `EDIT_MESSAGE` 能力位覆盖。业务层写一份代码，不判断能力位、不关心平台。终态新发的 reply 目标（原消息或刚删除的占位）为待定项 D15。

```python
# src/core/ports/_adapter.py

class BaseAdapter(ABC):
    """平台适配器基类

    - 一个平台一个实例，生命周期由 runtime 托管
    """

    @property
    @abstractmethod
    def platform(self) -> str:
        """平台标识"""

    @property
    @abstractmethod
    def capabilities(self) -> int:
        """能力位掩码"""

    @property
    @abstractmethod
    def interaction(self) -> InteractionPort:
        """交互端口"""

    @abstractmethod
    async def start(self) -> None:
        """启动事件接收"""

    @abstractmethod
    async def stop(self) -> None:
        """停止并释放连接"""

    @abstractmethod
    def supports(self, capability: int) -> bool:
        """能力探测"""
```

```python
# src/core/ports/_repository.py

class PrincipalRepository(ABC):
    """会话主体仓储"""

    @abstractmethod
    async def upsert(self, principal: PrincipalDTO, display_name: str) -> PrincipalDTO:
        """写入或更新主体"""

    @abstractmethod
    async def find_by_key(self, key: str) -> PrincipalDTO | None:
        """按唯一键查询"""

    @abstractmethod
    async def list_stale(self, before: float) -> tuple[PrincipalDTO, ...]:
        """列出失活主体

        - 取代现 cleanup_loop 的内存遍历
        """


class SessionRepository(ABC):
    """会话仓储"""

    @abstractmethod
    async def load(self, key: str, limit: int | None = None) -> SessionDTO:
        """加载会话快照"""

    @abstractmethod
    async def apply_patch(self, key: str, patch: SessionPatchDTO) -> SessionDTO:
        """应用增量并返回新快照

        - 会话写入的唯一入口
        """

    @abstractmethod
    async def trim_to(self, key: str, keep_count: int) -> int:
        """裁剪历史长度，返回删除条数"""

    @abstractmethod
    async def touch(self, key: str, at: float) -> None:
        """刷新活跃时间"""


class TaskRepository(ABC):
    """任务仓储"""

    @abstractmethod
    async def insert(self, request: TaskRequestDTO) -> TaskDTO:
        """落库新任务"""

    @abstractmethod
    async def patch(self, task_id: str, patch: TaskPatchDTO) -> TaskDTO | None:
        """更新任务"""

    @abstractmethod
    async def find(self, task_id: str) -> TaskDTO | None:
        """按 ID 查询"""

    @abstractmethod
    async def list_unfinished(self, key: str) -> tuple[TaskDTO, ...]:
        """列出主体未完成任务

        - 重启恢复与 /status 展示共用
        """

    @abstractmethod
    async def list_by_status(self, status: str) -> tuple[TaskDTO, ...]:
        """按状态查询

        - 进程启动时恢复 running 中断任务
        """

    @abstractmethod
    async def delete_by_principal(self, key: str) -> int:
        """清除主体全部任务"""


class MediaRepository(ABC):
    """媒体索引仓储

    - 本轮只建接口与表结构，不接业务
    """

    @abstractmethod
    async def register(self, ref: MessageRefDTO, entry: MediaEntryDTO) -> None:
        """登记一条媒体索引"""

    @abstractmethod
    async def locate(self, ref: MessageRefDTO) -> tuple[MediaEntryDTO, ...]:
        """按四元组定位媒体

        - 目标 1.3 的落点
        """

    @abstractmethod
    async def delete_by_principal(self, key: str) -> int:
        """清除主体全部媒体索引"""


class BlacklistRepository(ABC):
    """黑名单仓储

    - 取代现 blacklist.txt
    """

    @abstractmethod
    async def add(self, key: str, reason: str = "") -> bool:
        """加入黑名单，返回是否新增"""

    @abstractmethod
    async def remove(self, key: str) -> bool:
        """移出黑名单，返回是否存在"""

    @abstractmethod
    async def contains(self, key: str) -> bool:
        """判定是否命中"""

    @abstractmethod
    async def list_all(self) -> tuple[str, ...]:
        """列出全部条目"""


class UnitOfWork(ABC):
    """事务边界

    - 跨仓储的原子操作
    """

    @abstractmethod
    async def commit(self) -> None:
        """提交"""

    @abstractmethod
    async def rollback(self) -> None:
        """回滚"""
```

`UnitOfWork` 的必要性：会话清理要同时删 principal、session_message、task、media 索引四张表，现 `cleanup_loop` 的 unlink 三连就是缺事务边界的产物（`_monitor.py:119-125`，删一半失败就留下孤儿文件）。

### 3.5 任务队列端口

```python
# src/core/ports/_queue.py

class TaskQueuePort(ABC):
    """任务队列端口

    - 目标 1.4 的完整接口面
    """

    @abstractmethod
    async def enqueue(self, request: TaskRequestDTO) -> TaskDTO:
        """入队

        - 返回已落库的任务视图
        """

    @abstractmethod
    async def next_pending(self, key: str) -> TaskDTO | None:
        """取主体最高优先级待办

        - 不出队，由 ack 确认
        """

    @abstractmethod
    async def ack(self, task_id: str) -> None:
        """确认消费"""

    @abstractmethod
    async def cancel(self, task_id: str) -> bool:
        """取消单任务

        - 已 RUNNING 的置中断标志
        """

    @abstractmethod
    async def clear(
        self, key: str, *, keep_kinds: tuple[str, ...] = ()
    ) -> int:
        """清空主体队列

        - keep_kinds 内的任务保留
        - 返回清除条数
        """

    @abstractmethod
    async def change(
        self,
        task_id: str,
        *,
        priority: int | None = None,
        payload: tuple[tuple[str, str], ...] | None = None,
    ) -> TaskDTO | None:
        """改队

        - 插队与改内容统一入口
        """

    @abstractmethod
    async def bump_to_front(self, task_id: str) -> TaskDTO | None:
        """插队到最前"""

    async def snapshot(self, principal_key: str) -> tuple[TaskDTO, ...]:
        """队列快照

        - 供 /status 之类命令与 GUI 面板展示
        """

    async def recover(self) -> int:
        """重启恢复

        - 从仓储载入未完成任务重建热队列，返回恢复条数
        """
```

`TaskHandler` 注册表：每种 `TaskKind` 注册一个处理器，签名 `async def handler(task: TaskDTO, ctx: TaskRunContext) -> None`。现有 `/history` `/clear` `/md` 全部改注册到这里，而不是各自挂在 aiogram Router 上直接执行——这样它们自动获得排队、优先级、取消、持久化能力。

## 四、服务层与适配层契约

### 4.1 处理上下文

```python
# src/services/_context.py
# 归置在 services 而非 adapters：插件 import HandlerContext 属合法的服务层依赖，
# 放适配层会撞"plugins 不依赖 adapters"契约

@dataclass(frozen=True, slots=True)
class HandlerContext:
    """处理上下文

    - handler 的唯一依赖入口
    """

    event: InboundEventDTO
    interaction: InteractionPort
    sessions: SessionService
    tasks: TaskService
    media: MediaIndexService
    principal: PrincipalDTO

    async def reply(self, text: str) -> MessageRefDTO | None:
        """回复当前事件

        - 内部走 send_message，TEXT 载荷加 reply_ref=event.ref
        """

    async def answer(self, text: str) -> MessageRefDTO | None:
        """主动发送到当前会话"""

    async def direct_to(self, user_id: str, text: str) -> MessageRefDTO | None:
        """定向投递给某用户

        - 内部走 send_message，TEXT 载荷加 mention=True
        """

    def mention_fragment(self, user_id: str) -> str:
        """取提及文本片段

        - 同步方法，用于拼长文本
        - QQ 返回纯用户名
        """
```

`HandlerContext` 取代现有 handler 的 `(message: Message, bot: Bot, state: FSMContext)` 三元组。它是 frozen 的，且只暴露服务门面而非仓储——handler 拿不到 `SessionRepository`，只能调 `SessionService` 的方法，这是 5.1 私有化约束的执行点。

### 4.2 服务门面

```python
# src/services/__init__.py
"""服务门面

- 只代发多消费方的服务实例
"""

__all__ = [
    "sessions",       # SessionService
    "principals",     # PrincipalService
    "tasks",          # TaskService
    "media",          # MediaIndexService
    "blacklist",      # BlacklistService
    "ai",             # AI 客户端门面
]
```

服务实例在 `bot/` 装配阶段构建并注入端口实现，`services/` 包内不出现 `import data` 或 `import adapters`。装配代码是唯一知道具体实现类的地方。

### 4.3 SessionService

```python
# src/services/_session.py

class SessionService:
    """会话服务

    - 会话读写的唯一入口
    """

    async def snapshot(self, key: str) -> SessionDTO:
        """取会话只读快照"""

    async def history_for_model(self, key: str, limit: int) -> tuple[dict[str, str], ...]:
        """取模型入参格式的历史

        - dict 转换收在此一处
        """

    async def append_exchange(self, key: str, user_text: str, reply_text: str) -> None:
        """追加一轮对话"""

    async def inject_system(self, key: str, text: str) -> None:
        """注入系统指令

        - 取代 _identity 里的裸 append
        """

    async def reset(self, key: str) -> None:
        """重置为初始人设

        - 取代 _history 里的整体替换
        """

    async def touch(self, key: str) -> None:
        """刷新活跃时间"""

    async def purge_stale(self) -> int:
        """清理失活会话

        - 取代 cleanup_loop 的内存遍历与 unlink 三连
        """
```

`session_guard` 装饰器退役。它的两件事（初始化会话、初始化队列）分别由 `SessionPreload` 中间件与 `TaskService.enqueue` 内部承担，不再需要每个 handler 手动挂装饰器——现有代码里 `_history.py:33,52,66` 三处重复挂载、`_identity.py:76,116` 选择性挂载的不一致也随之消失。

Markdown 渲染不设会话级标记：旧 `md_status` 随本层删除，渲染触发下沉到消息级——worker 收尾时按回复文本判含码则挂渲染按钮（TG）或接受 md 命令（QQ），产物以消息 ref 为全局键存渲染索引，命中直返图片、未中现渲。

### 4.4 TaskService

```python
# src/services/tasks/_service.py

class TaskService:
    """任务服务

    - 队列操作的唯一对外入口
    """

    async def enqueue(self, request: TaskRequestDTO) -> TaskDTO:
        """入队

        - dedupe_key 命中时返回既有任务
        """

    async def clear(self, key: str, *, keep_kinds: tuple[str, ...] = ()) -> int:
        """清空主体队列"""

    async def cancel(self, task_id: str) -> bool:
        """取消单任务"""

    async def reprioritize(self, task_id: str, priority: int) -> TaskDTO | None:
        """调整优先级"""

    async def bump_to_front(self, task_id: str) -> TaskDTO | None:
        """插队到最前"""

    async def snapshot(self, key: str) -> tuple[TaskDTO, ...]:
        """队列快照

        - 供 GUI 面板与 /status 展示
        """

    async def recover(self) -> int:
        """重启恢复

        - 从仓储载入未完成任务重建热队列
        """

    def register(self, kind: str, handler: TaskHandler) -> None:
        """登记任务处理器

        - 装配期调用，运行期只读
        """
```

### 4.5 能力协商

```python
# src/core/domain/_capability.py

class AdapterCapability:
    """平台能力位

    - 值按位或组合，supports 做与运算
    """

    INLINE_MENU: ClassVar[int] = 1 << 0        # 内联键盘
    EDIT_MESSAGE: ClassVar[int] = 1 << 1       # 编辑已发消息
    DELETE_MESSAGE: ClassVar[int] = 1 << 2     # 撤回已发消息
    MENTION_LINK: ClassVar[int] = 1 << 3       # 可点击提及深链
    SEND_DOCUMENT: ClassVar[int] = 1 << 4
    CALLBACK_QUERY: ClassVar[int] = 1 << 5     # 原生按键回调
    REPLY_QUOTE: ClassVar[int] = 1 << 6        # 引用回复
    FSM_NATIVE: ClassVar[int] = 1 << 7         # 平台自带多步状态
```

不设 draft 能力位：展示流式已整体砍除（4.6 节），`sendMessageDraft` 不再被任何路径调用。两端思考态的唯一差异是占位能否原地刷新中间态，已由 `EDIT_MESSAGE` 单个能力位覆盖。

申报值：

| 能力 | Telegram | OneBot / QQ | 说明 |
| :--- | :--- | :--- | :--- |
| `INLINE_MENU` | ✓ | ✗ | 键盘只挂状态占位，QQ 降级为占位内可操作提示 |
| `CALLBACK_QUERY` | ✓ | ✗ | QQ 由引用回复反查映射还原 |
| `EDIT_MESSAGE` | ✓ | ✗ | 决定状态占位能否原地刷新中间态，见 4.6.3 |
| `DELETE_MESSAGE` | ✓ | ✓ | QQ 撤回受群权限与 2 分钟时限限制 |
| `MENTION_LINK` | ✓ | ✗ | QQ 点名走 at 段，深链仅文本内嵌场景退化 |
| `REPLY_QUOTE` | ✓ | ✓ | QQ 降级交互的依赖 |
| `SEND_DOCUMENT` | ✓ | 部分 | QQ 走文件上传或转长图 |
| `FSM_NATIVE` | ✓ | ✗ | QQ 多步状态一律落库 |

`EDIT_MESSAGE` 在 QQ 端为 ✗ 是硬事实，不是实现受限：OneBot v11 的公开接口清单只有 `send_msg` / `delete_msg` / `get_msg`，没有编辑消息的动作。NapCat、Lagrange.OneBot、LLOneBot 都遵循这一标准接口集。

降级规则集中在 `adapters/base/_degrade.py`，不散落在各 Adapter：

| 意图 | 有能力 | 无能力时的降级 |
| :--- | :--- | :--- |
| `send_status(spec)` | TG 占位挂内联键盘 | QQ 占位文本渲染可操作提示，`action_id ↔ 命令` 映射存 DB |
| `handle_callback` | `callback_query` 直投 | 收到引用回复时反查映射表，还原成 `CallbackEventDTO` |
| `send_message(mention=True)` | TG 正文或附言前置 `tg://user?id=` 深链 | QQ 加 at 段，私聊无 at 语义时退化为普通送达；部分实现离线成员高亮受限 |
| `mention_fragment` | markdown 深链，可嵌长文本 | 纯用户名，at 是消息段无法嵌进文本 |
| `send_status` | 发「正在思考中」占位引用原消息返回 ref，中间态 `edit_message` 原地刷新 | 占位同样发出并引用原消息，无编辑能力则中间态不刷新；终态删占位后新发，与 TG 同构 |
| `edit_message` | 直接编辑 | 撤回后重发，`degraded` 置真，返回新的 `MessageRefDTO`。QQ 侧占位中间态不刷新，故极少触发 |

引用与点名不设独立投递方法：OneBot v11 消息段规范中 at 段与 reply 段各自独立、可同条共存，点名不必借道引用，故 `send_message` 用 `reply_ref` 与 `mention` 两个正交标志表达，`direct_to_user` 退役。`mention_fragment` 独立保留：TG 深链是可嵌进长文本的片段，QQ 的 at 是消息段无法内嵌，片段形态差异仍在。`_identity.py:41-50` 的 `_make_mention` 深链拼装移入 TG Adapter，业务层只声明引用谁、点名谁。

QQ 端引用回复的应答识别流程：

```
send_status(spec=菜单)
  → QQ 降级发文本「正在思考… 可回复：1 停止」
  → 写 menu_action 表：(message_id, "1") → action_id
用户引用该消息回复「1」
  → normalize 时 reply_ref 命中 menu_action 表
  → 产出 CallbackEventDTO(action_id)
  → 与 TG 按键回调走完全相同的下游处理
```

核心层对两端无感知，这是目标 2.3 与 2.4 的落点。

### 4.6 思考态：砍除展示流式，保留传输流式

**定案（D8/D9）**：删除思考过程的界面展示，两端一律静默等待，完成后输出最终回答。draft 机制整体退役。

#### 4.6.1 两个"流式"必须分开

本节唯一需要辨清的概念，混为一谈会得出错误结论：

| | 含义 | Telegram | OneBot / QQ |
| :--- | :--- | :--- | :--- |
| **展示流式** | 用户看到消息内容逐字长出 | 技术上可做，本轮决定不做 | **协议层不可能** |
| **传输流式** | bot 以 SSE 从 AI 服务商逐块收 token | **保留** | **保留** |

展示流式在 QQ 端不可能：OneBot v11 公开接口只有 `send_msg` / `delete_msg` / `get_msg`，既无编辑消息也无草稿；用撤回重发模拟则受 2 分钟时限约束，且每次撤回都向全群推送系统提示，高频刷新等于刷屏并可能触发风控。NapCat、Lagrange.OneBot、LLOneBot 均遵循此标准接口集，属协议边界而非实现缺陷。

传输流式与平台无关：它是本程序与 AI 服务商之间的 HTTP 行为，聊天平台完全不参与。`AIClient.stream_chat`（`core/_client.py:31`）两端共用，一行不改。

#### 4.6.2 为何砍掉展示后仍保留 `stream_chat` 的 yield

三条理由均与界面无关，其中第一条是决定性的。

**① 超时语义完全不同。** `base_client.py:38-43` 构造 `httpx.Timeout(read=timeout)`，而 `timeout` 取自用户配置的 `global.network_timeout`：

| 模式 | `read` 超时的含义 | 后果 |
| :--- | :--- | :--- |
| 流式 | 等**下一块**数据的最长时间 | token 持续到达，间隔远小于超时值；连接真卡死才触发 |
| 非流式 | 等**整个响应**的最长时间 | 推理模型生成上百秒属正常，会误触发 `RequestTimeoutError` |

改成非流式就必须把超时调到覆盖最坏生成时长，代价是连接真卡死时要干等同样久才发现。流式让同一个超时值既能快速发现卡死、又不误杀长回答，纯收益。

**② 取消能力依赖它。** 用户删除自己的消息可中断生成（`_tasks.py:34` 的 `is_deleted()` → `AITaskStoppedError`），靠的是能在 `async for` 中提前 break。非流式只能等响应返回。

**③ 记录仍要 `reasoning_content`。** `_save_conversation_record`（`_worker.py:61`）把 `final_think` 写进 txt/md，`/history` 发给用户的正是该文件。只要记录保留思考内容，解析循环就得留着。

> D10 定案（2026-10-02，用户）：只砍展示、仍写入记录。`/history` 导出内容不变，思考过程另提供查看命令按消息读取。

#### 4.6.3 两端最终形态

TG 端——占位引用原消息，完成时删占位后引用加 at 新发结果：

```
用户提问
  → send_status 发「🧠 正在思考中」引用原消息（不 at），挂 [停止生成]
  → 等待期中间态经 edit_message 原地刷新（排队到思考），失败则跳过
  → 完成：delete_message 删占位，键盘随之消失
  → send_message 最终回答 + 引用原消息 + mention，不带键盘，后续操作靠命令
```

QQ 端——流程同构，仅中间态不刷新：

```
用户提问
  → send_status 发占位引用原消息（不 at），spec 降级为占位内可操作提示
  → 等待期无编辑能力，占位保持原文不动
  → 完成：delete_msg 删占位
  → send_msg 最终回答 + 引用段 + at 段，不带菜单
```

占位与终态的收发骨架两端一致，残余差异只剩占位能否原地刷新中间态，由 `EDIT_MESSAGE` 单个能力位覆盖。终态新发的 reply 目标指向原消息还是刚删除的占位，为待定项 D15：指向已删消息时 QQ 端引用会显示失效，TG 端静默丢引用，实测前按指向原消息实现。draft、节流、分档等机制仍不需要。

内联键盘两端都不受影响：键盘挂的是最终那条持久消息，与思考态展示本就是两件事。draft 是临时预览气泡、不可挂 `reply_markup`，这正是当初它无法与键盘共存的原因——现在 draft 整体退役，该矛盾自然消失。

#### 4.6.4 随之删除与保留的清单

删除：

| 对象 | 位置 |
| :--- | :--- |
| `show_thinking` 端口方法 | 本轮设计新增，直接不设 |
| `STREAM_DRAFT` 能力位 | 同上 |
| draft 调用与字段 | `_tasks.py:104-114` 的 `safe_draft`、`draft_id`、`last_draft_time` |
| 思考态 UI 更新 | `_worker.py:128-151` 的 `_update_thinking_ui` |
| 收尾更新中的草稿分支 | `_worker.py:168-171` |
| 节流配置 | `config.py:33` 的 `think_throttle_sec` |

保留：

| 对象 | 位置 | 理由 |
| :--- | :--- | :--- |
| `stream_chat` 及其 yield | `core/_client.py:31`、`base_client.py:70` | 见 4.6.2 |
| `_handle_ai_message` 流式循环 | `_worker.py:92` | 承载取消能力与内容累加 |
| 状态消息占位 | `_ai_chat.py:61` 的 `safe_reply(preview)` | 两端均发，QQ 端中间态不刷新 |
| `safe_edit` | `_tasks.py:77` | TG 端刷新占位中间态，终态不走编辑 |
| 分段发送 | `_worker.py:38` 的 `_send_long_message` | 不依赖编辑能力，两端通用 |

`_handle_ai_message` 的事件类型从四类减为三类：`think` 分支删除，保留 `chunk`（累加正文）、`final`（收尾）、`error`（异常）。`worker_loop` 的 `match` 相应去掉 `case "think"`。

## 五、关键机制设计

### 5.1 私有化与 DTO 边界

四条强制约束：

1. **禁止导出可变容器**。`user_sessions` / `task_queues` / `active_tasks` 这类模块级 dict/set 一律消失，改为服务实例持有私有状态。全项目搜索 `dict[` 出现在 `__all__` 导出符号类型里的，视为违规。
2. **仓储是唯一数据出入口**。任何模块要读写会话、任务、黑名单、记录，只能通过注入的 Repository / Service，不得直连 DB，也不得持有他人返回的可变对象。
3. **DTO 不可变**。`frozen=True, slots=True` + `tuple` 字段，从类型层面杜绝原地修改。需要"改"就产出新 DTO。
4. **领域实体不出包**。`data/_sqlite/` 内部的行对象、`services/tasks/` 内部的调度节点，全部 `_` 前缀且不进 `__all__`。跨包只流通 DTO。

落地手段：

- `core/` 各门面 `__init__.py` 严格执行"门面最小导出"，只代发多消费方符号。
- 阶段 0 引入 import-linter 契约，机器拦跨层导入。
- 提供 `services/` 单一门面，插件只 `from services import sessions, tasks`，不允许深挖子模块。

现有违规点的对应改法：

| 现状 | 位置 | 改法 |
| :--- | :--- | :--- |
| `user_sessions[user].message.append(...)` | `_identity.py:89,124` | `await ctx.sessions.inject_system(key, text)` |
| `session.message.extend([...])` | `_worker.py:229` | `await ctx.sessions.append_exchange(key, user_text, reply_text)` |
| `user_sessions[user].message = list(ai_config.init)` | `_history.py:57` | `await ctx.sessions.reset(key, system_prompt=...)` |
| `session.is_active = True/False` | `_ai_chat.py:70`、`_monitor.py:40,84` | 调度器内部经 `set_active` 统管，插件不可见 |
| `user_locks.pop(user, None)` | `_monitor.py:85` | 锁归调度器私有，不对外暴露 |
| `task.status_id = sent.message_id` | `_ai_chat.py:66` | `TaskPatchDTO(status_ref=...)` 经 `patch` |
| `task.draft_id = int(time.time_ns() % 2**63)` | `_worker.py:207` | 草稿机制封进 Adapter，业务层不再持有 draft_id |

### 5.2 任务队列

双层结构，这是本节最重要的取舍：

```
TaskService.enqueue(req)
   ├─▶ TaskRepository.insert()      持久化，status=PENDING，分配 sequence
   └─▶ _HotQueue.push(task)         内存优先级堆，排序键 (priority, sequence)

TaskScheduler
   ├─ 每 principal 一个消费协程，取代现 monitor_loop
   ├─ pop → patch(status=RUNNING) → 查 _registry 派发 TaskHandler
   └─ 结束 → patch(status=SUCCEEDED / FAILED / CANCELLED)

进程启动
   └─ TaskService.recover() → list_unfinished() → 重建热队列
```

为什么不全走 DB：队列消费是进程内高频操作，每次 pop 都查库会引入毫秒级延迟和写锁竞争，且 `asyncio` 的等待唤醒语义无法用 DB 表达。为什么不只走内存：进程崩溃或重启后排队中的任务全丢，用户视角是"消息发了没回应"。

分层职责：**DB 是真相源与恢复依据，内存堆是调度加速器**。两者由 `TaskService` 单点协调，`patch` 成功才动堆，保证不出现堆里有而库里没有的幽灵任务。

优先级语义，数值越小越优先：

```python
class TaskPriority:
    """任务优先级档位"""

    IMMEDIATE: ClassVar[int] = 0     # 控制类：清队、停止
    HIGH: ClassVar[int] = 10         # 命令类：/history /clear /md
    NORMAL: ClassVar[int] = 50       # 普通对话
    LOW: ClassVar[int] = 90          # 后台：记录导出等
```

三个队列操作的语义边界：

| 操作 | 作用范围 | RUNNING 任务如何处理 |
| :--- | :--- | :--- |
| `cancel(task_id)` | 单任务 | 走协作式中断：置取消标志，Handler 在流式循环的检查点自行退出，复用现有 `AITaskStoppedError` 通路 |
| `clear(principal_key)` | 该主体全部 PENDING | 同上，逐个发中断信号 |
| `change(task_id, priority=)` | 单任务 | 仅 PENDING 可改优先级，RUNNING 拒绝并返回原任务 |

`clear` 对 `CONTEXT_CLEAR` 这类任务本身要放行，否则会出现"清队把清队指令自己清掉了"的死锁，靠 `keep_kinds` 参数解决。

现有 `TelegramTaskItem` 的拆解去向：

| 原成员 | 去向 |
| :--- | :--- |
| `message: Message` | 删除，换成 `TaskDTO.source_ref: MessageRefDTO` |
| `chat_id` / `ori_id` / `type_` | 收进 `PrincipalDTO` |
| `status_id` | `TaskDTO.status_ref: MessageRefDTO` |
| `draft_id` / `last_draft_time` | **删除**，展示流式已砍除（4.6） |
| `bot: Bot` | 删除，Adapter 私有 |
| `is_deleted()` | `InteractionPort.probe_existence()` |
| `safe_delete()` | `InteractionPort.delete_message()` |
| `safe_reply()` | `InteractionPort.send_message(reply_ref=...)`，点名加 mention，占位场景走 `send_status()` |
| `safe_edit()` | `InteractionPort.edit_message()`，终态走删除占位加 `send_message` 重发，降级逻辑移入 Adapter |
| `safe_draft()` | **删除**，不设替代端口 |

原方法里的 `TelegramAPIError` 字符串匹配（`_tasks.py:42,70-72,90,96`）全部下沉到 Telegram Adapter 内部，翻译为领域异常 `MessageVanishedError` / `TaskAbortedError`。业务层再也见不到平台异常类型。

### 5.3 跨平台 middleware 日志

现有 `LoggingMiddleware` 拆三段，只有第一段有平台代码：

```
[平台相关] Adapter.normalize()        Update → InboundEventDTO
                                        OneBot 帧 → InboundEventDTO
                    ↓
[平台无关] EventPipeline.middlewares   AccessLogMiddleware 只吃 InboundEventDTO
                    ↓
[平台无关] adapters/base/_log_format.py  format_access_log(event) -> str
```

`AccessLogMiddleware` 变成**全项目唯一一份实现**，两个 Adapter 共用，不含任何 `import aiogram`。现有 `_build_log_entry` 的中文格式串（`middleware.py:67-123`）平移进 `_log_format.py`，映射表键从 `ChatType` 换成 `ChatScope`：

```python
_SCOPE_LABELS: dict[ChatScope, str] = {
    ChatScope.PRIVATE: "私聊",
    ChatScope.GROUP: "群组",
    ChatScope.SUPERGROUP: "超级群",
    ChatScope.CHANNEL: "频道",
    ChatScope.UNKNOWN: "未知",
}
```

内容预览的 `match content_type` 换成 `match event.content.kind`，`ContentKind` 覆盖 `TEXT / DOCUMENT / PHOTO / AUDIO / VOICE / ANIMATION / OTHER`，与现有分支一一对应。日志格式加平台前缀以区分来源：

```
[TG] 超级群[-100123]<测试群> | 用户123<张三> 发送[长度：5]文本：你好
[QQ] 群组[123456]<测试群> | 用户789<李四> 发送[回复][长度：3]文本：1
```

`[回复]` 标记原样保留（现有 `middleware.py:97` 的 `reply_mark`），QQ 端因为降级交互会频繁出现这个标记，正好用于排障。

管道中间件顺序固定：`AccessLog → Blacklist → RateLimit → SessionPreload → Router`。日志放最前，保证被黑名单拦掉的事件也留痕，与现有行为一致（现在挂在 `outer_middleware`，先于全部 handler）。

### 5.4 插件系统契约

插件导出物从裸 `router` 改为 `PluginSpec`：

```python
# src/plugins/_spec.py

@dataclass(frozen=True, slots=True)
class CommandSpec:
    """指令声明

    - 平台无关的指令元数据
    """

    name: str                            # history，不含斜杠
    aliases: tuple[str, ...] = ()
    help_text: str = ""
    scopes: tuple[ChatScope, ...] = ()   # 空表示全部
    allow_group: bool = True
    priority: int = TaskPriority.HIGH    # 入队优先级
    as_task: bool = True                 # 是否包装为 Task 执行
    task_kind: str = ""                  # as_task 为真时必填


@dataclass(frozen=True, slots=True)
class PluginSpec:
    """插件规格

    - 插件的唯一对外产物
    """

    name: str
    version: str = ""
    commands: tuple[CommandSpec, ...] = ()
    message_handler: MessageHandler | None = None    # 兜底消息处理
    callback_handler: CallbackHandler | None = None  # 菜单应答处理
```

`PluginSpec` 由 `adapters/base/_plugin_loader.py` 按现有白名单顺序加载，逐项报告格式与 `_PluginReport` 保持一致，`register_routers` 的失败不中断、全失败抛 `PluginsMissingError` 语义完整保留。

各 Adapter 的 `_router_bridge.py` 负责编译：

- Telegram：`CommandSpec` → `aiogram.filters.Command(name, *aliases)` + `Router.message(...)`；`scopes` → 自定义 Filter。每次启动构建全新 Router，消除 `router._parent_router = None`。
- OneBot：`CommandSpec` → 前缀匹配表；`scopes` → 事件过滤谓词。

兼容策略：加载器同时认旧契约（模块级 `router` 属性），命中时记 `WARNING` 并按 Telegram 专属插件处理，只挂到 Telegram Adapter。这样现有插件可以逐个迁移，不必一次推翻，中间态可运行。

### 5.5 多步会话状态

`/change` 与 `/system` 依赖 aiogram FSM（`_identity.py:25-35` 的 `StatesGroup`）。跨平台方案：

- 状态定义改为平台无关的步骤枚举，收进 `core/domain/_steps.py`，如 `IdentityStep.ASK_NAME` / `ASK_DESC`。
- 存储走 `ConversationStateStore` 端口。
- Telegram 侧提供两种实现：`_fsm_bridge.py` 桥接 aiogram FSM（保留现有内存态行为，改动最小），或直接用 DB 实现（重启不丢状态）。
- OneBot 侧只有 DB 实现。

建议**两端统一用 DB 实现**，理由：GUI 面板后续要展示"哪些用户卡在第几步"，DB 态可直接查询；且 aiogram FSM 默认内存存储，重启即丢，现有行为本身就是缺陷。这是决策点 D5。

### 5.6 数据模型

SQLite，WAL 模式，外键开启。八张表：

```sql
-- 会话主体
principal(
    key            TEXT PRIMARY KEY,     -- telegram:group:-100123:456
    platform       TEXT NOT NULL,
    scope          TEXT NOT NULL,
    chat_id        TEXT NOT NULL,
    user_id        TEXT NOT NULL,
    display_name   TEXT NOT NULL DEFAULT '',
    created_at     REAL NOT NULL,
    last_active_at REAL NOT NULL DEFAULT 0,
    is_active      INTEGER NOT NULL DEFAULT 0
)
INDEX idx_principal_platform ON principal(platform)
INDEX idx_principal_stale    ON principal(last_active_at, is_active)

-- 会话消息
session_message(
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    principal   TEXT NOT NULL REFERENCES principal(key) ON DELETE CASCADE,
    seq         INTEGER NOT NULL,        -- 会话内序号，保证顺序
    role        TEXT NOT NULL,           -- system / user / assistant
    content     TEXT NOT NULL,
    reasoning   TEXT NOT NULL DEFAULT '',
    created_at  REAL NOT NULL
)
UNIQUE idx_message_seq ON session_message(principal, seq)

-- 任务
task(
    id           TEXT PRIMARY KEY,       -- uuid4
    principal    TEXT NOT NULL REFERENCES principal(key) ON DELETE CASCADE,
    kind         TEXT NOT NULL,
    priority     INTEGER NOT NULL,
    sequence     INTEGER NOT NULL,
    status       TEXT NOT NULL,          -- pending/running/succeeded/failed/cancelled
    payload      TEXT NOT NULL DEFAULT '{}',   -- JSON
    source_ref   TEXT,                   -- JSON: MessageRefDTO
    status_ref   TEXT,                   -- JSON: MessageRefDTO
    dedupe_key   TEXT NOT NULL DEFAULT '',
    error        TEXT NOT NULL DEFAULT '',
    created_at   REAL NOT NULL,
    started_at   REAL,
    finished_at  REAL
)
INDEX idx_task_pending  ON task(principal, status, priority, sequence)
INDEX idx_task_unfinish ON task(status)
UNIQUE idx_task_dedupe  ON task(dedupe_key) WHERE status IN ('pending','running')

-- 媒体索引（本轮建表不接业务）
media_asset(
    platform    TEXT NOT NULL,
    chat_id     TEXT NOT NULL,
    user_id     TEXT NOT NULL,
    message_id  TEXT NOT NULL,
    kind        TEXT NOT NULL,
    slot        INTEGER NOT NULL DEFAULT 0,
    local_path  TEXT NOT NULL,
    size_bytes  INTEGER NOT NULL DEFAULT 0,
    meta        TEXT NOT NULL DEFAULT '{}',   -- JSON
    created_at  REAL NOT NULL,
    PRIMARY KEY (platform, chat_id, user_id, message_id, kind, slot)
)
INDEX idx_media_principal ON media_asset(platform, chat_id, user_id)

-- 黑名单
blacklist(
    principal  TEXT PRIMARY KEY,
    reason     TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL
)

-- 多步会话状态
conversation_state(
    principal  TEXT PRIMARY KEY,
    step       TEXT NOT NULL,
    data       TEXT NOT NULL DEFAULT '{}',   -- JSON
    updated_at REAL NOT NULL
)

-- 菜单应答映射（QQ 降级交互用）
menu_action(
    platform    TEXT NOT NULL,
    chat_id     TEXT NOT NULL,
    message_id  TEXT NOT NULL,
    token       TEXT NOT NULL,          -- 用户回复的序号或关键词
    action_id   TEXT NOT NULL,
    payload     TEXT NOT NULL DEFAULT '{}',
    created_at  REAL NOT NULL,
    expires_at  REAL NOT NULL,          -- 过期自动失效，防旧菜单被误触发
    PRIMARY KEY (platform, chat_id, message_id, token)
)
INDEX idx_menu_expire ON menu_action(expires_at)

-- 迁移版本（升级与回滚保护的依据，见 5.8.2）
schema_version(
    version     INTEGER PRIMARY KEY,
    applied_at  REAL NOT NULL,
    checksum    TEXT NOT NULL          -- 脚本内容哈希，防同版本号脚本被改动
)
```

`task.dedupe_key` 的部分唯一索引解决重复入队：用户连发三条同样消息，只有第一条建任务，后两条拿到既有 `TaskDTO`。

对话记录的 txt/md/png **不入库**，仍落盘，但改由 `RecordRepository` 统管路径与生命周期。理由：这些是给人看的导出物和大二进制，入库会让 DB 体积失控且没有查询需求。DB 只存索引与元数据。这是决策点 D4。

数据库文件放 `data/bot.db`。这不是随手选的：`launcher.py:50` 的 `_PRESERVE_NAMES` 已含 `data`，放在这里就自动进入升级保留范围，用户升级后数据完整留存，启动器零改动（详见 5.8.1）。

迁移策略：

- 迁移运行器在 `InitializationManager` 中执行，位于 `init_project_files()` 之后、Adapter 启动之前：此时 `data/` 已建好，失败可直接走 `error_guard` 弹窗，不会拉起半个残废的 bot。
- `_0001_baseline.py` 建全部表。
- `_0002_legacy_import.py` 一次性导入旧数据：扫 `blacklist.txt` 建 principal + blacklist 行；扫 `records/temp/*.md` 与 `staged/*.txt` 反解出会话消息（格式固定为 `时间\n\n用户：...\n\nAI思考：...\n\nAI回复：...`，见 `_worker.py:75-80`）；旧 key 按 P0 节的映射规则转新 key。
- 每个脚本执行前查 `schema_version`、执行后写表，全程包在事务里；迁移幂等，重跑不产生重复行。
- 迁移前无条件备份 `data/bot.db` 到 `data/backups/`，保留最近 3 份，备份失败则中止迁移并按原版本启动。
- DB 的 schema 版本高于代码内置 `SUPPORTED_SCHEMA` 时拒绝启动并弹窗指向备份，防止版本回滚后读到不认识的结构（详见 5.8.2）。
- 旧文件迁移后**保留不删**，改名加 `.migrated` 后缀，留一个版本的回滚窗口。

### 5.7 引擎与生命周期

`bot/_service.py` 的线程 + 事件循环骨架保留，改动三处：

1. `BotService(bot, dispatcher)` → `AdapterRuntime(adapter: BaseAdapter, pipeline: EventPipeline)`，构造参数换成平台无关抽象。
2. `_retry_if_network_running` 里的 `isinstance(exc, TelegramNetworkError)` → `adapter.lifecycle.is_retryable(exc)`。tenacity 的重试参数（`_RECONNECT_TIMEOUT = 60`、`_MIN_RETRY_DELAY = 1`、`_MAX_RETRY_DELAY = 10`）原样保留。
3. `register_lifecycle(self._bot.session.close, ...)` → `register_lifecycle(adapter.lifecycle.close, ...)`。

多 Adapter 并存：`bot/_registry.py` 持有 `dict[str, AdapterRuntime]`，GUI 面板可独立启停单个平台。现有 `stop_service()` 的单实例语义改为按平台 key 操作。

数据库连接的线程模型：SQLite 连接不跨线程共享。`data/_sqlite/_connection.py` 维护 per-loop 连接，Adapter 各在自己的事件循环线程里跑，天然隔离。GUI 线程要查数据（面板展示队列）走 `asyncio.run_coroutine_threadsafe` 投递到对应 loop，或走独立的只读连接。这是 D2 的影响面。

### 5.8 版本更新与启动器

先说结论：**现有启动器机制基本不用改，数据层迁移能平滑接入**。逐项核对如下。

#### 5.8.1 现有机制为何刚好够用

`launcher.py:50` 的保留清单已含 `data`：

```python
_PRESERVE_NAMES = ("config.toml", "data", "logs", "runtime", "_update", "_internal")
```

而 `init_files.py:16-20` 的记录与黑名单目录都在 `ROOT_DIR / "data"` 下。**把 SQLite 放在 `data/bot.db`，它就自动落在升级保留范围内**，用户升级后数据完整留存，启动器一行代码都不用改。这是 D1 选 SQLite 的又一收益——MySQL 的连接信息得进 `config.toml`（也在保留清单里），但服务端要用户自己维护。

依赖自动补装也已就绪：`_deps_digest()`（`launcher.py:243`）对 `pyproject.toml` 的 `dependencies` 列表算摘要，与 `runtime/.installed` 比对，不一致就重走安装（`_installed_ok`、`_ensure_runtime`）。所以阶段 0 往 `dependencies` 加 `aiosqlite` 后：

- 老用户升级 → 摘要变化 → 启动器自动补装 aiosqlite → 无需用户操作。
- `_check_update` 里升级完成后本来就调 `_ensure_runtime(root)`（`launcher.py:499`），链路已通。

代码替换也没问题：`_apply_update`（`launcher.py:452-463`）对白名单外目录"先删后拷"，`src/` 整树替换，新增的 `core/` `data/` `services/` `adapters/` 会正常落地，被删掉的旧模块不会残留（这正是 alpha.2 修过的坑）。

#### 5.8.2 必须新增的三件事

启动器只管文件和依赖，**数据库 schema 迁移必须由主程序自己做**，且要处理三个新风险。

**① 迁移时机与幂等**

放在 `InitializationManager`（`bot/_managers/_initialization.py`）里，`init_project_files()` 之后、Adapter 启动之前。理由：此时 `data/` 目录已建好，且迁移失败能直接走 `error_guard` 弹窗，不会拉起半个残废的 bot。

迁移记录表：

```sql
schema_version(
    version     INTEGER PRIMARY KEY,
    applied_at  REAL NOT NULL,
    checksum    TEXT NOT NULL      -- 迁移脚本内容哈希，防同版本号脚本被改动
)
```

每个迁移脚本执行前查表、执行后写表，全程包在事务里。重跑不产生重复变更。

**② 迁移前自动备份**

一次性导入（`_0002_legacy_import`）要解析旧的 txt/md 文件，格式一旦对不上就可能写坏数据。迁移前无条件备份：

```
data/bot.db  →  data/backups/bot-20261001-153000.db
```

保留最近 3 份，超出删最旧（这是 agent 自产物、非用户数据，可直接删）。备份失败则中止迁移并按原版本启动，不冒险。

**③ schema 版本降级保护（最容易被忽略的风险）**

场景：用户升到 v1.1（schema v3），出问题想回滚到 v1.0（代码只认 schema v2）。此时 DB 是 v3、代码是 v2，直接跑会读到不认识的表结构，报错还很难懂。

处理方式：主程序启动时比对 `schema_version` 最大值与自己代码内置的 `SUPPORTED_SCHEMA`：

| 关系 | 行为 |
| :--- | :--- |
| DB < 代码 | 正常执行迁移 |
| DB == 代码 | 直接启动 |
| DB > 代码 | **拒绝启动**，弹窗提示"数据由更新版本创建，请升级回 vX.Y 或从 data/backups 恢复备份"，附最新备份路径 |

拒绝启动比静默跑坏数据安全得多。这条也顺带保护了"升级失败回滚"的场景。

#### 5.8.3 版本号与 CHANGELOG

`docs/release-workflow.md` 的既有流程不变：`pyproject.toml` 递增版本 → CHANGELOG 定稿 → 打 tag → 上传 Release。

需要补充的只有一点：**引入 schema 变更的版本属于 Breaking**。因为回滚会撞上 5.8.2 的降级保护，用户没法简单退回旧版。这类版本应在 CHANGELOG 的 `⚠️ Breaking Changes` 里写明"本版起数据落库，降级需从备份恢复"。

阶段划分建议按这个原则切：阶段 2（建表）和阶段 3+4（Principal + 会话入库）会产生 schema，尽量合到同一个发布版本里，避免用户连续两次遇到不可回滚升级。

#### 5.8.4 一个待你确认的命名风险

D5 已定"保留 `bot/` 不改名"，顺带说清缘由：`_PRESERVE_NAMES` 里的 `runtime` 是**发布包根目录**的嵌入式 Python 存放处（`runtime\python.exe`），与 `src/` 下的 Python 包不是一个东西。若把 `src/bot/` 改名为 `src/runtime/`，两个 `runtime` 同时存在，排查问题时极易看错。保留 `bot/` 零风险。

### 5.9 并发模型

先厘清三个不同层面的"并发"，它们的约束完全不同。

#### 5.9.1 用户级并发：已经支持，但有个隐藏阻塞点

现状其实**已经是并发的**：`_ai_chat.py:71` 为每个用户 `create_task(monitor_loop(user))`，`active_tasks` 集合持有这些任务，N 个用户的对话在同一事件循环里并发推进。`user_locks`（`state.py:11`）只锁单个用户内部，保证同一用户的任务串行（队列语义正确）。

真正的瓶颈是**事件循环里的同步 IO**。`_worker.py:80-84`：

```python
with open(rec_dir / f"staged/{user}.txt", "a", encoding="utf8") as f:
    f.write(wrt)
with open(rec_dir / f"temp/{user}.md", "a", encoding="utf8") as f:
    f.write(wrt)
```

同步 `open` + `write` 在协程里直接执行，磁盘慢时**整个事件循环被冻住**——所有用户的流式输出、TG 长轮询、GUI 信号全部停摆。同理 `_chat_context.py:73` 的系统提示词写文件。

对比之下 `_blacklist.py:50,75` 已经正确用了 `asyncio.to_thread`。改造原则：**所有落盘操作一律 `to_thread`**，这条在阶段 4 顺手做掉。

数据层改造后要注意别引入新的阻塞：aiosqlite 本身在后台线程跑 SQL，不阻塞循环；但 `_save_conversation_record` 这类"写 DB + 写文件"的组合，DB 部分交给 aiosqlite、文件部分交给 `to_thread`，两者不要串行等待。

#### 5.9.2 多平台 / 多 bot 并发：架构支持，不需要动实例锁

这是重构后**新增的能力**，也是 `bot/_registry.py` 的价值：

```
一个进程 · 一个 GUI
  ├─ AdapterRuntime("telegram")  → 独立线程 + 独立事件循环
  ├─ AdapterRuntime("onebot")    → 独立线程 + 独立事件循环
  └─ 共享：SQLite（WAL）· TaskScheduler · GUIBridge
```

- 单进程内跑 TG + QQ 两个平台，**不需要改互斥锁**，因为仍是一个进程。
- 同平台多 bot（两个不同 token 的 TG 机器人）也可行：配置改为 bot 列表，每个条目一个 `AdapterRuntime`，各自独立线程与 loop。
- SQLite 在单进程内多连接是安全的：WAL 模式允许多读并发，写操作由 aiosqlite 的后台线程串行化，不会撞锁。

配置结构相应扩展（`config.toml`）：

```toml
[[bots]]
platform = "telegram"
token = "..."
proxy = ""

[[bots]]
platform = "onebot"
ws_url = "ws://127.0.0.1:3001"
access_token = "..."
```

GUI 面板加平台维度：每个 bot 一行，独立显示运行状态、队列深度、启停按钮。`_apply_config` 的指纹比对（`_managers/__init__.py:162-172`）改为按 bot 条目分别算指纹，只重启参数变化的那个，其余不闪断。

#### 5.9.3 多进程 / 多 GUI：不建议，三条硬约束

如果你想的是"开好几个程序窗口各跑一个 bot"，这条路我不建议，硬约束有三个：

1. **Telegram 长轮询互斥**：同一个 bot token 只能有一个 `getUpdates` 消费者。两个进程用同 token 会互相抢 update，消息随机丢一半。这是 Telegram 服务端行为，绕不过去。
2. **SQLite 单写者**：WAL 只解决"多读并发"，写仍是全库单写者。多进程写同一个 db 文件会频繁 `database is locked`，需要重试与超时策略，复杂度陡增。
3. **配置文件单份**：`config.toml` 只有一份，两个进程的热重载会互相覆盖对方的写入。

要真做多进程，得改成每实例独立 DB 文件 + 独立配置目录 + 带实例后缀的互斥锁名（`Local\TelegramBot-Instance-{n}`），改动面很大而收益很小——**单进程多 Adapter 已经能覆盖"同时跑 TG 和 QQ"和"同时跑多个 TG bot"两个真实需求**。

`single_instance.py:16` 的固定锁名保留不动，它防的正是上面第 1、2 条。

#### 5.9.4 任务级并发：需要新增全局上限

引入 TaskScheduler 后要加一个现在没有的东西——**全局并发上限**。

现状每个用户一个 `monitor_loop`，用户数无上限，等于并发数无上限。单用户单 bot 时无所谓，但多平台多 bot 并存后，同时活跃的用户可能几十个，每个都持有一条 AI 流式 HTTP 连接，会撞上：

- AI 服务商的 QPS / 并发限制（返回 429）
- 本机文件描述符与内存（每个任务还带 playwright 截图）

设计：

```python
# src/services/tasks/_scheduler.py

_MAX_CONCURRENT_TASKS = 4      # 全局并发上限，可配置
_MAX_PER_PRINCIPAL = 1         # 单主体并发上限，维持现有队列语义
```

- 单主体仍是 1（同一用户的任务排队执行，与现有行为一致，也是 `user_locks` 的语义）。
- 全局用 `asyncio.Semaphore(_MAX_CONCURRENT_TASKS)` 卡总量，超出的任务留在 DB 里 `PENDING`，等有槽位再拉起。
- 多 Adapter 共享同一个 Semaphore 实例（装配期注入），这样 TG 和 QQ 的任务一起算总账，不会各跑 4 个变成 8 个。

`_MAX_CONCURRENT_TASKS` 的具体值建议做成配置项，默认 4，让你按 AI 服务商的实际额度调。

#### 5.9.5 并发相关的改造清单

| 项 | 位置 | 阶段 |
| :--- | :--- | :--- |
| 同步文件写入改 `to_thread` | `_worker.py:80-84`、`_chat_context.py:73` | 阶段 4 |
| 全局并发 Semaphore | `services/tasks/_scheduler.py` | 阶段 6 |
| 多 Adapter 注册表 | `bot/_registry.py` | 阶段 9 |
| 配置改 bot 列表 + 分条指纹 | `utils/config/`、`bot/_managers/__init__.py` | 阶段 9 |
| GUI 面板加平台维度 | `gui/` | 阶段 9 |
| OneBot Adapter | `adapters/onebot/` | 阶段 10 |

多平台并存排在阶段 9，是因为它依赖阶段 5（InteractionPort）和阶段 6（TaskScheduler）先把平台无关的地基打好。在那之前项目仍是单 TG bot，功能不受影响。

## 六、决策点

D1～D7 已按建议定案（用户 2026-10-01 确认"我听你的"）。D8、D9 为思考态相关定案，D10 待你确认。

| 编号 | 决策 | 定案 | 依据 |
| :--- | :--- | :--- | :--- |
| D1 | 数据库 | **SQLite + WAL**，Repository 接口留双实现口子 | MySQL 要求用户自备服务，与"下载 zip 即用 + 启动器自动升级"的发布模式冲突。接口抽象后可无痛加 MySQL 实现 |
| D2 | 异步驱动 | **aiosqlite** | 纯 Python 包，PyInstaller 无额外 hook；标准库 `sqlite3` + `to_thread` 在高频队列操作下线程抖动明显 |
| D3 | DTO 载体 | **dataclass(frozen=True, slots=True)** | 项目已在用 dataclass（`config.py:18`、`models.py`），零新增依赖；pydantic 需打包 hook 且冷启动变慢，本场景 DTO 结构简单不值得引入 |
| D4 | 对话记录存储 | **落盘**，Repository 统管路径与生命周期 | 记录是导出物与大二进制，入库使 DB 体积失控且无查询需求 |
| D5 | `bot/` 目录 | **保留 `bot/`，不改名** | 原建议改名 `runtime/`，但 `packaging/launcher.py:50` 的 `_PRESERVE_NAMES` 已含 `runtime`——那是发布包根目录的嵌入式 Python 存放处（`runtime\python.exe`，见 `docs/packaging.md:14`）。两处同名虽不产生文件冲突（一个在包根、一个在 `src/` 下），但排查问题时极易混淆，且改名还要动 `build.py:204`、`launcher.py:595`、`development.md:12` 三处硬编码。收益纯语义、代价是新增混淆源，不值得。若日后仍要改，用 `app/` 或 `bootstrap/` 避开 `runtime` |
| D6 | 多步状态存储 | **统一 DB 实现** | 桥接 aiogram FSM 改动最小，但保留"重启丢状态"既有缺陷且两端行为不一致；DB 实现让 GUI 面板可查询卡在第几步的用户 |
| D7 | 迁移激进程度 | **新旧并存，插件逐个迁** | 每阶段可独立运行与回滚，加载器兼容旧 `router` 契约；一次切换出问题定位面大 |
| D8 | 思考过程展示 | **整体砍除**，两端静默等待后输出最终回答，draft 机制退役 | 用户 2026-10-01 决定。砍除后两端行为差异收敛为占位能否原地刷新中间态，由 `EDIT_MESSAGE` 单个能力位覆盖，不再需要 draft、节流、分档等机制。占位与终态流程见 D15 与 4.6.3，删除清单见 4.6.4 |
| D9 | 传输流式（SSE） | **保留**，`stream_chat` 两端共用不改 | 与界面无关，是程序与 AI 服务商之间的 HTTP 行为。保留理由三条：`read` 超时语义（流式下不会误杀长回答）、取消能力依赖 `async for` 提前 break、记录仍需 `reasoning_content`。详见 4.6.2 |
| D10 | `reasoning_content` 去向 | **砍展示、留记录** | 用户 2026-10-02 定案：思考过程随消息持久化（`MessageDTO` 加 `reasoning` 字段、`session_message` 表加列），`/history` 导出内容不变，另提供按消息查看思考过程的命令；`history_for_model` 转换时丢弃，不喂模型 |
| D11 | 会话级 md_ready | **删除**，渲染触发下沉消息级 | 产物按消息 ref 建索引，命中直返、未中现渲，会话布尔无消费者 |
| D12 | `TaskDTO.status_ref` | **保留** | 跨重启持久，恢复时清理僵尸占位的唯一把手，TG 降级重发也需改写 |
| D13 | DTO 命名 | **一律 DTO 后缀** | `core/dto` 类型统一后缀，不设裸名例外 |
| D14 | 发送面 | **`send_message` 单入口** | `OutboundContentDTO` 按 kind 分派文字与媒体，reply 与 mention 为 `send_message` 正交标志，不设独立回复或投递方法；OneBot v11 的 at 段与 reply 段独立，旧前提"QQ 提及只能靠引用"作废 |
| D15 | 状态消息流程 | **占位两端均发并引用原消息（不 at）；终态删占位后新发：引用加 at 加完整键盘** | 用户 2026-10-03 约定。待定：终态 reply 指向原消息还是刚删的占位——指向已删消息两端表现待实测，定前按原消息实现 |

## 七、分步实施路线

每阶段结束时代码可运行、可验证、可回滚。

**阶段 0 · 护栏**

引入 import-linter，契约配置放项目根 `.importlinter`（INI），按阶段渐进启用：阶段 0 只上 "core zero external dependencies" 与 "data and adapters isolation" 两条（空壳包天然通过、零误报），后续每阶段随对应层落地再追加。未迁移代码不写死契约，也就无需豁免清单。装 aiosqlite。

验证：项目根跑 lint-imports，输出 2 kept、0 broken。三个实操要点见操作手册 0.4：include_external_packages 开关不能少（forbidden 里有 aiogram 时缺它直接报错退出）；INI 必须存为 UTF-8 无 BOM（BOM 让 configparser 报 no section headers）；契约名用英文可彻底摆脱对 PYTHONUTF8 的依赖。

**阶段 1 · core 层落地**

建 `core/dto/`、`core/domain/`、`core/ports/` 全量定义，另在 `exceptions/` 下新增 `_domain.py` 领域异常族（继承现有 `AIError`，复用 `BotError` 基类，不建第二套异常树）。此阶段不接任何业务，纯类型与抽象。

验证：`core/` 不出现 aiogram / PySide6 / aiosqlite 导入；mypy 或 pyright 严格模式过。

**阶段 2 · data 层 + 迁移**

实现全部 SQLite Repository、UnitOfWork、迁移运行器、`_0001_baseline`（含 `schema_version` 表）。写一次性脚本验证 CRUD 与事务回滚。同步实现 5.8.2 的三件保护：迁移前自动备份到 `data/backups/`、保留最近 3 份、schema 版本高于代码时拒绝启动并弹窗。迁移运行器接进 `InitializationManager`，位于 `init_project_files()` 之后。

验证：单测覆盖状态机非法转移拒绝、dedupe 部分唯一索引、级联删除；迁移重跑不产生重复行；手工把 `schema_version` 改高一位确认能拦住启动；备份目录确实产出且只留 3 份。

**阶段 3 · Principal 切换（P0 优先）**

引入 `PrincipalDTO`，替换 `get_name()` 全部调用点。写 `_0002_legacy_import`，把黑名单 txt、会话记录文件导入新表。

验证：旧 key → 新 key 映射逐条比对；导入幂等（跑两次结果一致）；旧文件已加 `.migrated` 后缀且未删除。

**阶段 4 · 会话数据层收口（P0）**

删掉 `core/__init__.py` 导出的 `user_sessions`，实现 `SessionService`。逐个改造 `_identity.py:89,124`、`_worker.py:229`、`_history.py:57`、`_ai_chat.py`、`_monitor.py` 的裸访问。

同步落盘一并改异步：`_worker.py:80-84` 的两个 `open` + `write` 与 `_chat_context.py:73` 的系统提示词写文件都在协程里同步执行，磁盘慢时会冻住整个事件循环（所有用户的流式输出、长轮询、GUI 信号全停），一律改 `asyncio.to_thread`。`_blacklist.py:50,75` 已是正确写法，可作参照。

验证：全项目 grep 不到 `user_sessions`；`session_guard` 装饰器退役，改由 `SessionPreload` 中间件承担；协程内不再有裸 `open`（`to_thread` 包裹除外）。

**阶段 5 · InteractionPort + Telegram Adapter**

建 `adapters/base/` 与 `adapters/telegram/`。把 `TelegramTaskItem` 的四个 `safe_*` 方法拆进 `_interaction.py`（`safe_draft` 直接删除，见 4.6.4），新增 `send_status` 落地占位引用与终态删重发流程，`send_message` 并入 mention 与 reply 正交标志，平台异常字符串匹配下沉翻译成领域异常。`HandlerContext` 上线，handler 签名从 `(message, bot, state)` 改为 `(event, ctx)`。

验证：TG 端全功能回归——私聊对话、群聊触发词、占位消息编辑为最终回答、长消息分段、频控退避、原消息删除中断。确认 draft 相关代码已清除且不影响回答输出。

**阶段 6 · 任务队列重写**

实现 `TaskService` / `TaskScheduler` / `_HotQueue` / `_registry`。`/history` `/clear` `/md` 从 Router 直执行改为 Task 派发。删掉 `TaskQueue` 与 `monitor_loop`。

一并加入 5.9.4 的两级并发闸：单主体上限 1（维持现有队列语义）、全局上限 `_MAX_CONCURRENT_TASKS`（默认 4，做成配置项）。现状每用户一个 `monitor_loop` 且用户数无上限，等于并发数无上限；多平台并存后会同时撞上 AI 服务商 QPS 与本机资源（每个任务还带 playwright 截图）。

验证：插队（`bump_to_front` 后确实先执行）、清队（`clear` 后 PENDING 全 CANCELLED 且 RUNNING 收到中断）、重启恢复（杀进程后 `recover()` 重建队列）、dedupe（连发三条只建一个任务）、并发闸（把上限调成 1，开五个用户同时提问，确认同一时刻只有一个任务在 RUNNING、其余留在 PENDING）。

**阶段 7 · 插件契约迁移**

`PluginSpec` 上线，加载器兼容旧 `router` 契约。`welcome` / `help` / `ai` 三个插件逐个迁移。消除 `router._parent_router = None`。

验证：白名单顺序仍生效（AI 必须最后）；逐项报告格式不变；故意让一个插件加载失败，其余照常工作。

**阶段 8 · middleware 跨平台化**

`AccessLogMiddleware` 移到 `adapters/base/`，只吃 `InboundEventDTO`。`utils/middleware.py` 删除。日志加平台前缀。

验证：TG 端日志格式与改造前逐字段一致（除新增平台前缀）；`utils/` 下 grep 不到 aiogram。

**阶段 9 · 引擎抽象与多平台并存**

`BotService` → `AdapterRuntime`，`ConnectionLifecycle` 上线。`bot/_registry.py` 持有 `dict[str, AdapterRuntime]`，支持多 Adapter 并存与独立启停。配置结构从单 token 改为 `[[bots]]` 列表（platform + 各自凭据），`_apply_config` 的指纹比对（`_managers/__init__.py:162-172`）改为按 bot 条目分别计算，只重启参数变化的那个，其余不闪断。GUI 面板加平台维度：每个 bot 一行，独立显示状态、队列深度、启停按钮。

注意：本阶段仍不接 QQ，只是把装配层改成"能容纳多个 Adapter"。实例锁（`single_instance.py:16`）保持不动——多 Adapter 跑在同一进程内，仍是单实例。

验证：拔网重连行为与改造前一致（tenacity 参数未变）；关闭流程 `shutdown_completed_event` 时序不变；配两个 TG token 时能独立启停互不干扰；只改其中一个 token 时另一个不重启。

**阶段 10 · OneBot Adapter**

实现 `_api.py`（HTTP + 正向 WS）、`_normalize.py`、`_interaction.py`（含占位可操作提示降级、引用段与 at 段拼装、`send_status` 同样发占位、终态删占位重发）、`_state.py`、`_engine.py`。建 `menu_action` 映射逻辑。

验证：QQ 端私聊与群聊对话跑通；占位键盘降级为可操作提示后，引用回复序号能正确还原 `CallbackEventDTO`；提及走 at 段；等待期间占位保持原文不动、终态删占位后新发；日志前缀显示 `[QQ]`。

**阶段 11 · 媒体索引接线**

`MediaIndexService` 从骨架转为可用，`/md` 与截图产物走 `register`，按四元组 `locate`。

验证：同一 principal 多张图按 slot 区分；`delete_by_principal` 在会话清理时同步清索引，无孤儿行。

阶段 3 与 4 是 P0，建议优先且合并为一个发布版本，因为 `get_name` 与 `user_sessions` 的调用点高度重叠，分两次改会重复触碰同一批文件。

### 7.1 起步指引

第一次动手做这三件事，顺序固定，做完即有一个能跑的地基，不碰任何现有业务逻辑：

1. **阶段 0**：`pyproject.toml` 加 `aiosqlite`，装 import-linter，在项目根 `.importlinter` 写两条契约（core zero external deps、data and adapters isolation，后续阶段随层落地再追加，不搞全量豁免）。契约不进 `pyproject.toml`，开发工具配置独立成文件。此阶段不改一行业务代码。
2. **阶段 1**：建 `core/dto/`、`core/domain/`、`core/ports/`，另在 `exceptions/` 下新增 `_domain.py`（继承现有 `AIError`，复用 `BotError`，不建第二套异常树）。全部是类型与抽象基类，无实现、无第三方导入。写完用 pyright 严格模式过一遍。
3. **阶段 2**：建 `data/_sqlite/`，实现各 Repository 与 `_0001_baseline` 建表。写一次性脚本验证 CRUD、事务回滚、状态机非法转移拒绝。

这三步的共同点是**只加新文件、不改旧文件**，所以做完项目仍能正常启动运行，风险为零。真正的"破坏性"改动从阶段 3 才开始。

阶段 3 起才动现有代码，且每阶段结束都要能启动、能对话。第一个要碰的旧文件是 `plugins/AI/utils.py` 的 `get_name`——它调用点最多（`_auth.py` `_history.py` `_identity.py` `_ai_chat.py` `_chat_context.py` 共 8 处），是后续所有改造的公共前置，先换掉它，后面才顺。

### 7.2 阶段与优先级对照

| 阶段 | 内容 | 优先级 | 改旧文件 | 产生 schema | 能否独立发布 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | 护栏 | P0 前置 | 否 | — | 是 |
| 1 | core 层 | P0 前置 | 否 | — | 是 |
| 2 | data 层 + 迁移 + 备份与降级保护 | P0 前置 | 否 | ✓ | 是 |
| 3+4 | Principal + 会话收口 + 落盘改异步 | **P0** | 是 | ✓ | 是（与 2 合并一版） |
| 5 | InteractionPort + TG Adapter | P1 | 是 | — | 是 |
| 6 | 任务队列重写 + 并发闸 | P1 | 是 | — | 是 |
| 7 | 插件契约 | P1 | 是 | — | 是 |
| 8 | middleware 跨平台 | P1 | 是 | — | 是 |
| 9 | 引擎抽象 + 多平台并存 | P2 | 是 | — | 是 |
| 10 | OneBot Adapter | P2 | 否（新增） | — | 是 |
| 11 | 媒体索引接线 | P2 | 是 | — | 是 |

"能否独立发布"全为是，意味着任一阶段做完都可以停下、打 tag、发版，不必一口气做到底。这是 D7"新旧并存"的直接收益。

但"产生 schema"那一列有个例外约束：schema 一旦推进就**不可降级**（5.8.2 的降级保护会拒绝启动旧版代码）。所以阶段 2 与 3+4 建议合并进同一个发布版本，避免用户连续两次遇到不可回滚升级；这两版也应在 CHANGELOG 的 `⚠️ Breaking Changes` 里写明降级需从 `data/backups` 恢复。其余阶段不改 schema，可自由发版。

## 附一：术语速查

面向非科班读者，用现有代码举例。

| 术语 | 一句话 | 你项目里的例子 |
| :--- | :--- | :--- |
| **DTO** | 只装数据、不带行为、跨层传递用的"纯数据盒子"，只读不可改 | 现有 `TaskItem`（`models.py:15`）就是半个 DTO，但它塞了 `Message` 活体对象，不纯。改造后 `TaskDTO` 只装 `task_id`、状态、时间等纯值 |
| **Repository（仓储）** | 专门管一类数据的增删改查，把"数据存哪、怎么存"藏起来，外面只调方法 | 现有 `_blacklist.py` 的 `get_black_list` / `save_black_list` 就是雏形，只是它存 txt。改造后 `BlacklistRepository` 存 SQLite，接口不变 |
| **Port（端口）** | 只定义"能做什么"的抽象方法，不含"怎么做"，具体实现由别处提供 | `InteractionPort.send_message(...)` 只声明"要能发一条消息"，TG 版用 aiogram 实现，QQ 版用 OneBot 实现，业务层调同一个方法 |
| **Adapter（适配器）** | 把某个具体平台的 API 翻译成 Port 要求的样子 | `TelegramAdapter` 把 aiogram 包成 Port；`OneBotAdapter` 把 OneBot 包成同一个 Port |
| **UnitOfWork（工作单元）** | 把多个数据库操作打包成一个事务，要么全成要么全滚 | 清理会话要同时删 4 张表，现有 `_monitor.py:119` 的 unlink 三连没有事务，删一半失败就留孤儿文件。UnitOfWork 解决这个 |
| **WAL** | SQLite 的一种日志模式，让"读"和"写"不打架，读写可并发 | 默认模式下写库时读库会被阻塞；开 WAL 后 GUI 面板查队列和后台写任务能同时进行。一行 `PRAGMA journal_mode=WAL` 开启 |
| **落盘 / 入库** | 落盘=写成文件存硬盘；入库=写进数据库 | 对话记录（txt/md/png）是"落盘"；会话、任务、黑名单改造后是"入库" |
| **Principal（主体）** | 唯一标识"哪个平台的哪个会话里的哪个用户" | 现有 `get_name` 产出 `u_123`，缺平台维度。`PrincipalDTO` 补全为 `telegram:private:123:123`，QQ 用户就不会和 TG 用户撞号 |
| **能力协商** | 运行时先问"这平台支持 X 吗"，不支持就走降级 | `supports(EDIT_MESSAGE)` 在 QQ 返回 False，思考态就自动改走"撤回重发"而非"原地编辑" |
| **降级** | 高级能力不可用时，退而求其次用低级能力达到近似效果 | 占位内联键盘 QQ 不支持，降级成占位内可操作提示 + 引用回复序号 |

### aiosqlite 与标准库 sqlite3 的区别

两者最终都操作同一个 SQLite 文件，区别只在**会不会卡住你的异步循环**：

- 标准库 `sqlite3` 是同步的。在 `async` 函数里直接调 `conn.execute(...)`，这几毫秒内整个事件循环被冻住——所有用户的消息处理、TG 长轮询、GUI 信号全部停摆。要绕开就得 `asyncio.to_thread(...)` 把每次查询丢进线程池，高频操作下线程反复创建销毁，抖动明显。
- `aiosqlite` 本质是"标准库 sqlite3 + 一个专属后台线程 + async 封装"。你写 `await db.execute(...)`，它在后台线程跑真正的 SQL，跑完唤醒你的协程，事件循环全程不冻。API 和 sqlite3 几乎一样，学习成本极低。

一句话：**aiosqlite 让你的数据库操作不阻塞机器人**。这也是 D2 选它的原因。

## 附二：不在本轮范围

- Telegram 内联键盘的实际实现（只保证 `send_status` 的 spec 参数与降级通路可用）。
- MySQL Repository 实现（只保证接口可承载）。
- OneBot v11 之外的协议版本（NapCat / Lagrange 等实现差异在 `_api.py` 内部消化）。
- GUI 面板的队列可视化（`TaskService.snapshot` 已备好数据，界面后续做）。
- 上下文压缩（实现时再登记对应 `TaskKind` 值，本轮不占位）。
