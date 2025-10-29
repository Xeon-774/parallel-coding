"""
WSL Claude CLI 自動セットアップ

Claude CLIのインストールと認証を完全自動化します。
トークン入力が必要な場合は、GUIウィンドウで入力を求めます。
"""

import subprocess
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext
from typing import Callable, Optional


class TokenInputDialog:
    """トークン入力ダイアログ（シンプル版）"""

    def __init__(
        self, title: str = "Claude API Token", prompt: str = "トークンを入力してください:"
    ):
        self.token: Optional[str] = None
        self.title = title
        self.prompt = prompt

    def show(self) -> Optional[str]:
        """ダイアログを表示してトークンを取得"""
        root = tk.Tk()
        root.title(self.title)
        root.geometry("500x300")

        # メインフレーム
        frame = tk.Frame(root, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # 説明
        label = tk.Label(frame, text=self.prompt, font=("Arial", 11))
        label.pack(pady=(0, 10))

        info = tk.Label(
            frame,
            text="https://claude.ai / settings / developer でトークンを生成",
            fg="blue",
            cursor="hand2",
            font=("Arial", 9),
        )
        info.pack(pady=(0, 10))

        # クリックでブラウザを開く
        def open_url(event: tk.Event[tk.Misc]) -> None:
            import webbrowser

            webbrowser.open("https://claude.ai / settings / developer")

        info.bind("<Button - 1>", open_url)

        # トークン入力
        token_entry = scrolledtext.ScrolledText(frame, height=6, wrap=tk.WORD, font=("Courier", 9))
        token_entry.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        token_entry.focus()

        # ボタン
        def on_ok() -> None:
            self.token = token_entry.get("1.0", tk.END).strip()
            if self.token:
                root.destroy()
            else:
                messagebox.showerror("エラー", "トークンを入力してください")

        def on_cancel() -> None:
            self.token = None
            root.destroy()

        btn_frame = tk.Frame(frame)
        btn_frame.pack()

        ok_btn = tk.Button(
            btn_frame,
            text="OK",
            command=on_ok,
            width=12,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
        )
        ok_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = tk.Button(btn_frame, text="キャンセル", command=on_cancel, width=12)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # Enterキーで送信
        root.bind("<Return>", lambda e: on_ok())
        root.bind("<Escape>", lambda e: on_cancel())

        # ウィンドウを中央に配置
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
        y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
        root.geometry(f"+{x}+{y}")

        root.mainloop()
        return self.token


class WSLClaudeSetup:
    """WSL Claude CLI 自動セットアップ"""

    def __init__(self, wsl_distribution: str = "Ubuntu - 24.04"):
        self.wsl_distribution = wsl_distribution
        self.process: Optional[subprocess.Popen[str]] = None
        self.output_buffer: list[str] = []
        self.token_requested = False

    def run_wsl_command(
        self, command: str, timeout: int = 120, on_output: Optional[Callable[[str], None]] = None
    ) -> tuple[bool, str]:
        """
        WSLコマンドを実行し、出力を監視

        Args:
            command: 実行するコマンド
            timeout: タイムアウト（秒）
            on_output: 出力があった際のコールバック

        Returns:
            (成功フラグ, 出力)
        """
        full_command = f'wsl -d {self.wsl_distribution} bash -c "{command}"'

        try:
            self.process = subprocess.Popen(
                full_command,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            output_lines = []
            start_time = time.time()

            # Type guard: process is guaranteed to be non - None here
            assert self.process is not None
            assert self.process.stdout is not None

            while True:
                # タイムアウトチェック
                if time.time() - start_time > timeout:
                    self.process.kill()
                    return False, "Timeout"

                # 出力を読み込み
                line = self.process.stdout.readline()

                if line:
                    line = line.rstrip()
                    output_lines.append(line)
                    print(f"[WSL] {line}")

                    if on_output:
                        on_output(line)

                # プロセス終了チェック
                if self.process.poll() is not None:
                    # 残りの出力を読み込み
                    remaining = self.process.stdout.read()
                    if remaining:
                        output_lines.append(remaining.rstrip())
                    break

            exit_code = self.process.returncode
            output = "\n".join(output_lines)

            return exit_code == 0, output

        except Exception as e:
            return False, str(e)

    def check_claude_installed(self) -> bool:
        """Claude CLIがインストールされているか確認"""
        print("[1 / 4] Claude CLI インストール確認中...")

        success, output = self.run_wsl_command(
            "~/.local / bin / claude --version 2>/dev / null || echo 'not installed'", timeout=10
        )

        if success and "not installed" not in output:
            print(f"  [OK] Claude CLI 既にインストール済み: {output}")
            return True
        else:
            print("  -> Claude CLI 未インストール")
            return False

    def install_claude_cli(self) -> bool:
        """Claude CLIをインストール"""
        print("[2 / 4] Claude CLI インストール中...")
        print("  公式インストールスクリプトを実行します...")

        success, output = self.run_wsl_command(
            "curl -fsSL https://claude.ai / install.sh | bash", timeout=180
        )

        if success:
            print("  [OK] Claude CLI インストール完了")
            return True
        else:
            print(f"  [X] インストール失敗: {output}")
            return False

    def setup_token_interactive(self) -> bool:
        """
        対話的にトークンを設定

        setup - token コマンドを実行し、トークン入力が必要になったら
        GUIダイアログを表示して入力を求める
        """
        print("[3 / 4] トークン設定中...")

        # まず、既にトークンが設定されているかチェック
        success, output = self.run_wsl_command(
            "test -f ~/.config / claude / token.txt && echo 'exists' || echo 'not exists'",
            timeout=10,
        )

        if "exists" in output:
            print("  [OK] トークン既に設定済み")
            # 認証確認
            success, output = self.run_wsl_command(
                "~/.local / bin / claude --print <<< 'test' 2>&1", timeout=15
            )
            if success and "Invalid API key" not in output:
                print("  [OK] 認証成功")
                return True
            else:
                print("  -> トークンが無効、再設定します")

        # トークンをGUIで取得
        print("  トークン入力ダイアログを表示します...")

        dialog = TokenInputDialog(
            title="Claude CLI トークン設定", prompt="Claude API トークンを入力してください:"
        )

        token = dialog.show()

        if not token:
            print("  [X] トークン入力がキャンセルされました")
            return False

        print(f"  トークンを取得しました（長さ: {len(token)}文字）")

        # トークンを設定
        print("  トークンをWSLに保存中...")

        # 設定ディレクトリ作成
        self.run_wsl_command("mkdir -p ~/.config / claude", timeout=10)

        # トークンを保存（エスケープ処理）
        escaped_token = token.replace("'", "'\\''")
        success, output = self.run_wsl_command(
            f"echo '{escaped_token}' > ~/.config / claude / token.txt", timeout=10
        )

        if not success:
            print(f"  [X] トークン保存失敗: {output}")
            return False

        # 認証確認
        print("  認証を確認中...")
        success, output = self.run_wsl_command(
            "~/.local / bin / claude --print <<< 'Hello' 2>&1", timeout=20
        )

        if success and "Invalid API key" not in output:
            print("  [OK] 認証成功！")
            return True
        else:
            print(f"  [X] 認証失敗: {output}")
            return False

    def verify_setup(self) -> bool:
        """セットアップを検証"""
        print("[4 / 4] セットアップ検証中...")

        # バージョン確認
        success, output = self.run_wsl_command("~/.local / bin / claude --version", timeout=10)

        if not success:
            print("  [X] Claude CLI が正しくインストールされていません")
            return False

        print(f"  [OK] Claude CLI バージョン: {output}")

        # 簡単なテスト実行
        print("  簡単なテストを実行中...")
        success, output = self.run_wsl_command(
            "~/.local / bin / claude --print <<< 'Say hello in one word' 2>&1", timeout=20
        )

        if success and len(output) > 0 and "Invalid API key" not in output:
            print("  [OK] テスト成功")
            print(f"  Claude応答: {output[:100]}")
            return True
        else:
            print(f"  [X] テスト失敗: {output}")
            return False

    def run_full_setup(self) -> bool:
        """完全セットアップを実行"""
        print("=" * 70)
        print("WSL Claude CLI 自動セットアップ")
        print(f"WSL Distribution: {self.wsl_distribution}")
        print("=" * 70)
        print()

        # 1. インストール確認
        already_installed = self.check_claude_installed()

        # 2. インストール（必要な場合）
        if not already_installed:
            if not self.install_claude_cli():
                return False
        else:
            print("[2 / 4] インストール -> スキップ (既にインストール済み)")

        # 3. トークン設定
        if not self.setup_token_interactive():
            return False

        # 4. 検証
        if not self.verify_setup():
            return False

        print()
        print("=" * 70)
        print("[OK] セットアップ完了！")
        print("=" * 70)
        print()
        print("次のステップ:")
        print("  python tests / test_simple_worker_wsl.py")
        print()

        return True


def main() -> None:
    """メイン関数"""
    import sys

    # WSLディストリビューション名を取得
    if len(sys.argv) > 1:
        distribution = sys.argv[1]
    else:
        distribution = "Ubuntu - 24.04"

    setup = WSLClaudeSetup(wsl_distribution=distribution)

    try:
        success = setup.run_full_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n中断されました。")
        sys.exit(1)
    except Exception as e:
        print(f"\n[X] エラー: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
