#!/bin/bash
# telegram-crawler実行後に自動的にjsonl_to_syslog.pyを実行するラッパースクリプト

set -e

# 設定
TELEGRAM_CRAWLER_DIR="${TELEGRAM_CRAWLER_DIR:-/opt/telegram-crawler}"
TELEGRAM_CRAWLER_SCRIPT="${TELEGRAM_CRAWLER_SCRIPT:-telegram_crawler.py}"
OUTPUT_DIR="${OUTPUT_DIR:-$TELEGRAM_CRAWLER_DIR/output}"
JSONL_TO_SYSLOG="${JSONL_TO_SYSLOG:-$TELEGRAM_CRAWLER_DIR/jsonl_to_syslog.py}"
STATE_FILE="${STATE_FILE:-/var/lib/jsonl-over-syslog/.last_run}"

echo "=== telegram-crawler実行 ==="
echo ""

# telegram-crawlerを実行
cd "$TELEGRAM_CRAWLER_DIR"
if [ -f "$TELEGRAM_CRAWLER_SCRIPT" ]; then
    echo "1. telegram-crawlerを実行中..."
    python3 "$TELEGRAM_CRAWLER_SCRIPT" "$@"
    CRAWLER_EXIT_CODE=$?
    
    if [ $CRAWLER_EXIT_CODE -ne 0 ]; then
        echo "✗ telegram-crawlerの実行に失敗しました（終了コード: $CRAWLER_EXIT_CODE）"
        exit $CRAWLER_EXIT_CODE
    fi
    
    echo "✓ telegram-crawlerの実行が完了しました"
    echo ""
else
    echo "✗ telegram-crawlerスクリプトが見つかりません: $TELEGRAM_CRAWLER_SCRIPT"
    exit 1
fi

# 処理完了後、最新のファイルを送信
echo "2. 最新のJSONLファイルをsyslog経由で送信..."
if [ -f "$JSONL_TO_SYSLOG" ]; then
    # 前回実行以降に作成されたファイルを自動的に処理
    # --dirオプションにより、最新のファイルのみが送信される
    echo "   送信対象ディレクトリ: $OUTPUT_DIR"
    python3 "$JSONL_TO_SYSLOG" --dir "$OUTPUT_DIR" --state-file "$STATE_FILE"
    
    if [ $? -eq 0 ]; then
        echo "✓ 送信完了"
    else
        echo "✗ 送信に失敗しました"
        exit 1
    fi
else
    echo "✗ jsonl_to_syslog.pyが見つかりません: $JSONL_TO_SYSLOG"
    exit 1
fi

echo ""
echo "✓ すべての処理が完了しました"
