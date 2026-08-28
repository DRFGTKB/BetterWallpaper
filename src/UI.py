"""
UI 模块：注册所有页面（主页 + 壁纸库）
由 main.py 导入并启动，本文件不调用 ui.run。
"""
from pathlib import Path

from nicegui import ui
from nicegui.events import GenericEventArguments

import filemanage as fm

# 全局状态：当前选中项在媒体列表中的下标（跨页面共享）
current = [0]


# ═══════════ 主页：全屏展示 + 滚轮切换（双缓冲淡入淡出，无黑屏）═══════════
@ui.page('/')
def index():
    library = fm.scan_all()
    if not library:
        ui.label('壁纸库为空，去 /library 上传').classes('text-white')
        return
    ui.query('body').classes('bg-black overflow-hidden')   # 黑底 + 禁滚动（防scale溢出出滚动条）
    ui.query('html').classes('overflow-hidden')
    idx = [current[0] % len(library)]
    pending = [0]                            # 滚轮累计值（防抖）
    active = [0]                             # 0=A层显示, 1=B层显示
    switching = [False]                      # 切换进行中，防连发

    FG_CLS = ('w-1/2 h-auto rounded-2xl shadow-xl '
              'hover:-translate-y-3 hover:scale-[1.03] hover:shadow-2xl '
              'transition-all duration-300 ease-out cursor-pointer')
    BG_CLS = 'w-full h-full object-cover blur-lg scale-110 pointer-events-none'

    # 背景层 × 2（交叉淡入淡出）
    with ui.element('div').classes('absolute inset-0'):
        bg_a = ui.element('div').classes(
            'absolute inset-0 transition-opacity duration-300')
        with bg_a:
            bg_a_img = ui.image('').props('fit="cover"').classes(BG_CLS)
            bg_a_vid = ui.video('', controls=False, autoplay=True, muted=True, loop=True).classes(BG_CLS)
            bg_a_vid.set_visibility(False)
        bg_b = ui.element('div').classes(
            'absolute inset-0 transition-opacity duration-300 opacity-0 pointer-events-none')
        with bg_b:
            bg_b_img = ui.image('').props('fit="cover"').classes(BG_CLS)
            bg_b_vid = ui.video('', controls=False, autoplay=True, muted=True, loop=True).classes(BG_CLS)
            bg_b_vid.set_visibility(False)

    # 前景层 × 2（交叉淡入淡出）
    with ui.element('div').classes('absolute inset-0') as stage:
        fg_a = ui.element('div').classes(
            'absolute inset-0 flex items-center justify-center transition-opacity duration-300')
        with fg_a:
            fg_a_img = ui.image('').classes(FG_CLS)
            fg_a_vid = ui.video('', controls=True, autoplay=True, muted=True, loop=True).classes(FG_CLS)
            fg_a_vid.set_visibility(False)
        fg_b = ui.element('div').classes(
            'absolute inset-0 flex items-center justify-center transition-opacity duration-300 opacity-0 pointer-events-none')
        with fg_b:
            fg_b_img = ui.image('').classes(FG_CLS)
            fg_b_vid = ui.video('', controls=True, autoplay=True, muted=True, loop=True).classes(FG_CLS)
            fg_b_vid.set_visibility(False)

    info = ui.label('').classes(
        'fixed bottom-6 left-1/2 -translate-x-1/2 '
        'text-white/80 text-sm bg-black/30 px-3 py-1 rounded-full')

    def set_media(img_el, vid_el, item) -> None:
        """把 item 装进某层的图/视频元素（按类型切换显示）"""
        url = fm.to_url(item)
        if fm.is_video(item):
            img_el.set_visibility(False)
            vid_el.set_source(url)
            vid_el.set_visibility(True)
        else:
            vid_el.set_visibility(False)
            img_el.set_source(url)
            img_el.set_visibility(True)

    def switch_to(new_idx: int) -> None:
        if switching[0]:
            return
        switching[0] = True
        idx[0] = new_idx % len(library)
        item = library[idx[0]]
        target = 1 - active[0]
        # 新内容装进隐藏层（背景+前景）
        if target == 0:
            set_media(bg_a_img, bg_a_vid, item)
            set_media(fg_a_img, fg_a_vid, item)
            fg_el = fg_a_vid if fm.is_video(item) else fg_a_img
        else:
            set_media(bg_b_img, bg_b_vid, item)
            set_media(fg_b_img, fg_b_vid, item)
            fg_el = fg_b_vid if fm.is_video(item) else fg_b_img
        # 就绪后淡入：图片固定短延迟（邻居已预载，缓存命中几乎瞬时）；
        # 视频等首帧 loadeddata，1.5 秒兜底防卡死
        if fm.is_video(item):
            fg_el.on('loadeddata', fade_in)
            ui.timer(1.5, fade_in, once=True)
        else:
            ui.timer(0.08, fade_in, once=True)

    def fade_in() -> None:
        if not switching[0]:
            return
        switching[0] = False
        target = 1 - active[0]
        active[0] = target
        for old, new in ((bg_a, bg_b), (fg_a, fg_b)):
            (old if target == 1 else new).classes(
                add='opacity-0 pointer-events-none')      # 旧层：淡出 + 不再拦鼠标
            (new if target == 1 else old).classes(
                remove='opacity-0 pointer-events-none')   # 新层：淡入 + 恢复交互
        current[0] = idx[0]
        item = library[idx[0]]
        info.set_text(
            f'{idx[0] + 1} / {len(library)}   {item.name}   '
            f'{"🎬视频" if fm.is_video(item) else "🖼图片"}')
        preload_neighbors()

    def preload_neighbors() -> None:
        """预加载相邻图片到浏览器缓存，下一次切换更快"""
        n = len(library)
        for off in (-1, 1):
            neighbor = library[(idx[0] + off) % n]
            if not fm.is_video(neighbor):
                ui.run_javascript(f'new Image().src = "{fm.to_url(neighbor)}";')

    def on_wheel(e: GenericEventArguments) -> None:
        pending[0] += e.args.get('deltaY', 0)
        if abs(pending[0]) < 100:
            return
        step = 1 if pending[0] > 0 else -1
        pending[0] = 0
        switch_to((idx[0] + step) % len(library))

    # 初始显示（A 层）
    set_media(bg_a_img, bg_a_vid, library[idx[0]])
    set_media(fg_a_img, fg_a_vid, library[idx[0]])
    current[0] = idx[0]
    info.set_text(f'1 / {len(library)}   {library[idx[0]].name}   '
                  f'{"🎬视频" if fm.is_video(library[idx[0]]) else "🖼图片"}')
    preload_neighbors()

    stage.on('wheel', on_wheel, throttle=0.05)       # 滚轮事件从媒体冒泡到舞台


# ═══════════ 壁纸库：网格 + 点选 + 上传入库 + 删除 ═══════════
def choose(p: Path) -> None:
    current[0] = fm.scan_all().index(p)
    ui.navigate.to('/')


@ui.refreshable
def wallpaper_grid() -> None:
    library = fm.scan_all()
    if not library:
        ui.label('壁纸库为空，用下面的上传按钮入库').classes('text-gray-400')
        return
    with ui.grid(columns=4).classes('gap-4'):
        for item in library:
            with ui.card().classes(
                    'cursor-pointer hover:-translate-y-1 hover:shadow-2xl '
                    'transition-all duration-300') as card:
                if fm.is_video(item):
                    ui.label('🎬').classes(
                        'w-full h-40 flex items-center justify-center text-5xl '
                        'bg-gray-800 rounded-t-2xl')
                else:
                    ui.image(fm.to_url(item)).classes(
                        'w-full h-40 object-cover rounded-t-2xl')
                ui.label(f'{item.name} · {item.stat().st_size // 1024 // 1024} MB').classes(
                    'text-xs text-gray-500 p-2')
            card.on('click', lambda item=item: choose(item))       # 闭包捕获
            with card:
                ui.button('✕ 删除', color='red', on_click=lambda item=item: confirm_delete(item))


def confirm_delete(item: Path) -> None:
    """删除确认对话框"""
    def do_delete() -> None:
        try:
            fm.file_delet(item)
            wallpaper_grid.refresh()
            ui.notify(f'已删除 {item.name}', type='positive')
        except ValueError as err:
            ui.notify(str(err), type='negative')
        dialog.close()

    with ui.dialog() as dialog, ui.card():
        ui.label(f'确定删除 {item.name} ?')
        with ui.row():
            ui.button('删除', color='red', on_click=do_delete)
            ui.button('取消', on_click=dialog.close)
    dialog.open()


@ui.page('/library')
def library():
    ui.query('body').classes('bg-gray-900')

    def on_upload(e) -> None:
        ext = Path(e.name).suffix.lower()
        if ext not in fm.ALL_EXTS:
            ui.notify(f'不支持的格式: {ext}', type='warning')
            return
        filename = fm.next_id(ext)
        with open(fm.WALLPAPER_DIR / filename, 'wb') as f:
            f.write(e.content.read())
        wallpaper_grid.refresh()
        ui.notify(f'已入库: {filename}', type='positive')

    with ui.column().classes('p-8 max-w-6xl mx-auto'):
        ui.label('壁纸库').classes('text-white text-2xl font-bold mb-4')
        with ui.row().classes('items-center gap-4 mb-6'):
            ui.upload(label='上传壁纸/视频入库', auto_upload=True,
                      on_upload=on_upload).classes('w-72')
            ui.button('回主页', on_click=lambda: ui.navigate.to('/'))
        wallpaper_grid()
