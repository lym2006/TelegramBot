# src/utils/config/__init__.py
"""
配置系统门面模块

导出：
- 配置文件的检查与初始化
- UI Schema 获取
- 配置数据加载与保存
- 安全取值器
"""

from typing import Any, TypeVar

from .._root_dir import ROOT_DIR
from ..exception import (
    ConfigInputError,
    ConfigMissingError,
    ConfigOutputError,
    ConfigParseError,
)
from ..init_files import ensure_file_exists
from ..logger import get_logger
from ._io import ConfigIO
from ._parser import ConfigParser
from .models import AppConfigData, AppSchema

logger = get_logger("Bot.Config")

# ==================== 模块级常量与单例初始化 ====================
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
    "get_schema",
    "load_config",
    "save_config",
    "get_attr",
]


# ==================== 1. 启动阶段 ====================
def ensure_config() -> None:
    """检查 config.toml 是否存在，不存在则从 example 复制并抛出异常暂停启动"""
    if _CONFIG_PATH.exists():
        return

    if _EXAMPLE_PATH.exists():
        logger.info("💡 未找到 config.toml，正在从模板自动创建...")
        ensure_file_exists("config.toml", "config.example.toml")
        logger.info("✅ config.toml 创建成功")
    else:
        logger.error("❌ 错误: 找不到配置文件与模板文件")

    logger.warning("🛑 启动已暂停：请打开 GUI 配置面板，完善必要配置")
    raise ConfigMissingError("🚨 配置文件缺失，需用户手动完善") from None


# ==================== 2. 数据读取与 UI 渲染 ====================
def get_schema() -> AppSchema:
    """获取 UI 渲染所需的强类型 Schema 结构树"""
    try:
        return _PARSER.parse()
    except ConfigMissingError as e:
        logger.warning(e)
    except ConfigParseError as e:
        logger.error(e)
    return []


def load_config() -> AppConfigData:
    """读取当前 config.toml 数据"""
    try:
        return _IO.load()
    except ConfigMissingError as e:
        logger.warning(e)
    except ConfigInputError as e:
        logger.error(e)
    return {}


# ==================== 3. 数据保存 ====================
def save_config(config_data: AppConfigData) -> None:
    """将 GUI 修改后的数据写回磁盘"""
    try:
        _IO.save(config_data)
        logger.info("✅ 配置已成功保存！")
    except ConfigOutputError as e:
        logger.error(e)
        raise ConfigOutputError(e) from e


# ==================== 4. 极简安全取值器 ====================
def get_attr(
    key_path: str, expected_type: type[T], default: T | None = None
) -> T | None:
    """
    极简安全取值器

    支持点号路径穿透，并自动进行类型守卫
    如 get_attr("global.proxy", str, "default")
    """
    keys = key_path.split(".")
    value: Any = _CONFIG
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return default
    return value if isinstance(value, expected_type) else default


# ==================== 5. 全局单例注入 ====================
def set_config(config_data: AppConfigData) -> None:
    """将加载好的配置注入到全局单例中，供全程序使用"""
    global _CONFIG
    _CONFIG = config_data
