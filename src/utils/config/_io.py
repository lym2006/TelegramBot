# src/utils/config/_io.py
"""
配置 I/O 模块（内部实现）

- 从磁盘安全地读取配置数据（保留注释元数据）
- 将内存中的配置数据增量写入磁盘（保留原有注释和格式）
"""

import shutil
from pathlib import Path

import tomlkit
from tomlkit import TOMLDocument
from tomlkit.items import Table

from exceptions import ConfigInputError, ConfigMissingError, ConfigOutputError

from .models import AppConfigData, TabData


class ConfigIO:
    """配置文件读写器"""

    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path

    # ==================== 1. 读取 ====================

    def load(self) -> AppConfigData:
        """读取当前 config.toml 数据"""
        if not self._config_path.exists():
            raise ConfigMissingError() from None

        try:
            raw_text = self._config_path.read_text(encoding="utf-8")
            # 使用 tomlkit 读取，返回带有注释元数据的对象
            return tomlkit.parse(raw_text)
        except Exception as e:
            raise ConfigInputError() from e

    # ==================== 2. 写入 ====================

    def save(self, config_data: AppConfigData) -> None:
        """将配置数据增量写入 config.toml"""
        try:
            # 1. 写入前自动备份旧文件
            if self._config_path.exists():
                backup_path = self._config_path.with_suffix(".toml.bak")
                shutil.copy2(self._config_path, backup_path)

            # 2. 读取原文件，获取带有注释元数据的 tomlkit 文档对象
            if self._config_path.exists():
                raw_text = self._config_path.read_text(encoding="utf-8")
                doc = tomlkit.parse(raw_text)
            else:
                doc = tomlkit.document()

            # 3. 增量合并（只修改值，不破坏原有结构）
            self._merge_dict(doc, config_data)

            # 4. 序列化并写入
            content = tomlkit.dumps(doc)
            self._config_path.write_text(content, encoding="utf-8")

        except Exception as e:
            raise ConfigOutputError() from e

    def _merge_dict(
        self,
        target: Table | TOMLDocument,
        source: AppConfigData | TabData,
    ) -> None:
        """递归地将 source 中的新值合并到 target 中"""
        for key, value in source.items():
            if isinstance(value, dict):
                # 如果是嵌套字典（Tab），递归处理
                if key not in target:
                    target.add(key, tomlkit.table())
                self._merge_dict(target[key], value)
            else:
                # 如果是具体的值，直接覆盖（原 key 上的注释会自动保留）
                if key in target:
                    target[key] = value
                else:
                    target.add(key, value)
