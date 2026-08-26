# src/utils/config/models.py
"""
配置数据模型模块

负责：
- 定义配置值的精确类型别名
- 定义 UI 渲染所需的 Schema 结构
"""

from dataclasses import dataclass, field

# ==================== 1. 核心配置值类型 ====================
# 单个 TOML 配置值
ConfigValue = (
    str | int | float | bool | None | list["ConfigValue"] | dict[str, "ConfigValue"]
)

# ==================== 2. 运行时配置数据结构 ====================
# 一个标签页
TabData = dict[str, ConfigValue]

# 完整 TOML 配置文件结构
AppConfigData = dict[str, TabData]


# ==================== 3. UI Schema 结构契约 ====================
@dataclass
class FieldSchema:
    """单个配置项的 UI 属性"""

    key: str  # 对应 TOML 里的键名
    label: str  # 界面上显示的标题
    desc: str  # 鼠标悬停时的提示语
    default: ConfigValue  # 默认值


@dataclass
class TabSchema:
    """一个标签页的 UI 结构"""

    title: str  # Tab 标题
    fields: list[FieldSchema] = field(default_factory=list)


# 完整 UI 渲染结构树
AppSchema = list[TabSchema]
