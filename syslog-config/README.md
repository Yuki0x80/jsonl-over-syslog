# Syslogサーバ設定ファイル

このディレクトリには、rsyslogサーバ側の設定ファイル例が含まれています。

## ファイル一覧

- `rsyslog.conf.example`: rsyslog用の設定ファイル例

## 使用方法

0. **rsyslog-gnutlsパッケージをインストール**（TLSを使用する場合）：
   ```bash
   sudo apt update
   sudo apt install rsyslog-gnutls
   ```
   これにより`gtls`モジュールが利用可能になります。

1. 設定ファイルをコピー：
   ```bash
   sudo cp syslog-config/rsyslog.conf.example /etc/rsyslog.d/99-telegram-crawler.conf
   ```

2. **設定ファイルの確認と調整**：
   - 他の設定ファイル（例: `01-tls.conf`）で既に`global()`ブロックでTLS設定がされている場合、`99-telegram-crawler.conf`内の`global()`ブロックはコメントアウトされています（そのままで問題ありません）
   - `imtcp`モジュールが既にロードされている場合、`module(load="imtcp")`の行もコメントアウトされています（そのままで問題ありません）
   - このファイルを独立して使用する場合は、コメントアウトされている`global()`ブロックを有効化してください

3. TLS証明書を設定：
   - CA証明書: `/etc/rsyslog/tls/ca.crt`
   - サーバ証明書: `/etc/rsyslog/tls/server.crt`
   - サーバ秘密鍵: `/etc/rsyslog/tls/server.key`
   - 証明書ファイルを配置してください：
     ```bash
     sudo mkdir -p /etc/rsyslog/tls
     sudo cp ca.crt /etc/rsyslog/tls/
     sudo cp server.crt /etc/rsyslog/tls/
     sudo cp server.key /etc/rsyslog/tls/
     sudo chmod 600 /etc/rsyslog/tls/server.key
     sudo chown root:root /etc/rsyslog/tls/*
     ```

4. ログディレクトリを作成：
   ```bash
   sudo mkdir -p /srv/logs/telegram-crawler
   sudo chown syslog:syslog /srv/logs/telegram-crawler
   ```

5. rsyslogを再起動：
   ```bash
   sudo systemctl restart rsyslog
   ```

6. 設定を確認：
   ```bash
   sudo systemctl status rsyslog
   sudo tail -f /srv/logs/telegram-crawler/telegram-crawler-*.jsonl
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
sudo tail -f /srv/logs/telegram-crawler/telegram-crawler-*.jsonl
```

## ポート番号

この設定は**TLS通信を前提**としており、以下のポート番号を使用します：

- **TLS**: 6514（RFC 5425推奨、デフォルト）

ポート番号は、`jsonl_to_syslog.py`の`--port`オプションまたは`.env`ファイルの`SYSLOG_PORT`で変更できます。

## ログファイルの保存先

設定例では、**カスタムテンプレートを使用してJSONL形式で保存**します：

- `/srv/logs/telegram-crawler/telegram-crawler-YYYY-MM-DD.jsonl`: 日付ごとのJSONLファイル（推奨）
  - メッセージ部分（JSON文字列）のみを抽出して保存
  - 元のJSONLファイルと同じ形式で保存されるため、後でJSONLとして処理しやすい

### カスタムテンプレート vs 標準テンプレート

**カスタムテンプレート（推奨）**:
- メッセージ部分（JSON文字列）のみを抽出
- 元のJSONLファイルと同じ形式
- JSONLとして処理しやすい
- ファイル拡張子: `.jsonl`

**標準テンプレート**:
- syslogヘッダー（タイムスタンプ、ホスト名など）も含む
- メタデータが必要な場合に使用
- ファイル拡張子: `.log`

必要に応じて、設定ファイルを編集して保存先やテンプレートを変更してください。

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

### 設定エラーが発生する場合

1. **rsyslog v8対応**: この設定ファイルはrsyslog v8のRainerScript構文を使用しています
2. **global()ブロックの重複**: 他の設定ファイルで既に`global()`でTLS設定がされている場合、このファイル内の`global()`ブロックはコメントアウトしてください
3. **imtcpモジュールの重複ロード**: `module 'imtcp' already in this config`エラーが出る場合、`module(load="imtcp")`の行をコメントアウトしてください
4. **rulesetの定義順序**: `ruleset`は`input`より前に定義する必要があります（設定ファイル内で既に正しい順序になっています）

### ログが受信されない場合

1. rsyslogが正しく起動しているか確認：
   ```bash
   sudo systemctl status rsyslog
   ```

2. 設定ファイルの構文チェック：
   ```bash
   sudo rsyslogd -N1
   ```

3. ポートが開いているか確認：
   ```bash
   sudo netstat -tlnp | grep 6514
   # または
   sudo ss -tlnp | grep 6514
   ```

4. ファイアウォール設定を確認

5. ログファイルの権限を確認：
   ```bash
   ls -la /srv/logs/telegram-crawler/
   ```

6. rsyslogのログを確認：
   ```bash
   sudo journalctl -u rsyslog -f
   ```
