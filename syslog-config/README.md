# Syslogサーバ設定ファイル

このディレクトリには、syslogサーバ側の設定ファイル例が含まれています。

## ファイル一覧

- `rsyslog.conf.example`: rsyslog用の設定ファイル例
- `syslog-ng.conf.example`: syslog-ng用の設定ファイル例

## 使用方法

### rsyslogの場合

1. 設定ファイルをコピー：
   ```bash
   sudo cp syslog-config/rsyslog.conf.example /etc/rsyslog.d/99-telegram-crawler.conf
   ```

2. TLS証明書を設定：
   - CA証明書: `/etc/ssl/certs/ca-certificates.crt`
   - サーバ証明書: `/etc/ssl/certs/server.crt`
   - サーバ秘密鍵: `/etc/ssl/private/server.key`
   - 必要に応じてパスを変更してください

3. ログディレクトリを作成：
   ```bash
   sudo mkdir -p /var/log/telegram-crawler
   sudo chown syslog:syslog /var/log/telegram-crawler
   ```

3. rsyslogを再起動：
   ```bash
   sudo systemctl restart rsyslog
   ```

4. 設定を確認：
   ```bash
   sudo systemctl status rsyslog
   sudo tail -f /var/log/telegram-crawler/telegram-crawler-*.log
   ```

### syslog-ngの場合

1. **TLS証明書を準備**：
   ```bash
   # 証明書ファイルが存在するか確認
   ls -la /etc/ssl/certs/server.crt
   ls -la /etc/ssl/private/server.key
   ls -la /etc/ssl/certs/ca-certificates.crt
   
   # 存在しない場合は証明書を生成するか、既存の証明書を使用してください
   # 証明書のパスは設定ファイル内で変更できます
   ```

2. **設定ファイルをコピー**：
   ```bash
   sudo cp syslog-config/syslog-ng.conf.example /etc/syslog-ng/conf.d/telegram-crawler.conf
   ```

3. **証明書パスの確認と修正**（必要に応じて）：
   ```bash
   sudo nano /etc/syslog-ng/conf.d/telegram-crawler.conf
   # 証明書のパスを実際の環境に合わせて修正
   ```

4. **ログディレクトリを作成**：
   ```bash
   sudo mkdir -p /var/log/telegram-crawler
   sudo chown syslog:syslog /var/log/telegram-crawler
   sudo chmod 755 /var/log/telegram-crawler
   ```

5. **syslog-ngの設定を確認**：
   ```bash
   sudo syslog-ng -s
   # エラーがないことを確認
   ```

6. **syslog-ngを再起動**：
   ```bash
   sudo systemctl restart syslog-ng
   ```

7. **設定を確認**：
   ```bash
   # syslog-ngの状態を確認
   sudo systemctl status syslog-ng
   
   # ポート6514がリッスンしているか確認
   sudo ss -tlnp | grep 6514
   
   # ログファイルを監視
   sudo tail -f /var/log/telegram-crawler/telegram-crawler-*.log
   ```

## クライアント側の設定

syslogサーバ側の設定だけでは動作しません。**クライアント側（`jsonl_to_syslog.py`）もTLSで送信するように設定する必要があります**。

### .envファイルの設定例

```bash
# syslogサーバのホスト名
SYSLOG_HOST=your-syslog-server.example.com

# TLSプロトコルとポート6514を使用
SYSLOG_PROTOCOL=tls
SYSLOG_PORT=6514

# CA証明書のパス（サーバ証明書を検証するために必要）
SYSLOG_CA_CERT=/path/to/ca.crt

# クライアント認証が必要な場合（オプション）
# SYSLOG_CLIENT_CERT=/path/to/client.crt
# SYSLOG_CLIENT_KEY=/path/to/client.key

# アプリケーション名をtelegram-crawlerに設定
SYSLOG_APP_NAME=telegram-crawler
```

### 動作確認

```bash
# テスト用のJSONLファイルを作成
echo '{"test": "message"}' > test.jsonl

# syslogサーバに送信（TLS）
python jsonl_to_syslog.py test.jsonl --host your-syslog-server.example.com --port 6514 --protocol tls --ca-cert /path/to/ca.crt --app-name telegram-crawler

# syslogサーバ側でログを確認
sudo tail -f /var/log/telegram-crawler/telegram-crawler-*.log
```

## ポート番号

この設定は**TLS通信を前提**としており、以下のポート番号を使用します：

- **TLS**: 6514（RFC 5425推奨、デフォルト）

ポート番号は、`jsonl_to_syslog.py`の`--port`オプションまたは`.env`ファイルの`SYSLOG_PORT`で変更できます。

## ログファイルの保存先

設定例では、以下のディレクトリにログファイルを保存します：

- `/var/log/telegram-crawler/telegram-crawler-YYYY-MM-DD.log`: 日付ごとのログファイル
- `/var/log/telegram-crawler/telegram-crawler.log`: すべてのメッセージを1つのファイルに保存（コメントアウト）
- `/var/log/telegram-crawler/telegram-crawler-raw.log`: JSONL形式でメッセージ部分のみ保存（コメントアウト）

必要に応じて、設定ファイルを編集して保存先を変更してください。

## セキュリティ

### ファイアウォール設定

syslogサーバでTLSポートを開く必要があります：

```bash
# UFWの場合
sudo ufw allow 6514/tcp

# firewalldの場合
sudo firewall-cmd --add-port=6514/tcp --permanent
sudo firewall-cmd --reload
```

### TLSを使用する場合

TLSを使用する場合は、適切な証明書を設定してください：

1. CA証明書、サーバ証明書、サーバ秘密鍵を準備
2. 設定ファイル内の証明書パスを更新
3. クライアント（jsonl-over-syslog）にCA証明書を提供

## トラブルシューティング

### ログが受信されない場合

1. rsyslog/syslog-ngが正しく起動しているか確認：
   ```bash
   sudo systemctl status rsyslog
   # または
   sudo systemctl status syslog-ng
   ```

2. ポートが開いているか確認：
   ```bash
   sudo netstat -tlnp | grep 6514
   # または
   sudo ss -tlnp | grep 6514
   ```

3. ファイアウォール設定を確認

4. ログファイルの権限を確認：
   ```bash
   ls -la /var/log/telegram-crawler/
   ```

5. rsyslog/syslog-ngのログを確認：
   ```bash
   sudo journalctl -u rsyslog -f
   # または
   sudo journalctl -u syslog-ng -f
   ```
