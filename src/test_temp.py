import sys
from PySide6.QtWidgets import QApplication

# ==================== 1. 强制软件渲染（排查显卡驱动白屏） ====================
import os

os.environ["QT_QUICK_BACKEND"] = "software"
os.environ["QT_OPENGL"] = "software"

# ==================== 2. 导入用户自己的 GUI ====================
# 注意：必须在 src 目录下运行（即 src/ 在 Python 路径中）
# 如果报错 ImportError，请检查当前工作目录是否正确
try:
    from gui import create_gui
except ImportError as e:
    print(f"❌ 导入失败！请确保在 src 目录下运行此脚本。")
    print(f"   当前工作目录: {os.getcwd()}")
    print(f"   错误信息: {e}")
    sys.exit(1)


# ==================== 3. 创建应用并显示窗口 ====================
def main():
    app = QApplication(sys.argv)

    # 调用用户自己的 create_gui() 创建窗口（不启动任何 Bot）
    window = create_gui()

    # 注册一个测试按钮回调，验证按钮能响应
    window.register_action("btn_start", lambda: print("✅ 按钮 start 被点击了！"))
    window.register_action("btn_stop", lambda: print("✅ 按钮 stop 被点击了！"))

    # 显示窗口
    window.show()

    print("✅ 窗口已显示。如果界面正常，说明 GUI 没问题，白屏是 Bot 业务逻辑导致的。")
    print("   如果还是白屏，说明问题出在 create_gui() 内部的样式表或布局。")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
