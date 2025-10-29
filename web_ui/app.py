"""
FastAPI Web UI Application

オーケストレーターとワーカーAIの統括ダッシュボード
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, NoReturn, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Claude Orchestrator Dashboard",
    description="リアルタイムAI並列実行ダッシュボード",
    version="10.0.0",
)

# グローバル設定
WORKSPACE_ROOT = Path(os.getenv("ORCHESTRATOR_WORKSPACE", "./workspace"))
LOGS_DIR = Path(os.getenv("ORCHESTRATOR_LOGS", "./workspace / logs"))
SCREENSHOTS_DIR = Path(os.getenv("ORCHESTRATOR_SCREENSHOTS", "./workspace / screenshots"))


# WebSocket接続管理
class ConnectionManager:
    """WebSocket接続マネージャー"""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """接続を受け入れ"""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """接続を削除"""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """全接続にメッセージをブロードキャスト"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                # Log the error but continue broadcasting to other connections
                print(f"Error broadcasting to connection: {e}")


manager = ConnectionManager()


# Static files
app.mount("/static", StaticFiles(directory="web_ui / static"), name="static")


@app.get("/")
async def index() -> FileResponse:
    """ダッシュボードのトップページ"""
    return FileResponse("web_ui / static / index.html")


@app.get("/api / status")
async def get_status() -> JSONResponse:
    """システム全体の状態を取得"""
    try:
        # ワークスペース内のワーカーディレクトリを検索
        workers = []
        if WORKSPACE_ROOT.exists():
            for worker_dir in WORKSPACE_ROOT.glob("worker_*"):
                worker_id = worker_dir.name

                # 出力ファイルを確認
                output_file = worker_dir / "output.txt"
                task_file = worker_dir / "task.txt"

                # タスク内容を読み込み
                task_content = ""
                if task_file.exists():
                    with open(task_file, "r", encoding="utf - 8") as f:
                        task_content = f.read().strip()[:100]  # 最初の100文字

                # 出力の最後の数行を読み込み
                recent_output = ""
                if output_file.exists():
                    with open(output_file, "r", encoding="utf - 8") as f:
                        lines = f.readlines()
                        recent_output = "".join(lines[-5:]) if lines else ""

                # スクリーンショットを確認
                screenshots = (
                    list(SCREENSHOTS_DIR.glob(f"{worker_id}_*.png"))
                    if SCREENSHOTS_DIR.exists()
                    else []
                )
                latest_screenshot = (
                    max(screenshots, key=lambda p: p.stat().st_mtime).name if screenshots else None
                )

                workers.append(
                    {
                        "id": worker_id,
                        "task": task_content,
                        "status": "running" if output_file.exists() else "pending",
                        "recent_output": recent_output,
                        "screenshot": latest_screenshot,
                        "updated_at": datetime.now().isoformat(),
                    }
                )

        # 最新のログファイルを取得
        latest_log = None
        if LOGS_DIR.exists():
            log_files = list(LOGS_DIR.glob("orchestrator_*.jsonl"))
            if log_files:
                latest_log_file = max(log_files, key=lambda p: p.stat().st_mtime)
                latest_log = latest_log_file.name

        return JSONResponse(
            {
                "status": "running" if workers else "idle",
                "workers_count": len(workers),
                "workers": workers,
                "latest_log": latest_log,
                "workspace": str(WORKSPACE_ROOT),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api / logs/{log_file}")
async def get_logs(log_file: str, lines: int = 100) -> JSONResponse:
    """ログファイルの内容を取得"""
    try:
        # Security: Prevent path traversal attacks
        if ".." in log_file or "/" in log_file or "\\" in log_file:
            return JSONResponse({"error": "Invalid log file name"}, status_code=400)

        log_path = LOGS_DIR / log_file

        # Security: Ensure the resolved path is within LOGS_DIR
        try:
            log_path = log_path.resolve()
            if not (
                LOGS_DIR.resolve() in log_path.parents or log_path.parent == LOGS_DIR.resolve()
            ):
                return JSONResponse({"error": "Invalid log file path"}, status_code=400)
        except (ValueError, OSError):
            return JSONResponse({"error": "Invalid log file path"}, status_code=400)

        if not log_path.exists():
            return JSONResponse({"error": "Log file not found"}, status_code=404)

        with open(log_path, "r", encoding="utf - 8") as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        # JSONLフォーマットをパース
        logs = []
        for line in recent_lines:
            try:
                logs.append(json.loads(line))
            except:
                logs.append({"raw": line.strip()})

        return JSONResponse(
            {"logs": logs, "total_lines": len(all_lines), "returned_lines": len(logs)}
        )

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api / screenshots/{screenshot_file}", response_model=None)
async def get_screenshot(screenshot_file: str) -> FileResponse | JSONResponse:
    """スクリーンショット画像を取得"""
    # Security: Prevent path traversal attacks
    if ".." in screenshot_file or "/" in screenshot_file or "\\" in screenshot_file:
        return JSONResponse({"error": "Invalid screenshot file name"}, status_code=400)

    screenshot_path = SCREENSHOTS_DIR / screenshot_file

    # Security: Ensure the resolved path is within SCREENSHOTS_DIR
    try:
        screenshot_path = screenshot_path.resolve()
        if screenshot_path.parent != SCREENSHOTS_DIR.resolve():
            return JSONResponse({"error": "Invalid screenshot file path"}, status_code=400)
    except (ValueError, OSError):
        return JSONResponse({"error": "Invalid screenshot file path"}, status_code=400)

    if not screenshot_path.exists():
        return JSONResponse({"error": "Screenshot not found"}, status_code=404)

    return FileResponse(screenshot_path)


@app.get("/api / worker/{worker_id}/output")
async def get_worker_output(worker_id: str, lines: int = 50) -> JSONResponse:
    """ワーカーの出力を取得"""
    try:
        # Security: Validate worker_id format
        if (
            not worker_id.startswith("worker_")
            or ".." in worker_id
            or "/" in worker_id
            or "\\" in worker_id
        ):
            return JSONResponse({"error": "Invalid worker ID"}, status_code=400)

        worker_dir = WORKSPACE_ROOT / worker_id

        # Security: Ensure worker_dir is within WORKSPACE_ROOT
        try:
            worker_dir = worker_dir.resolve()
            if worker_dir.parent != WORKSPACE_ROOT.resolve():
                return JSONResponse({"error": "Invalid worker directory"}, status_code=400)
        except (ValueError, OSError):
            return JSONResponse({"error": "Invalid worker directory"}, status_code=400)

        output_file = worker_dir / "output.txt"

        if not output_file.exists():
            return JSONResponse({"error": "Worker output not found"}, status_code=404)

        with open(output_file, "r", encoding="utf - 8") as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        return JSONResponse(
            {"worker_id": worker_id, "output": "".join(recent_lines), "total_lines": len(all_lines)}
        )

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocketエンドポイント - リアルタイム更新"""
    await manager.connect(websocket)
    try:
        while True:
            # クライアントからのメッセージを待機
            data = await websocket.receive_text()

            # 状態を取得して送信
            status_response = await get_status()
            await websocket.send_json(json.loads(status_response.body))

    except WebSocketDisconnect:
        manager.disconnect(websocket)


def start_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Webサーバーを起動"""
    print("=" * 62)
    print("  Claude Orchestrator Dashboard v10.0")
    print("  Real - time AI Parallel Execution Dashboard")
    print("=" * 62)
    print()
    print(f"Dashboard URL: http://{host}:{port}")
    print(f"Workspace: {WORKSPACE_ROOT}")
    print(f"Logs: {LOGS_DIR}")
    print(f"Screenshots: {SCREENSHOTS_DIR}")
    print()
    print("Starting server...")
    print()

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    start_server()
