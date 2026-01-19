# jsonl-over-syslog

JSONL（JSON Lines）形式のデータをログ集約用サーバにsyslog経由で送信するツールです。

## 機能

- JSONLファイルの各行をRFC 5424形式のsyslogメッセージとして送信
- UDP/TCP/TLSプロトコルに対応
- 日付ベースで新規ファイルを自動検出・処理
- .envファイルによる設定管理

## インストール

Python 3.6以上が必要です（標準ライブラリのみ使用）。

```bash
chmod +x jsonl_to_syslog.py
```

## 使用方法

### 基本的な使い方

```bash
# ファイルを送信
python3 jsonl_to_syslog.py data.jsonl

# リモートサーバに送信
python3 jsonl_to_syslog.py data.jsonl --host logs.example.com --port 5140

# TLSで送信
python3 jsonl_to_syslog.py data.jsonl --host logs.example.com --port 6514 --protocol tls --ca-cert /etc/ssl/certs/ca.crt

# ディレクトリを指定して、前回実行以降に作成されたファイルを自動処理
python3 jsonl_to_syslog.py --dir /path/to/output

# 標準入力から読み込み
cat data.jsonl | python3 jsonl_to_syslog.py -
```

### .envファイルによる設定

プロジェクトルートに`.env`ファイルを作成：

```bash
SYSLOG_HOST=logs.example.com
SYSLOG_PORT=6514
SYSLOG_PROTOCOL=tls
SYSLOG_CA_CERT=/etc/ssl/certs/ca.crt
SYSLOG_APP_NAME=telegram-crawler
```

## コマンドラインオプション

| オプション | 説明 | デフォルト |
|---------|------|---------|
| `--host` | syslogサーバのホスト名 | localhost |
| `--port` | syslogサーバのポート番号 | 5140 (TCP/UDP), 6514 (TLS) |
| `--protocol` | プロトコル (udp, tcp, tls) | tcp |
| `--dir` | ディレクトリパス（前回実行以降のファイルを自動処理） | - |
| `--state-file` | 状態ファイルのパス | .last_run |
| `--ca-cert` | CA証明書ファイルのパス（TLS用） | - |
| `--app-name` | アプリケーション名 | jsonl-over-syslog |

詳細は `python3 jsonl_to_syslog.py --help` を参照してください。

## TLS設定

TLSを使用する場合、CA証明書を指定します（通常はクライアント証明書は不要）：

```bash
python3 jsonl_to_syslog.py data.jsonl --protocol tls --ca-cert /etc/ssl/certs/ca.crt
```

## telegram-crawlerとの連携

[telegram-crawler](https://github.com/Yuki0x80/telegram-crawler)が出力するJSONLファイルをsyslog経由で送信できます。

systemdサービスとして実行する場合は、[telegram-crawler-syslogd](https://github.com/Yuki0x80/telegram-crawler-syslogd)を参照してください。

## Cronでの定期実行

```bash
# crontabを編集
crontab -e

# 30分ごとに実行
*/30 * * * * /usr/bin/python3 /path/to/jsonl_to_syslog.py --dir /path/to/output --state-file /var/lib/jsonl-over-syslog/.last_run
```

## ライセンス

MIT License
