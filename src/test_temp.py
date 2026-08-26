# test_temp.py
from utils.config import load_config, set_config, get_attr, get_schema
import json

# ==================== 1. 测试配置读取 ====================
print("=" * 30, "测试配置读取", "=" * 30)
config = load_config()
set_config(config)

proxy = get_attr("global.proxy", str)
token = get_attr("global.telegram_token", str)

print(f"Proxy: {proxy}")
print(f"Token: {token}")


# ==================== 2. 测试 Schema 解析 ====================
print("\n" + "=" * 30, "测试 Schema 解析", "=" * 30)
try:
    schema = get_schema()

    # 1. 检查返回值是否为空
    if schema is None:
        print("❌ 错误：Schema 解析返回了 None")
    else:
        print("✅ Schema 成功解析！")

        # 2. 打印完整的 Schema 结构（方便肉眼检查）
        # 如果你的 AppSchema 是 dataclass 或普通字典，可以直接打印
        # 如果是复杂的 Pydantic 模型，可以用 model_dump() 或 __dict__
        print("\n👇 完整 Schema 结构：")
        try:
            # 尝试以 JSON 格式美化打印，方便阅读
            print(json.dumps(schema, indent=2, ensure_ascii=False, default=str))
        except Exception:
            print(schema)

except Exception as e:
    print(f"❌ Schema 解析失败: {e}")
    import traceback

    traceback.print_exc()
