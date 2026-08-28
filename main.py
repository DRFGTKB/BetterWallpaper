"""
BetterWallpaper 主入口
- 把 src 目录加入模块路径
- 导入 filemanage（文件管理）和 UI（界面注册）
- 启动 nicegui
"""
import sys
from pathlib import Path

from nicegui import ui, app

# 让 src/ 下的模块可以被导入
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))

import filemanage  # noqa: E402  文件管理（索引/入库/出库）
import UI  # noqa: E402          界面（注册 / 和 /library 页面）

# 应用配置
app.add_static_files('/static', 'static')           # 壁纸库目录挂载
app.native.window_args['resizable'] = False         # 关闭窗口调整

if __name__ in {'__main__', '__mp_main__'}:          # reload 子进程是 __mp_main__，必须放行
    ui.run(native=True, reload=True, window_size=(1024, 576))
