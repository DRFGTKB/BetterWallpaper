"""
文件管理模块：壁纸库的「图书馆系统」
- 索引：扫描 static/ 目录，图片 + 视频
- 入库：把外部文件复制进库（唯一 ID 命名）
- 出库：删除库内文件（带安全校验）
纯逻辑模块，不依赖 UI。
"""
import functools
import random
import shutil
import time
from pathlib import Path

path_root = Path(__file__).resolve().parent.parent          # 项目根目录
WALLPAPER_DIR = path_root / 'static'                        # 壁纸库目录

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}
VIDEO_EXTS = {'.mp4', '.webm', '.mov', '.mkv', '.avi'}
ALL_EXTS = IMAGE_EXTS | VIDEO_EXTS

# magic 可选：装了用真实 MIME，没装退回扩展名判断
try:
    import magic as _magic
except ImportError:
    _magic = None


# ═══════════ 索引 ═══════════
def scan_all() -> list[Path]:
    """扫描壁纸库，返回全部媒体文件（图片+视频），按文件名排序"""
    return sorted(
        (p for p in WALLPAPER_DIR.iterdir() if p.suffix.lower() in ALL_EXTS),
        key=lambda p: p.name.lower(),
    )


def scan_images() -> list[Path]:
    return sorted(
        (p for p in WALLPAPER_DIR.iterdir() if p.suffix.lower() in IMAGE_EXTS),
        key=lambda p: p.name.lower(),
    )


def scan_videos() -> list[Path]:
    return sorted(
        (p for p in WALLPAPER_DIR.iterdir() if p.suffix.lower() in VIDEO_EXTS),
        key=lambda p: p.name.lower(),
    )


@functools.lru_cache(maxsize=512)          # 缓存类型，避免每次切换都读文件嗅探
def get_type(path: Path) -> str:
    """返回 'image' / 'video' / 'unknown'，magic 读真实 MIME，异常退回扩展名"""
    if _magic is not None:
        try:
            with open(path, 'rb') as f:
                mime = _magic.from_buffer(f.read(2048), mime=True)
            if mime.startswith('video/'):
                return 'video'
            if mime.startswith('image/'):
                return 'image'
        except Exception:
            pass
    ext = Path(path).suffix.lower()
    if ext in VIDEO_EXTS:
        return 'video'
    if ext in IMAGE_EXTS:
        return 'image'
    return 'unknown'


def is_video(path: Path) -> bool:
    return get_type(path) == 'video'


# ═══════════ 工具 ═══════════
def to_url(path: Path) -> str:
    """本地路径 → 浏览器 URL"""
    return f'/static/{Path(path).name}'


def next_id(ext: str) -> str:
    """生成唯一文件名：时间戳毫秒 + 随机数"""
    return f'{int(time.time() * 1000)}{random.randint(1000, 9999)}{ext}'


# ═══════════ 入库：把外部文件复制进壁纸库 ═══════════
def file_save(path: Path) -> Path:
    """将外部文件复制进 static/，自动生成唯一ID文件名，返回新路径"""
    p = Path(path)
    if not p.is_file():
        raise ValueError(f'不是文件: {p}')
    ext = p.suffix.lower()
    if ext not in ALL_EXTS:
        raise ValueError(f'不支持的格式: {ext}')
    target = WALLPAPER_DIR / next_id(ext)
    shutil.copy2(p, target)
    get_type.cache_clear()                         # 库变了，清类型缓存
    return target


# ═══════════ 出库：删除壁纸库内文件（防越权）═══════════
def file_delet(path: Path) -> None:
    """删除库内文件；只允许删 static/ 目录里的文件"""
    p = Path(path)
    if not p.is_file():
        raise ValueError(f'文件不存在: {p}')
    if p.parent.resolve() != WALLPAPER_DIR.resolve():
        raise ValueError(f'只能删除壁纸库内的文件: {p}')
    p.unlink()
    get_type.cache_clear()                         # 库变了，清类型缓存
