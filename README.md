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
# Python 3がインストールされているか確認
python3 --version

# 実行権限を付与
chmod +x jsonl_to_syslog.py
chmod +x test_send_logs.sh  # テストスクリプトにも実行権限を付与
```

**注意**: Ubuntu 20.04以降では、`python`コマンドがデフォルトでインストールされていません。以下のいずれかの方法で対応してください：

1. **`python3`コマンドを使用**（推奨）:
   ```bash
   python3 jsonl_to_syslog.py data.jsonl
   ```

2. **`python-is-python3`パッケージをインストール**（`python`コマンドを使いたい場合）:
   ```bash
   sudo apt update
   sudo apt install python-is-python3
   ```
   これにより、`python`コマンドが`python3`を指すようになります。

## 使用方法

### 環境変数ファイル（.env）による設定

プログラムに設定を直接書かずに、`.env`ファイルで設定できます。プロジェクトルートに`.env`ファイルを作成し、以下のように設定してください：

```bash
# .envファイルの例
SYSLOG_HOST=logs.example.com
SYSLOG_PORT=5140
SYSLOG_PROTOCOL=tcp

# TLS設定（オプション）
# SYSLOG_CA_CERT=/etc/ssl/certs/ca.crt          # CA証明書のパス（推奨: /etc/ssl/certs/）
# SYSLOG_CLIENT_CERT=/etc/ssl/certs/client.crt  # クライアント証明書のパス
# SYSLOG_CLIENT_KEY=/etc/ssl/private/client.key  # クライアント秘密鍵のパス（推奨: /etc/ssl/private/）
# SYSLOG_NO_VERIFY=false

# その他の設定（オプション）
# SYSLOG_FACILITY=16          # syslog facility (0-23, デフォルト: 16 = local0)
# SYSLOG_SEVERITY=6           # syslog severity (0-7, デフォルト: 6 = informational)
# SYSLOG_APP_NAME=jsonl-over-syslog  # アプリケーション名
# SYSLOG_DELAY=0.0            # 各行送信間の遅延（秒）
```

環境変数はコマンドライン引数より優先度が低く、コマンドライン引数で上書きできます。

### テストスクリプトの使用方法

ログ送信をテストするためのスクリプト `test_send_logs.sh` が用意されています。

```bash
# テストスクリプトを実行
./test_send_logs.sh
```

このスクリプトは以下を実行します：
1. テスト用のJSONLファイルを作成
2. `.env`ファイルから設定を読み込み（存在する場合）
3. ログを送信
4. 送信結果を表示
5. サーバ側での確認方法を表示

**事前準備**:
- `.env`ファイルを作成して設定を記述（オプション、デフォルト値で動作）
- TLSを使用する場合、CA証明書のパスを`.env`に設定

**実行例**:
```bash
# .envファイルがある場合
./test_send_logs.sh

# .envファイルがない場合（デフォルト設定で動作）
./test_send_logs.sh
```

### 基本的な使い方

```bash
# ローカルのsyslogサーバにTCPで送信（デフォルト: ポート5140）
python3 jsonl_to_syslog.py data.jsonl

# リモートサーバに送信
python3 jsonl_to_syslog.py data.jsonl --host logs.example.com --port 5140

# UDPプロトコルを使用
python3 jsonl_to_syslog.py data.jsonl --host logs.example.com --port 514 --protocol udp

# TLSで送信（CA証明書を使用してサーバ証明書を検証）
python3 jsonl_to_syslog.py data.jsonl --host logs.example.com --port 6514 --protocol tls --ca-cert ca.crt

# TLSで送信（クライアント証明書も使用）
python3 jsonl_to_syslog.py data.jsonl --host logs.example.com --port 6514 --protocol tls --ca-cert ca.crt --client-cert client.crt --client-key client.key

# 標準入力から読み込み
cat data.jsonl | python3 jsonl_to_syslog.py -

# telegram-crawlerの出力ファイルを送信
python3 jsonl_to_syslog.py /path/to/telegram-crawler/output/20260118_053532_telegram_messages.jsonl

# ワイルドカードを使用して複数ファイルを送信（シェルで展開）
python3 jsonl_to_syslog.py /path/to/telegram-crawler/output/*.jsonl

# ディレクトリを指定して、前回実行以降に作成されたファイルを自動的に処理（日付ベース）
python3 jsonl_to_syslog.py --dir /path/to/telegram-crawler/output

# 状態ファイルのパスを指定
python3 jsonl_to_syslog.py --dir /path/to/telegram-crawler/output --state-file /tmp/.last_run
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
python3 jsonl_to_syslog.py data.jsonl --host logs.example.com --port 6514 --protocol tls --no-verify
```

### TLS接続について

TLSプロトコルを使用する場合、以下の証明書オプションが利用できます：

- **CA証明書（`--ca-cert`）**: ログ集約サーバの証明書を検証するために使用します。サーバから提供されたCA証明書ファイルを指定してください。**通常はこれだけで十分です。**
- **クライアント証明書（`--client-cert`、`--client-key`）**: サーバがクライアント認証を要求する場合のみ使用します。両方を指定する必要があります。**通常は不要です。**
- **証明書検証の無効化（`--no-verify`）**: 開発・テスト環境でのみ使用してください。本番環境では使用しないことを強く推奨します。

**一般的な使用方法（クライアント証明書不要）**:
```bash
# CA証明書のみで送信（推奨）
python3 jsonl_to_syslog.py data.jsonl --host logs.example.com --port 6514 --protocol tls --ca-cert /etc/ssl/certs/ca.crt
```

**ポート番号**: 
- **TCP/UDP**: デフォルトは5140です
- **TLS**: 6514（RFC 5425推奨）を使用してください

#### 証明書ファイルの配置場所（Ubuntuサーバ）

**サーバ側（rsyslog）**:
- CA証明書: `/etc/rsyslog/tls/ca.crt`
- サーバ証明書: `/etc/rsyslog/tls/server.crt`
- サーバ秘密鍵: `/etc/rsyslog/tls/server.key`

**クライアント側（jsonl_to_syslog.py）**:
- **推奨場所**（CA証明書のみ、クライアント証明書不要）:
  - CA証明書: `/etc/ssl/certs/ca.crt` または `/usr/local/share/ca-certificates/ca.crt`

- **その他の選択肢**:
  - プロジェクトディレクトリ内: `./certs/ca.crt`（相対パス）
  - ユーザーディレクトリ: `~/certs/ca.crt`
  - 任意の場所: `.env`ファイルで絶対パスを指定

**証明書ファイルの配置例**:
```bash
# サーバ側
sudo mkdir -p /etc/rsyslog/tls
sudo cp ca.crt /etc/rsyslog/tls/
sudo cp server.crt /etc/rsyslog/tls/
sudo cp server.key /etc/rsyslog/tls/
sudo chmod 600 /etc/rsyslog/tls/server.key
sudo chown root:root /etc/rsyslog/tls/*

# クライアント側（CA証明書のみ、推奨）
sudo mkdir -p /etc/ssl/certs
sudo cp ca.crt /etc/ssl/certs/
sudo chmod 644 /etc/ssl/certs/ca.crt
sudo chown root:root /etc/ssl/certs/ca.crt

# .envファイルの設定例（クライアント証明書不要）
SYSLOG_CA_CERT=/etc/ssl/certs/ca.crt
# SYSLOG_CLIENT_CERT と SYSLOG_CLIENT_KEY は指定不要（コメントアウトまたは削除）
```

**注意**: クライアント証明書は、サーバがクライアント認証を要求する場合のみ必要です。通常はCA証明書のみで送信できます。

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

### 方法1: 処理完了直後に自動送信（推奨）

telegram-crawlerの処理完了直後に自動的に送信するラッパースクリプトを使用：

```bash
# ラッパースクリプトを使用（telegram-crawler実行後、自動的に送信）
./deploy/telegram-crawler-wrapper.sh [telegram-crawlerの引数]

# 例: telegram-crawlerの通常の実行方法をそのまま使用
./deploy/telegram-crawler-wrapper.sh --channel example_channel
```

この方法では、telegram-crawlerの処理が完了した直後に、最新のJSONLファイルが自動的に送信されます。

### 方法2: 手動で送信

```bash
# telegram-crawlerの出力ファイルを直接送信
python3 jsonl_to_syslog.py /path/to/telegram-crawler/output/20260118_053532_telegram_messages.jsonl

# 複数のファイルを送信（シェルで展開）
python3 jsonl_to_syslog.py /path/to/telegram-crawler/output/*.jsonl

# ディレクトリを指定して、前回実行以降に作成されたファイルを自動的に処理（推奨）
# 初回実行時は、ディレクトリ内のすべてのJSONLファイルを処理
# 2回目以降は、前回実行以降に作成されたファイルのみを処理
python3 jsonl_to_syslog.py --dir /path/to/telegram-crawler/output

# 状態ファイルのパスを指定（デフォルト: .last_run）
python3 jsonl_to_syslog.py --dir /path/to/telegram-crawler/output --state-file /tmp/.last_run

# .envファイルで設定済みの場合
python3 jsonl_to_syslog.py --dir /path/to/telegram-crawler/output
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

### デプロイメント方法

#### 方法1: systemdサービスを使用（推奨）

Infrastructure as Code（IaC）的な観点から、systemdサービスファイルが用意されています：

```bash
# インストールスクリプトを実行
sudo ./deploy/install.sh

# telegram-crawlerサービスを有効化（10分ごとに実行）
sudo systemctl enable --now telegram-crawler.timer

# 状態を確認
sudo systemctl status telegram-crawler.timer
```

このサービスは、telegram-crawler実行後に自動的にsyslog送信を行います。

詳細は`deploy/README.md`を参照してください。

#### 方法2: Cronを使用

Cronでの定期実行も可能です。`--dir`オプションを使用することで、前回実行以降に作成されたファイルのみを自動的に処理できます。

##### Cron設定例

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
