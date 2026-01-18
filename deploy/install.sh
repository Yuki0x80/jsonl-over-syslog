#!/bin/bash
# jsonl-over-syslog インストールスクリプト

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== jsonl-over-syslog インストール ==="
echo ""

# 設定
INSTALL_DIR="${INSTALL_DIR:-/opt/telegram-crawler}"
SERVICE_USER="${SERVICE_USER:-telegram-crawler}"
STATE_DIR="/var/lib/jsonl-over-syslog"

# 1. 必要なディレクトリを作成
echo "1. ディレクトリを作成..."
sudo mkdir -p "$INSTALL_DIR"
sudo mkdir -p "$STATE_DIR"

# 2. ファイルをコピー
echo "2. ファイルをコピー..."
sudo cp "$PROJECT_ROOT/jsonl_to_syslog.py" "$INSTALL_DIR/"
sudo chmod +x "$INSTALL_DIR/jsonl_to_syslog.py"

# ラッパースクリプトをコピー
if [ -f "$PROJECT_ROOT/deploy/telegram-crawler-wrapper.sh" ]; then
    sudo mkdir -p "$INSTALL_DIR/deploy"
    sudo cp "$PROJECT_ROOT/deploy/telegram-crawler-wrapper.sh" "$INSTALL_DIR/deploy/"
    sudo chmod +x "$INSTALL_DIR/deploy/telegram-crawler-wrapper.sh"
    echo "   ラッパースクリプトをコピーしました"
fi

# 3. ユーザーを作成（存在しない場合）
if ! id "$SERVICE_USER" &>/dev/null; then
    echo "3. ユーザーを作成: $SERVICE_USER"
    sudo useradd -r -s /bin/false "$SERVICE_USER" || true
else
    echo "3. ユーザーは既に存在します: $SERVICE_USER"
fi

# 4. 権限を設定
echo "4. 権限を設定..."
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$STATE_DIR"

# 5. telegram-crawlerサービスファイルをインストール（ラッパースクリプト使用）
if [ -f "$SCRIPT_DIR/systemd/telegram-crawler.service" ]; then
    echo "5. telegram-crawlerサービスファイルをインストール..."
    sudo cp "$SCRIPT_DIR/systemd/telegram-crawler.service" /etc/systemd/system/
    sudo cp "$SCRIPT_DIR/systemd/telegram-crawler.timer" /etc/systemd/system/
    
    # サービスファイル内のパスを更新
    sudo sed -i "s|/opt/telegram-crawler|$INSTALL_DIR|g" /etc/systemd/system/telegram-crawler.service
    
    sudo systemctl daemon-reload
    echo "   telegram-crawlerサービスファイルをインストールしました"
    echo ""
    echo "   有効化するには: sudo systemctl enable --now telegram-crawler.timer"
    echo ""
    echo "   動作:"
    echo "   - telegram-crawlerを実行"
    echo "   - outputに生成された最新のJSONLファイルをsyslog経由で送信"
    echo "   - 10分ごとに自動実行"
    echo "   - PC再起動後も自動実行される（Persistent=true）"
else
    echo "5. telegram-crawlerサービスファイルが見つかりません（スキップ）"
fi

# 6. .envファイルの確認
if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo "7. .envファイルを作成してください:"
    echo "   sudo nano $INSTALL_DIR/.env"
    echo ""
    echo "   最低限の設定例:"
    echo "   SYSLOG_HOST=your-syslog-server.example.com"
    echo "   SYSLOG_PORT=6514"
    echo "   SYSLOG_PROTOCOL=tls"
    echo "   SYSLOG_CA_CERT=/etc/ssl/certs/ca.crt"
    echo "   SYSLOG_APP_NAME=telegram-crawler"
else
    echo "6. .envファイルは既に存在します"
fi

echo ""
echo "✓ インストール完了！"
echo ""
echo "次のステップ:"
echo "1. .envファイルを設定: sudo nano $INSTALL_DIR/.env"
echo "2. telegram-crawlerサービスを有効化: sudo systemctl enable --now telegram-crawler.timer"
echo "3. 状態を確認: sudo systemctl status telegram-crawler.timer"
