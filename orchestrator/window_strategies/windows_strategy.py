"""
Windows window management strategy

Implements window management for Windows using PowerShell scripts.
"""

import subprocess
from pathlib import Path
from typing import Optional

from orchestrator.window_strategies.base import WindowInfo, WindowManagerBase


class WindowsWindowManager(WindowManagerBase):
    """
    Windows - specific window manager implementation

    Uses PowerShell scripts and batch files to create monitoring windows.
    """

    def create_monitoring_window(
        self, worker_id: str, task_name: str, output_file: str, error_file: Optional[str] = None
    ) -> WindowInfo:
        """Create monitoring window for Windows platform"""

        # Sanitize task name for window title
        clean_task_name = self._sanitize_task_name(task_name)
        window_title = f"[{worker_id}] {clean_task_name}"

        # Create PowerShell monitoring script
        worker_dir = self.workspace_root / worker_id
        worker_dir.mkdir(parents=True, exist_ok=True)

        monitor_script = self._create_powershell_script(
            worker_dir=worker_dir,
            worker_id=worker_id,
            task_name=clean_task_name,
            window_title=window_title,
            output_file=output_file,
        )

        # Create batch file to launch PowerShell with correct title
        batch_file = self._create_batch_launcher(
            worker_dir=worker_dir, window_title=window_title, monitor_script=monitor_script
        )

        # Launch the monitoring window
        try:
            process = subprocess.Popen(
                [str(batch_file)], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE
            )

            window_info = WindowInfo(
                worker_id=worker_id,
                task_name=task_name,
                window_title=window_title,
                batch_file=str(batch_file),
                process=process,
            )

            # Capture screenshot
            self._capture_screenshot(worker_id, window_title, window_info)

            self.windows[worker_id] = window_info
            return window_info

        except Exception as e:
            raise RuntimeError(f"Failed to create monitoring window: {e}")

    def _create_powershell_script(
        self, worker_dir: Path, worker_id: str, task_name: str, window_title: str, output_file: str
    ) -> Path:
        """Create PowerShell monitoring script"""

        script_path = worker_dir / "monitor.ps1"
        ps_output_file = str(Path(output_file)).replace("\\", "\\\\")

        # Escape special PowerShell characters
        task_name.replace('"', '`"').replace("$", "`$").replace("`", "``")

        ps_script = """
$host.UI.RawUI.WindowTitle = "{window_title}"
$outputFile = "{ps_output_file}"

Write - Host "====================================" -ForegroundColor Cyan
Write - Host "  Worker AI Monitor" -ForegroundColor Cyan
Write - Host "====================================" -ForegroundColor Cyan
Write - Host ""
Write - Host "Worker ID: {worker_id}" -ForegroundColor Yellow
Write - Host "Task: {safe_task_name}" -ForegroundColor Yellow
Write - Host ""
Write - Host "Waiting for worker..." -ForegroundColor Gray
Write - Host ""

# Wait for output file (max 30 seconds)
$timeout = 30
$elapsed = 0
while (-not (Test - Path $outputFile) -and $elapsed -lt $timeout) {{
    Start - Sleep -Milliseconds 500
    $elapsed += 0.5
}}

if (Test - Path $outputFile) {{
    Write - Host "Worker started!" -ForegroundColor Green
    Write - Host "====================================" -ForegroundColor Cyan
    Write - Host ""
    Get - Content $outputFile -Wait -Tail 0
}} else {{
    Write - Host "Timeout: Worker did not start" -ForegroundColor Red
}}

Write - Host ""
Write - Host "====================================" -ForegroundColor Cyan
Write - Host "  Worker Completed" -ForegroundColor Green
Write - Host "====================================" -ForegroundColor Cyan
"""

        if self.auto_close:
            ps_script += """
Write - Host "Closing in {self.close_delay} seconds..." -ForegroundColor Yellow
Start - Sleep -Seconds {self.close_delay}
"""
        else:
            ps_script += """
Write - Host "Press any key to close..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
"""

        with open(script_path, "w", encoding="utf - 8") as f:
            f.write(ps_script)

        return script_path

    def _create_batch_launcher(
        self, worker_dir: Path, window_title: str, monitor_script: Path
    ) -> Path:
        """Create batch file to launch PowerShell with correct title"""

        batch_file = worker_dir / "launch_monitor.bat"
        safe_title = window_title.replace("\n", " ").replace("\r", " ")

        batch_content = """@echo off
title {safe_title}
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "{monitor_script}"
"""

        with open(batch_file, "w", encoding="utf - 8") as f:
            f.write(batch_content)

        return batch_file

    def close_window(self, worker_id: str) -> None:
        """Close a specific window"""
        if worker_id not in self.windows:
            return

        window_info = self.windows[worker_id]
        if window_info.process:
            try:
                window_info.process.terminate()
            except Exception:
                pass

        del self.windows[worker_id]
