# src/utils/config/__init__.py
"""
配置系统门面

- 配置生命周期控制（检查与初始化）
- 配置数据加载与保存
- UI Schema 获取
- 安全取值器
"""

from typing import Any, TypeVar, cast, get_origin

from exceptions import (
    ConfigAttrError,
    ConfigMissingError,
    ConfigTemplateMissingError,
)

from .._root_dir import ROOT_DIR
from ..init_files import ensure_file_exists
from ._io import ConfigIO
from ._parser import ConfigParser
from .models import AppConfigData, AppSchema

# ==================== 内部常量与单例初始化 ====================

# 全局配置单例
_CONFIG: AppConfigData | None = None

# 配置文件路径常量
_CONFIG_PATH = ROOT_DIR / "config.toml"
_EXAMPLE_PATH = ROOT_DIR / "config.example.toml"

# 底层组件实例化
_IO = ConfigIO(_CONFIG_PATH)
_PARSER = ConfigParser(_EXAMPLE_PATH)

# 泛型类型变量，用于 get_attr() 函数的类型推导
T = TypeVar("T")

__all__ = [
    # 核心生命周期控制
    "ensure_config",
    "set_config",
    # 数据读写与 UI 渲染
    "get_attr",
    "get_schema",
    "load_config",
    "save_config",
]

# ==================== 1. 启动阶段 ====================


def ensure_config() -> None:
    """检查 config.toml 是否存在，不存在则从 example 复制并抛出异常"""
    if _CONFIG_PATH.exists():
        return

    if _EXAMPLE_PATH.exists():
        ensure_file_exists("config.toml", "config.example.toml")
        raise ConfigMissingError() from None

    raise ConfigTemplateMissingError() from None


# ==================== 2. 数据读取与 UI 渲染 ====================


def get_schema() -> AppSchema:
    """获取 UI 渲染所需的强类型 Schema 结构树"""
    return _PARSER.parse()


def load_config() -> AppConfigData:
    """读取当前 config.toml 数据"""
    return _IO.load()


# ==================== 3. 数据保存 ====================


def save_config(config_data: AppConfigData) -> None:
    """将 GUI 修改后的数据写回磁盘"""
    _IO.save(config_data)


# ==================== 4. 极简安全取值器 ====================


def get_attr(key_path: str, expected_type: type[T]) -> T:
    """
    极简安全取值器

    支持点号路径穿透，并自动进行类型守卫
    如 get_attr("global.proxy", str)
    """
    keys = key_path.split(".")
    value: Any = _CONFIG

    # 1. 路径穿透
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            raise ConfigAttrError(key_path, expected_type, value)

    # 2. 空值检查
    if value is None:
        raise ConfigAttrError(key_path, expected_type, None)
    # 3. 类型守卫
    # 兼容 TOML 将无小数点的浮点数解析为 int 的情况
    if isinstance(value, int) and expected_type is float:
        value = float(value)

    # 提取泛型原始类型（如 list[str] -> list）
    origin_type = get_origin(expected_type)
    if not isinstance(value, origin_type or expected_type):
        raise ConfigAttrError(key_path, expected_type, value)

    return cast(T, value)


# ==================== 5. 全局单例注入 ====================


def set_config(config_data: AppConfigData) -> None:
    """将加载好的配置注入到全局单例中，供全程序使用"""
    global _CONFIG
    _CONFIG = config_data
