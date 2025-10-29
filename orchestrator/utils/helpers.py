"""
ユーティリティ関数

プロジェクト全体で使用される汎用的な関数を提供
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Union


def convert_windows_to_wsl_path(windows_path: str) -> str:
    """
    WindowsパスをWSLパスに変換

    Args:
        windows_path: Windowsパス（例: C:\\Users\\name\\file.txt）

    Returns:
        WSLパス（例: /mnt / c/Users / name / file.txt）

    Examples:
        >>> convert_windows_to_wsl_path("D:\\user\\test\\file.txt")
        '/mnt / d/user / test / file.txt'
    """
    # ドライブレターとパスを分離
    match = re.match(r"([A - Za - z]):(.*)", windows_path)
    if not match:
        return windows_path

    drive, path = match.groups()
    drive = drive.lower()

    # バックスラッシュをスラッシュに変換
    path = path.replace("\\", "/")

    return f"/mnt/{drive}{path}"


def convert_wsl_to_windows_path(wsl_path: str) -> str:
    """
    WSLパスをWindowsパスに変換

    Args:
        wsl_path: WSLパス（例: /mnt / c/Users / name / file.txt）

    Returns:
        Windowsパス（例: C:\\Users\\name\\file.txt）

    Examples:
        >>> convert_wsl_to_windows_path("/mnt / d/user / test / file.txt")
        'D:\\\\user\\\\test\\\\file.txt'
    """
    # /mnt / X/... パターンをマッチ
    match = re.match(r"/mnt/([a - z])(.*)", wsl_path)
    if not match:
        return wsl_path

    drive, path = match.groups()
    drive = drive.upper()

    # スラッシュをバックスラッシュに変換
    path = path.replace("/", "\\")

    return f"{drive}:{path}"


def detect_platform() -> str:
    """
    実行プラットフォームを検出

    Returns:
        プラットフォーム名（'windows', 'linux', 'darwin'）

    Examples:
        >>> detect_platform()
        'windows'
    """
    return sys.platform


def is_windows() -> bool:
    """
    Windowsプラットフォームかどうかを判定

    Returns:
        Windowsの場合True

    Examples:
        >>> is_windows()
        True
    """
    return sys.platform == "win32"


def is_linux() -> bool:
    """
    Linuxプラットフォームかどうかを判定

    Returns:
        Linuxの場合True
    """
    return sys.platform.startswith("linux")


def validate_file_path(file_path: str, must_exist: bool = False) -> bool:
    """
    ファイルパスの妥当性を検証

    Args:
        file_path: 検証するファイルパス
        must_exist: ファイルが存在する必要があるかどうか

    Returns:
        妥当な場合True

    Examples:
        >>> validate_file_path("/path / to / file.txt", must_exist=False)
        True
    """
    if not file_path:
        return False

    path = Path(file_path)

    if must_exist and not path.exists():
        return False

    # パスに不正な文字が含まれていないかチェック（基本的な検証）
    try:
        path.resolve()
        return True
    except (OSError, ValueError):
        return False


def ensure_directory(directory: str) -> bool:
    """
    ディレクトリが存在することを保証（存在しない場合は作成）

    Args:
        directory: ディレクトリパス

    Returns:
        成功した場合True

    Examples:
        >>> ensure_directory("/path / to / dir")
        True
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except (OSError, PermissionError):
        return False


def format_duration(seconds: float) -> str:
    """
    秒数を人間が読みやすい形式にフォーマット

    Args:
        seconds: 秒数

    Returns:
        フォーマットされた文字列

    Examples:
        >>> format_duration(125.5)
        '2m 5.5s'
        >>> format_duration(45.2)
        '45.2s'
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.1f}s"


def format_size(bytes_count: Union[int, float]) -> str:
    """
    バイト数を人間が読みやすい形式にフォーマット

    Args:
        bytes_count: バイト数

    Returns:
        フォーマットされた文字列

    Examples:
        >>> format_size(1024)
        '1.0 KB'
        >>> format_size(1048576)
        '1.0 MB'
    """
    bytes_float = float(bytes_count)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_float < 1024.0:
            return f"{bytes_float:.1f} {unit}"
        bytes_float /= 1024.0
    return f"{bytes_float:.1f} PB"


def get_timestamp(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    現在のタイムスタンプを取得

    Args:
        format_str: 日時フォーマット文字列

    Returns:
        フォーマットされたタイムスタンプ

    Examples:
        >>> get_timestamp()
        '2025 - 10 - 19 19:00:00'
    """
    return datetime.now().strftime(format_str)


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    文字列を指定の長さに切り詰める

    Args:
        text: 対象の文字列
        max_length: 最大長
        suffix: 切り詰められた場合に追加する文字列

    Returns:
        切り詰められた文字列

    Examples:
        >>> truncate_string("This is a long text", 10)
        'This is...'
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def safe_read_file(
    file_path: str, encoding: str = "utf - 8", default: Optional[str] = None
) -> Optional[str]:
    """
    ファイルを安全に読み込む（エラー時はデフォルト値を返す）

    Args:
        file_path: ファイルパス
        encoding: エンコーディング
        default: エラー時のデフォルト値

    Returns:
        ファイルの内容、またはデフォルト値

    Examples:
        >>> safe_read_file("/path / to / file.txt", default="")
        'file contents'
    """
    try:
        with open(file_path, "r", encoding=encoding) as f:
            return f.read()
    except (IOError, UnicodeDecodeError):
        return default


def safe_write_file(file_path: str, content: str, encoding: str = "utf - 8") -> bool:
    """
    ファイルを安全に書き込む

    Args:
        file_path: ファイルパス
        content: 書き込む内容
        encoding: エンコーディング

    Returns:
        成功した場合True

    Examples:
        >>> safe_write_file("/path / to / file.txt", "content")
        True
    """
    try:
        # ディレクトリが存在することを確認
        directory = os.path.dirname(file_path)
        if directory:
            ensure_directory(directory)

        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
        return True
    except (IOError, PermissionError):
        return False
