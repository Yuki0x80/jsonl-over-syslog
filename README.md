# jsonl-over-syslog

JSONL（JSON Lines）形式のデータをログ集約用サーバにsyslog経由で送信するツールです。

このツールは、Cronなどで定期実行することを想定して設計されています。日付ベースで新規ファイルを自動的に検出・処理する機能により、継続的なログ送信が可能です。

## 機能

- JSONLファイルの各行をRFC 5424形式のsyslogメッセージとして送信
- UDP/TCP/TLSプロトコルに対応
- TLS接続時の証明書検証に対応（CA証明書、クライアント証明書）
- 標準入力からの読み込みに対応
- Structured Data形式でJSONデータを送信
- .envファイルによる設定管理に対応

## インストール

このツールはPython 3.6以上で動作します。追加の依存関係は必要ありません（標準ライブラリのみを使用）。

```bash
# 実行権限を付与
chmod +x jsonl_to_syslog.py
```

## 使用方法

### 環境変数ファイル（.env）による設定

プログラムに設定を直接書かずに、`.env`ファイルで設定できます。プロジェクトルートに`.env`ファイルを作成し、以下のように設定してください：

```bash
# .envファイルの例
SYSLOG_HOST=logs.example.com
SYSLOG_PORT=5140
SYSLOG_PROTOCOL=tcp

# TLS設定（オプション）
# SYSLOG_CA_CERT=ca.crt
# SYSLOG_CLIENT_CERT=client.crt
# SYSLOG_CLIENT_KEY=client.key
# SYSLOG_NO_VERIFY=false

# その他の設定（オプション）
# SYSLOG_FACILITY=16          # syslog facility (0-23, デフォルト: 16 = local0)
# SYSLOG_SEVERITY=6           # syslog severity (0-7, デフォルト: 6 = informational)
# SYSLOG_APP_NAME=jsonl-over-syslog  # アプリケーション名
# SYSLOG_DELAY=0.0            # 各行送信間の遅延（秒）
```

環境変数はコマンドライン引数より優先度が低く、コマンドライン引数で上書きできます。

### 基本的な使い方

```bash
# ローカルのsyslogサーバにTCPで送信（デフォルト: ポート5140）
python jsonl_to_syslog.py data.jsonl

# リモートサーバに送信
python jsonl_to_syslog.py data.jsonl --host logs.example.com --port 5140

# UDPプロトコルを使用
python jsonl_to_syslog.py data.jsonl --host logs.example.com --port 514 --protocol udp

# TLSで送信（CA証明書を使用してサーバ証明書を検証）
python jsonl_to_syslog.py data.jsonl --host logs.example.com --port 6514 --protocol tls --ca-cert ca.crt

# TLSで送信（クライアント証明書も使用）
python jsonl_to_syslog.py data.jsonl --host logs.example.com --port 6514 --protocol tls --ca-cert ca.crt --client-cert client.crt --client-key client.key

# 標準入力から読み込み
cat data.jsonl | python jsonl_to_syslog.py -

# telegram-crawlerの出力ファイルを送信
python jsonl_to_syslog.py /Users/yuki/Desktop/git_code/telegram-crawler/output/20260118_053532_telegram_messages.jsonl

# ワイルドカードを使用して複数ファイルを送信（シェルで展開）
python jsonl_to_syslog.py /Users/yuki/Desktop/git_code/telegram-crawler/output/*.jsonl

# ディレクトリを指定して、前回実行以降に作成されたファイルを自動的に処理（日付ベース）
python jsonl_to_syslog.py --dir /Users/yuki/Desktop/git_code/telegram-crawler/output

# 状態ファイルのパスを指定
python jsonl_to_syslog.py --dir /Users/yuki/Desktop/git_code/telegram-crawler/output --state-file /tmp/.last_run
```

### オプション

- `--host`: syslogサーバのホスト名（デフォルト: localhost、環境変数: `SYSLOG_HOST`）
- `--port`: syslogサーバのポート番号（デフォルト: 5140、環境変数: `SYSLOG_PORT`）
- `--protocol`: プロトコル（udp、tcp、または tls、デフォルト: tcp、環境変数: `SYSLOG_PROTOCOL`）
- `--facility`: syslog facility（0-23、デフォルト: 16 = local0、環境変数: `SYSLOG_FACILITY`）
- `--severity`: syslog severity（0-7、デフォルト: 6 = informational、環境変数: `SYSLOG_SEVERITY`）
- `--app-name`: アプリケーション名（デフォルト: jsonl-over-syslog、環境変数: `SYSLOG_APP_NAME`）
- `--delay`: 各行送信間の遅延（秒、デフォルト: 0.0、環境変数: `SYSLOG_DELAY`）
- `--ca-cert`: CA証明書ファイルのパス（TLS用、環境変数: `SYSLOG_CA_CERT`）
- `--client-cert`: クライアント証明書ファイルのパス（TLS用、環境変数: `SYSLOG_CLIENT_CERT`）
- `--client-key`: クライアント秘密鍵ファイルのパス（TLS用、環境変数: `SYSLOG_CLIENT_KEY`）
- `--no-verify`: 証明書検証を無効化（TLS用、非推奨、環境変数: `SYSLOG_NO_VERIFY`）
- `--dir`: ディレクトリパス（指定すると、前回実行以降に作成されたJSONLファイルを自動的に処理）
- `--state-file`: 状態ファイルのパス（前回処理日時を記録、デフォルト: `.last_run`）
- `--pattern`: ファイル名のパターン（`--dir`使用時、デフォルト: `*.jsonl`）

**注意**: このツールはログ出力を行いません。JSONLデータをsyslogサーバに送信するだけです。

### 使用例

```bash
# .envファイルの設定を使用して送信
python jsonl_to_syslog.py data.jsonl

# 送信間隔を0.1秒に設定
python jsonl_to_syslog.py data.jsonl --delay 0.1

# カスタムアプリケーション名とseverityを指定
python jsonl_to_syslog.py data.jsonl --app-name myapp --severity 4

# TLSで送信（証明書検証を無効化、非推奨）
python jsonl_to_syslog.py data.jsonl --host logs.example.com --port 6514 --protocol tls --no-verify
```

### TLS接続について

TLSプロトコルを使用する場合、以下の証明書オプションが利用できます：

- **CA証明書（`--ca-cert`）**: ログ集約サーバの証明書を検証するために使用します。サーバから提供されたCA証明書ファイルを指定してください。
- **クライアント証明書（`--client-cert`、`--client-key`）**: サーバがクライアント認証を要求する場合に使用します。両方を指定する必要があります。
- **証明書検証の無効化（`--no-verify`）**: 開発・テスト環境でのみ使用してください。本番環境では使用しないことを強く推奨します。

一般的なsyslog over TLSのポート番号は6514です（RFC 5425で推奨）。

## JSONLファイル形式

JSONLファイルは各行が独立したJSONオブジェクトである必要があります：

```json
{"timestamp": "2024-01-01T00:00:00Z", "level": "info", "message": "Hello"}
{"timestamp": "2024-01-01T00:00:01Z", "level": "error", "message": "Error occurred"}
{"timestamp": "2024-01-01T00:00:02Z", "level": "debug", "message": "Debug info"}
```

複雑なネストしたJSON構造（オブジェクトや配列を含む）も正しく送信されます：

```json
{"channel_name": "example", "message_id": 123, "from_id": {"peerUser": 123456}, "sender_user": {"user_id": 123456, "username": "user"}}
```

## telegram-crawlerとの連携

[telegram-crawler](https://github.com/Yuki0x80/telegram-crawler)が出力するJSONLファイルをsyslog経由で送信できます：

```bash
# telegram-crawlerの出力ファイルを直接送信
python jsonl_to_syslog.py /path/to/telegram-crawler/output/20260118_053532_telegram_messages.jsonl

# 複数のファイルを送信（シェルで展開）
python jsonl_to_syslog.py /path/to/telegram-crawler/output/*.jsonl

# ディレクトリを指定して、前回実行以降に作成されたファイルを自動的に処理（推奨）
# 初回実行時は、ディレクトリ内のすべてのJSONLファイルを処理
# 2回目以降は、前回実行以降に作成されたファイルのみを処理
python jsonl_to_syslog.py --dir /path/to/telegram-crawler/output

# 状態ファイルのパスを指定（デフォルト: .last_run）
python jsonl_to_syslog.py --dir /path/to/telegram-crawler/output --state-file /tmp/.last_run

# .envファイルで設定済みの場合
python jsonl_to_syslog.py --dir /path/to/telegram-crawler/output
```

telegram-crawlerが出力する複雑なJSON構造（`from_id`、`sender_user`などのネストしたオブジェクト）も、データ破損なく正しく送信されます。

### telegram-crawlerの出力ファイル形式

telegram-crawlerは以下のような形式でJSONLファイルを出力します：
- ファイル名: `YYYYMMDD_HHMMSS_telegram_messages.jsonl`
- 各行が独立したJSONオブジェクト
- 複雑なネストした構造を含むJSONも正しく処理されます

### 日付ベースの自動処理

`--dir`オプションを使用すると、以下の動作になります：

1. **初回実行**: ディレクトリ内のすべてのJSONLファイルを処理し、最新のファイル作成日時を記録
2. **2回目以降**: 前回実行以降に作成されたファイルのみを処理し、最新の日時を更新
3. **状態ファイル**: `.last_run`（または`--state-file`で指定したパス）に前回処理日時を記録

これにより、cronなどで定期実行する際に、新しく作成されたファイルのみを効率的に処理できます。

### Ubuntu環境での使用

このツールはPython標準ライブラリのみを使用しているため、Ubuntu環境で追加のパッケージインストールは不要です：

```bash
# Python 3.6以上が必要
python3 --version

# 実行権限を付与
chmod +x jsonl_to_syslog.py
```

### Cronでの定期実行

このツールは、Cronなどで定期実行することを想定して設計されています。`--dir`オプションを使用することで、前回実行以降に作成されたファイルのみを自動的に処理できます。

#### Cron設定例

```bash
# crontabを編集
crontab -e

# 毎時実行（0分に実行）
0 * * * * /usr/bin/python3 /path/to/jsonl_to_syslog.py --dir /path/to/telegram-crawler/output

# 30分ごとに実行
*/30 * * * * /usr/bin/python3 /path/to/jsonl_to_syslog.py --dir /path/to/telegram-crawler/output

# 毎日午前2時に実行
0 2 * * * /usr/bin/python3 /path/to/jsonl_to_syslog.py --dir /path/to/telegram-crawler/output

# 状態ファイルのパスを指定して実行
0 * * * * /usr/bin/python3 /path/to/jsonl_to_syslog.py --dir /path/to/output --state-file /var/lib/jsonl-over-syslog/.last_run
```

#### Cron実行時の注意点

- **状態ファイルのパス**: デフォルトでは`.last_run`がカレントディレクトリに作成されます。Cron実行時は絶対パスを指定することを推奨します
- **環境変数**: Cron実行時は環境変数が限定的なため、`.env`ファイルを使用するか、Cron設定で環境変数を明示的に設定してください
- **ログ出力**: このツールはログ出力を行いません。エラー確認が必要な場合は、標準エラー出力をリダイレクトしてください：
  ```bash
  0 * * * * /usr/bin/python3 /path/to/jsonl_to_syslog.py --dir /path/to/output >> /var/log/jsonl-over-syslog.log 2>&1
  ```

## syslogメッセージ形式

このツールはRFC 5424形式のsyslogメッセージを送信します。JSONデータはStructured Data形式で送信され、メッセージ部分にはJSON文字列が含まれます。

## ライセンス

MIT License
