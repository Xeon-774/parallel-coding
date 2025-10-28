#!/bin/bash

# MainAI起動ヘルパースクリプト
# ユーザーがMainAIワークスペースでClaude Codeを起動するのを補助

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 設定
MAIN_AI_WORKSPACE="${PROJECT_ROOT}/workspace/main_ai"
PROMPT_FILE="${SCRIPT_DIR}/prompts/main_ai_system.md"

# カラー出力
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   MainAI 起動ヘルパー (v11.0)                  ║${NC}"
echo -e "${GREEN}║   Recursive Orchestration System              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""

# ワークスペース準備
echo -e "${YELLOW}[1/3]${NC} ワークスペース準備中..."
mkdir -p "$MAIN_AI_WORKSPACE"
mkdir -p "$MAIN_AI_WORKSPACE/workers"
echo "      ✓ Workspace: $MAIN_AI_WORKSPACE"

# MonitorAIワークスペース準備
MONITOR_AI_WORKSPACE="${PROJECT_ROOT}/workspace/monitor_ai"
mkdir -p "$MONITOR_AI_WORKSPACE"
echo "      ✓ Monitor workspace: $MONITOR_AI_WORKSPACE"

# システムプロンプト表示
echo -e "${YELLOW}[2/3]${NC} システムプロンプト準備完了"
echo "      ✓ Prompt: $PROMPT_FILE"

# 起動方法表示
echo -e "${YELLOW}[3/3]${NC} Claude Code起動方法"
echo ""
echo "以下のコマンドでMainAIを起動してください:"
echo ""
echo -e "${GREEN}claude_code --workspace \"$MAIN_AI_WORKSPACE\"${NC}"
echo ""
echo "起動後、以下のプロンプトを送信してください:"
echo ""
echo "---"
cat "$PROMPT_FILE" | head -n 20
echo "..."
echo "(完全なプロンプトは $PROMPT_FILE を参照)"
echo "---"
echo ""
echo "または、プロンプトファイルをClaude Codeに直接読み込ませてください。"
echo ""

# 環境変数設定ヒント
echo -e "${YELLOW}Tips:${NC}"
echo "  - Wait時間を変更: export RECURSIVE_ORCH_MONITOR_TIMEOUT=60"
echo "  - デバッグモード: export RECURSIVE_ORCH_DEBUG_MODE=true"
echo "  - 設定確認: python orchestrator/recursive/config.py"
echo ""

# 自動起動オプション
read -p "自動的にClaude Codeを起動しますか？ (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo ""
    echo -e "${GREEN}Claude Code起動中...${NC}"
    echo ""

    # Claude Code起動
    cd "$PROJECT_ROOT"
    claude_code --workspace "$MAIN_AI_WORKSPACE"
fi
