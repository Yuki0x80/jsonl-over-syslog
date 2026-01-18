#!/bin/bash
# ログ送信テストスクリプト

set -e

echo "=== JSONL over Syslog テスト ==="
echo ""

# テスト用のJSONLファイルを作成
TEST_FILE="test_telegram_messages.jsonl"
echo "1. テスト用JSONLファイルを作成: $TEST_FILE"

cat > "$TEST_FILE" << 'EOF'
{"channel_name": "test_channel", "message_id": 1, "text": "テストメッセージ1", "date": "2024-01-18T12:00:00Z"}
{"channel_name": "test_channel", "message_id": 2, "text": "テストメッセージ2", "date": "2024-01-18T12:01:00Z"}
{"channel_name": "test_channel", "message_id": 3, "text": "テストメッセージ3", "date": "2024-01-18T12:02:00Z"}
EOF

echo "   作成完了: $TEST_FILE"
echo ""

# .envファイルの読み込み
if [ -f ".env" ]; then
    echo "2. .envファイルを読み込み中..."
    # .envファイルから環境変数を読み込む（コメント行と空行を除外）
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    echo "   SYSLOG_HOST=${SYSLOG_HOST:-未設定}"
    echo "   SYSLOG_PORT=${SYSLOG_PORT:-未設定}"
    echo "   SYSLOG_PROTOCOL=${SYSLOG_PROTOCOL:-未設定}"
    echo "   SYSLOG_APP_NAME=${SYSLOG_APP_NAME:-未設定}"
    echo ""
else
    echo "2. .envファイルが見つかりません"
    echo "   デフォルト設定（localhost:5140, TCP, telegram-crawler）で送信します"
    echo "   注意: TLSの場合はポート6514がデフォルトです"
    echo ""
fi

# 送信コマンドの構築
HOST="${SYSLOG_HOST:-localhost}"
PROTOCOL="${SYSLOG_PROTOCOL:-tcp}"
APP_NAME="${SYSLOG_APP_NAME:-telegram-crawler}"

# プロトコルに応じてデフォルトポートを設定
if [ "$PROTOCOL" = "tls" ]; then
    PORT="${SYSLOG_PORT:-6514}"
else
    PORT="${SYSLOG_PORT:-5140}"
fi

echo "3. 送信設定:"
echo "   ホスト: $HOST"
echo "   ポート: $PORT"
echo "   プロトコル: $PROTOCOL"
echo "   アプリケーション名: $APP_NAME"
echo ""

# TLS設定の確認
TLS_ARGS=""
if [ "$PROTOCOL" = "tls" ]; then
    if [ -n "$SYSLOG_CA_CERT" ]; then
        TLS_ARGS="--ca-cert $SYSLOG_CA_CERT"
        echo "   CA証明書: $SYSLOG_CA_CERT"
    fi
    if [ -n "$SYSLOG_CLIENT_CERT" ] && [ -n "$SYSLOG_CLIENT_KEY" ]; then
        TLS_ARGS="$TLS_ARGS --client-cert $SYSLOG_CLIENT_CERT --client-key $SYSLOG_CLIENT_KEY"
        echo "   クライアント証明書: $SYSLOG_CLIENT_CERT"
        echo "   クライアント鍵: $SYSLOG_CLIENT_KEY"
    fi
    echo ""
fi

echo "4. ログを送信します..."
echo "   コマンド: python3 jsonl_to_syslog.py $TEST_FILE --host $HOST --port $PORT --protocol $PROTOCOL --app-name $APP_NAME $TLS_ARGS"
echo ""

python3 jsonl_to_syslog.py "$TEST_FILE" \
    --host "$HOST" \
    --port "$PORT" \
    --protocol "$PROTOCOL" \
    --app-name "$APP_NAME" \
    $TLS_ARGS

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ 送信成功！"
    echo ""
    echo "5. サーバ側でログを確認してください:"
    echo "   sudo tail -f /srv/logs/telegram-crawler/telegram-crawler-*.jsonl"
    echo ""
    echo "   または、rsyslogのログを確認:"
    echo "   sudo journalctl -u rsyslog -f"
    echo ""
else
    echo ""
    echo "✗ 送信失敗"
    echo "   エラーメッセージを確認してください"
    exit 1
fi

# クリーンアップ
read -p "テストファイルを削除しますか？ (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f "$TEST_FILE"
    echo "テストファイルを削除しました"
fi
