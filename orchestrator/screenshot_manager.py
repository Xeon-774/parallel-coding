"""
自動スクリーンショット管理モジュール

ワーカーAIウィンドウのスクリーンショットを自動的に撮影し、
AIが自律的に状態を確認できるようにする。
"""

import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class ScreenshotManager:
    """
    スクリーンショット管理クラス

    ウィンドウのスクリーンショットを自動撮影し、保存・確認する
    """

    def __init__(self, workspace_root: str):
        """
        初期化

        Args:
            workspace_root: ワークスペースのルートディレクトリ
        """
        self.workspace_root = Path(workspace_root)
        self.screenshots_dir = self.workspace_root / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)

    def capture_window(
        self, worker_id: str, window_title: str, delay: float = 2.0
    ) -> Optional[str]:
        """
        特定のウィンドウのスクリーンショットを撮影

        Args:
            worker_id: ワーカーID
            window_title: ウィンドウタイトル
            delay: 撮影前の遅延（秒）

        Returns:
            スクリーンショットのファイルパス（失敗時はNone）
        """
        # 少し待機してウィンドウが完全に開くのを待つ
        time.sleep(delay)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = self.screenshots_dir / f"{worker_id}_{timestamp}.png"

        # PowerShellスクリプトでスクリーンショットを撮影
        ps_script = """
Add - Type -AssemblyName System.Windows.Forms
Add - Type -AssemblyName System.Drawing

# 特定のウィンドウを探す
Add - Type @"
    using System;
    using System.Runtime.InteropServices;
    using System.Text;
    public class WindowHelper {{
        [DllImport("user32.dll")]
        public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

        [DllImport("user32.dll")]
        public static extern bool SetForegroundWindow(IntPtr hWnd);

        [DllImport("user32.dll")]
        public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

        [DllImport("user32.dll")]
        public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, int nFlags);
    }}

    public struct RECT {{
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }}
"@

# ウィンドウを探す（worker_idでマッチ - より確実）
# タイトルに改行が含まれる可能性があるため、worker_idのみで検索
$windows = Get - Process | Where - Object {{ $_.MainWindowTitle -like "*[{worker_id}]*" }}

if ($windows) {{
    $window = $windows[0]
    $hwnd = $window.MainWindowHandle

    # ウィンドウを前面に
    [WindowHelper]::SetForegroundWindow($hwnd)
    Start - Sleep -Milliseconds 500

    # ウィンドウの矩形を取得
    $rect = New - Object RECT
    [WindowHelper]::GetWindowRect($hwnd, [ref]$rect)

    $width = $rect.Right - $rect.Left
    $height = $rect.Bottom - $rect.Top

    if ($width -gt 0 -and $height -gt 0) {{
        # ビットマップを作成
        $bitmap = New - Object System.Drawing.Bitmap($width, $height)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)

        # ウィンドウをキャプチャ
        $hdcBitmap = $graphics.GetHdc()
        [WindowHelper]::PrintWindow($hwnd, $hdcBitmap, 0)
        $graphics.ReleaseHdc($hdcBitmap)

        # 保存
        $bitmap.Save("{screenshot_path}", [System.Drawing.Imaging.ImageFormat]::Png)
        $bitmap.Dispose()
        $graphics.Dispose()

        Write - Host "Screenshot saved: {screenshot_path}"
    }}
}} else {{
    # ウィンドウが見つからない場合、全画面をキャプチャ
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bitmap = New - Object System.Drawing.Bitmap($screen.Width, $screen.Height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
    $bitmap.Save("{screenshot_path}", [System.Drawing.Imaging.ImageFormat]::Png)
    $bitmap.Dispose()
    $graphics.Dispose()
    Write - Host "Window not found. Full screen captured: {screenshot_path}"
}}
"""

        # PowerShellスクリプトを実行
        try:
            _ =  subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    ps_script,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if screenshot_path.exists():
                return str(screenshot_path)
            else:
                print(f"[WARNING] Screenshot not created: {screenshot_path}")
                return None

        except Exception as e:
            print(f"[ERROR] Screenshot capture failed: {e}")
            return None

    def capture_all_workers(self, worker_ids: List[str], delay: float = 2.0) -> List[str]:
        """
        すべてのワーカーウィンドウのスクリーンショットを撮影

        Args:
            worker_ids: ワーカーIDのリスト
            delay: 各撮影の間隔（秒）

        Returns:
            スクリーンショットのファイルパスリスト
        """
        screenshots = []
        for worker_id in worker_ids:
            screenshot = self.capture_window(
                worker_id=worker_id, window_title=f"[{worker_id}]", delay=delay
            )
            if screenshot:
                screenshots.append(screenshot)

        return screenshots

    def get_latest_screenshot(self, worker_id: str) -> Optional[str]:
        """
        特定のワーカーの最新スクリーンショットを取得

        Args:
            worker_id: ワーカーID

        Returns:
            最新のスクリーンショットパス（なければNone）
        """
        screenshots = sorted(
            self.screenshots_dir.glob(f"{worker_id}_*.png"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        return str(screenshots[0]) if screenshots else None

    def cleanup_old_screenshots(self, days: int = 7) -> None:
        """
        古いスクリーンショットを削除

        Args:
            days: 保持期間（日数）
        """
        cutoff_time = time.time() - (days * 24 * 3600)

        for screenshot in self.screenshots_dir.glob("*.png"):
            if screenshot.stat().st_mtime < cutoff_time:
                screenshot.unlink()
