import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # type: ignore # Python < 3.11
    except ImportError:
        print("❌ 错误: 缺少 TOML 库。请运行: pip install tomli")
        sys.exit(1)

def get_project_root():
    return Path(__file__).resolve().parent.parent

def load_config(): 
    root_dir=get_project_root()
    config_path=root_dir/"config.toml"

    if not config_path.exists():
        print(f"❌ 错误: 找不到配置文件 '{config_path}'")
        print("💡 请在项目根目录下创建 config.toml")
        sys.exit(1)

    try:
        with open(config_path,"rb") as f:
            config=tomllib.load(f)
        return config,root_dir
    except Exception as e:
        print(f"❌ 错误: 解析 config.toml 失败: {e}")
        sys.exit(1)


CONFIG,ROOT_DIR=load_config()
proxy=CONFIG['network']['proxy']
key=CONFIG['api_keys']['siliconflow_key']
token=CONFIG['api_keys']['telegram_token']