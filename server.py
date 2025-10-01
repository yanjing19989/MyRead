#!/usr/bin/env python3
"""
Browser History Browser - Python Backend Server
启动脚本
"""

import uvicorn
import sys
from pathlib import Path

# 添加后端路径到系统路径
backend_path = Path(__file__).parent / "app"
sys.path.insert(0, str(backend_path))

def main():
    """启动服务器"""
    # 检测是否为打包后的可执行文件
    is_packaged = getattr(sys, 'frozen', False)
    
    print("🚀 启动 Browser History Browser 服务器...")
    print("📍 前端地址: http://127.0.0.1:8000")
    print("📍 API文档: http://127.0.0.1:8000/docs")
    print("⏹️  按 Ctrl+C 停止服务器")
    
    if is_packaged:
        print("📦 运行模式: 生产环境 (打包版本)")
    else:
        print("🔧 运行模式: 开发环境 (自动重载)")
    
    try:
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=not is_packaged,  # 仅在非打包环境下启用自动重载
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
