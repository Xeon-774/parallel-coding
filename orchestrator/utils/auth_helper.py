"""
認証ヘルパー - Claude CLI トークン設定

GUIダイアログでユーザーがトークンを入力できるようにします。
"""

import platform
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext
from typing import Optional


class ClaudeAuthDialog:
    """Claude CLI トークン設定用GUIダイアログ"""

    def __init__(self) -> None:
        self.token: Optional[str] = None
        self.root: Optional[tk.Tk] = None

    def show_token_input_dialog(self) -> Optional[str]:
        """
        トークン入力ダイアログを表示

        Returns:
            入力されたトークン、またはキャンセル時はNone
        """
        self.root = tk.Tk()
        self.root.title("Claude CLI 認証")
        self.root.geometry("600x400")

        # メインフレーム
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 説明テキスト
        instructions = tk.Label(
            main_frame, text="Claude CLI認証トークンの設定", font=("Arial", 14, "bold")
        )
        instructions.pack(pady=(0, 10))

        info_text = """
Claude CLIを使用するには、認証トークンが必要です。

手順:
1. https://console.anthropic.com/settings/keys にアクセス
2. "Create Key" をクリック
3. 生成されたトークンをコピー (sk-ant-で始まる)
4. 下のテキストボックスに貼り付け
5. "保存" ボタンをクリック
        """

        info_label = tk.Label(main_frame, text=info_text, justify=tk.LEFT, font=("Arial", 10))
        info_label.pack(pady=(0, 20))

        # トークン入力フィールド
        token_label = tk.Label(main_frame, text="認証トークン:")
        token_label.pack(anchor=tk.W)

        self.token_entry = scrolledtext.ScrolledText(
            main_frame, height=5, width=60, wrap=tk.WORD, font=("Courier", 9)
        )
        self.token_entry.pack(fill=tk.BOTH, expand=True, pady=(5, 20))

        # ボタンフレーム
        button_frame = tk.Frame(main_frame)
        button_frame.pack()

        save_button = tk.Button(
            button_frame,
            text="保存",
            command=self._on_save,
            width=15,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
        )
        save_button.pack(side=tk.LEFT, padx=5)

        cancel_button = tk.Button(
            button_frame, text="キャンセル", command=self._on_cancel, width=15, font=("Arial", 10)
        )
        cancel_button.pack(side=tk.LEFT, padx=5)

        # Enterキーで保存
        self.root.bind("<Return>", lambda e: self._on_save())

        # ウィンドウを中央に配置
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        # ダイアログを表示
        self.root.mainloop()

        return self.token

    def _on_save(self) -> None:
        """保存ボタンクリック時の処理"""
        token = self.token_entry.get("1.0", tk.END).strip()

        if not token:
            messagebox.showerror("エラー", "トークンを入力してください。")
            return

        if len(token) < 20:
            messagebox.showerror(
                "エラー", "トークンが短すぎます。正しいトークンを入力してください。"
            )
            return

        self.token = token
        if self.root:
            self.root.destroy()

    def _on_cancel(self) -> None:
        """キャンセルボタンクリック時の処理"""
        self.token = None
        if self.root:
            self.root.destroy()


def setup_claude_token_wsl(
    wsl_distribution: str = "Ubuntu-24.04", token: Optional[str] = None, use_gui: bool = False
) -> bool:
    """
    WSL内のClaude CLIにトークンを設定

    Args:
        wsl_distribution: WSLディストリビューション名
        token: 認証トークン（Noneの場合はuse_gui=Trueならばupdate表示、Falseならエラー）
        use_gui: GUIダイアログを使用するか（デフォルト: False）

    Returns:
        成功した場合True
    """
    # トークンが指定されていない場合
    if token is None:
        if use_gui:
            # GUIで入力
            dialog = ClaudeAuthDialog()
            token = dialog.show_token_input_dialog()

            if token is None:
                print("トークン設定がキャンセルされました。")
                return False
        else:
            # CLI - エラーを表示
            print("[ERROR] トークンが指定されていません。")
            print("  環境変数 CLAUDE_API_TOKEN を設定するか、")
            print("  .env ファイルに CLAUDE_API_TOKEN=sk-ant-... を追加してください。")
            return False

    # WSL内の設定ディレクトリを作成
    config_dir = "~/.config/claude"

    cmd_create_dir = f'wsl -d {wsl_distribution} bash -c "mkdir -p {config_dir}"'
    subprocess.run(cmd_create_dir, shell=True, check=True)

    # トークンファイルを作成
    # セキュリティのため、エスケープ処理を行う
    escaped_token = token.replace("'", "'\\''")

    cmd_write_token = (
        f"wsl -d {wsl_distribution} bash -c " f"\"echo '{escaped_token}' > {config_dir}/token.txt\""
    )

    try:
        subprocess.run(cmd_write_token, shell=True, check=True)
        print(f"✅ トークンをWSL ({wsl_distribution}) に保存しました。")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ トークン保存に失敗: {e}")
        return False


def setup_claude_token_windows(token: Optional[str] = None, use_gui: bool = False) -> bool:
    """
    Windows環境のClaude CLIにトークンを設定

    Args:
        token: 認証トークン（Noneの場合はuse_gui=Trueならば表示、Falseならエラー）
        use_gui: GUIダイアログを使用するか（デフォルト: False）

    Returns:
        成功した場合True
    """
    # トークンが指定されていない場合
    if token is None:
        if use_gui:
            # GUIで入力
            dialog = ClaudeAuthDialog()
            token = dialog.show_token_input_dialog()

            if token is None:
                print("トークン設定がキャンセルされました。")
                return False
        else:
            # CLI - エラーを表示
            print("[ERROR] トークンが指定されていません。")
            print("  環境変数 CLAUDE_API_TOKEN を設定するか、")
            print("  .env ファイルに CLAUDE_API_TOKEN=sk-ant-... を追加してください。")
            return False

    # Windows設定ディレクトリ
    config_dir = Path.home() / ".config" / "claude"
    config_dir.mkdir(parents=True, exist_ok=True)

    # トークンファイルを作成
    token_file = config_dir / "token.txt"

    try:
        with open(token_file, "w", encoding="utf-8") as f:
            f.write(token)
        print(f"✅ トークンを保存しました: {token_file}")
        return True
    except Exception as e:
        print(f"❌ トークン保存に失敗: {e}")
        return False


def get_token_from_env_or_file() -> Optional[str]:
    """
    環境変数またはファイルからトークンを取得

    優先順位:
    1. 環境変数 CLAUDE_API_TOKEN
    2. カレントディレクトリの .claude_token ファイル
    3. ホームディレクトリの .claude_token ファイル

    Returns:
        トークン、または見つからない場合はNone
    """
    import os

    # 1. 環境変数から取得
    token = os.getenv("CLAUDE_API_TOKEN")
    if token:
        print(f"✓ 環境変数 CLAUDE_API_TOKEN からトークンを取得しました")
        return token.strip()

    # 2. カレントディレクトリの .claude_token
    token_file = Path(".claude_token")
    if token_file.exists():
        try:
            token = token_file.read_text(encoding="utf-8").strip()
            if token:
                print(f"✓ {token_file} からトークンを取得しました")
                return token
        except Exception as e:
            print(f"警告: {token_file} の読み込みに失敗: {e}")

    # 3. ホームディレクトリの .claude_token
    token_file = Path.home() / ".claude_token"
    if token_file.exists():
        try:
            token = token_file.read_text(encoding="utf-8").strip()
            if token:
                print(f"✓ {token_file} からトークンを取得しました")
                return token
        except Exception as e:
            print(f"警告: {token_file} の読み込みに失敗: {e}")

    return None


def setup_claude_token(
    execution_mode: str = "wsl",
    wsl_distribution: str = "Ubuntu-24.04",
    token: Optional[str] = None,
    use_gui: bool = False,
) -> bool:
    """
    実行モードに応じてClaude CLIトークンを設定

    Args:
        execution_mode: 実行モード ("wsl" or "windows")
        wsl_distribution: WSLディストリビューション名
        token: 認証トークン（Noneの場合は自動取得を試みる）
        use_gui: GUIダイアログを使用するか（デフォルト: False）

    Returns:
        成功した場合True
    """
    # トークンが指定されていない場合、環境変数/ファイルから取得を試みる
    if token is None:
        token = get_token_from_env_or_file()

    # それでも取得できない場合、GUIを使用（use_gui=Trueの場合のみ）
    if token is None and use_gui:
        print("トークンが見つかりません。GUIダイアログを表示します...")

    if execution_mode == "wsl":
        return setup_claude_token_wsl(wsl_distribution, token, use_gui)
    else:
        return setup_claude_token_windows(token, use_gui)


if __name__ == "__main__":
    """テスト実行"""
    import sys

    print("=== Claude CLI 認証トークン設定 ===\n")

    # 実行モードを選択
    mode = input("実行モード (wsl/windows) [wsl]: ").strip().lower() or "wsl"

    if mode == "wsl":
        dist = input("WSLディストリビューション名 [Ubuntu-24.04]: ").strip() or "Ubuntu-24.04"
        success = setup_claude_token(execution_mode="wsl", wsl_distribution=dist)
    else:
        success = setup_claude_token(execution_mode="windows")

    if success:
        print("\n✅ トークン設定完了！")
        sys.exit(0)
    else:
        print("\n❌ トークン設定に失敗しました。")
        sys.exit(1)
