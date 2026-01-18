# デプロイメント

このディレクトリには、Infrastructure as Code（IaC）的な観点でのデプロイメント関連ファイルが含まれています。

## ファイル一覧

- `systemd/`: systemdサービスファイル
  - `telegram-crawler.service`: telegram-crawler実行＋syslog送信サービス（ラッパースクリプト使用）
  - `telegram-crawler.timer`: telegram-crawler定期実行用タイマー（10分ごと）
- `install.sh`: インストールスクリプト
- `telegram-crawler-wrapper.sh`: telegram-crawler実行後に自動送信するラッパースクリプト

## telegram-crawlerとの統合

### 方法1: systemdサービスを使用（推奨）

telegram-crawlerをsystemdサービスとして実行し、処理完了直後に自動送信：

```bash
# インストールスクリプトを実行（telegram-crawlerサービスもインストール）
sudo ./deploy/install.sh

# telegram-crawlerサービスを有効化（10分ごとに実行）
sudo systemctl enable --now telegram-crawler.timer

# 状態を確認
sudo systemctl status telegram-crawler.timer

# ログを確認
sudo journalctl -u telegram-crawler.service -f
```

この方法では：
1. telegram-crawlerが10分ごとに自動実行される
2. 処理完了後、最新のJSONLファイルが自動的にsyslog経由で送信される
3. systemdでログ管理が可能

### 方法2: ラッパースクリプトを直接実行

手動で実行する場合：

```bash
# ラッパースクリプトを実行
./deploy/telegram-crawler-wrapper.sh [telegram-crawlerの引数]

# 例
./deploy/telegram-crawler-wrapper.sh --channel example_channel
```

このスクリプトは：
1. telegram-crawlerを実行
2. 処理完了後、最新のJSONLファイルを自動的にsyslog経由で送信

### ラッパースクリプトの設定

環境変数でカスタマイズ可能：

```bash
export TELEGRAM_CRAWLER_DIR=/opt/telegram-crawler
export TELEGRAM_CRAWLER_SCRIPT=telegram_crawler.py
export OUTPUT_DIR=/opt/telegram-crawler/output
export JSONL_TO_SYSLOG=/opt/telegram-crawler/jsonl_to_syslog.py
export STATE_FILE=/var/lib/jsonl-over-syslog/.last_run

./deploy/telegram-crawler-wrapper.sh
```

## 使用方法

### 方法1: インストールスクリプトを使用（推奨）

```bash
# インストールスクリプトを実行
sudo ./deploy/install.sh

# カスタムインストールディレクトリを指定
sudo INSTALL_DIR=/opt/custom/path ./deploy/install.sh
```

### 方法2: 手動インストール

#### systemdサービスを使用する場合

```bash
# 1. サービスファイルをコピー
sudo cp deploy/systemd/telegram-crawler.service /etc/systemd/system/
sudo cp deploy/systemd/telegram-crawler.timer /etc/systemd/system/

# 2. パスを編集（必要に応じて）
sudo nano /etc/systemd/system/telegram-crawler.service

# 3. systemdをリロード
sudo systemctl daemon-reload

# 4. タイマーを有効化（10分ごとに実行）
sudo systemctl enable --now telegram-crawler.timer

# 5. 状態を確認
sudo systemctl status telegram-crawler.timer
```

#### Cronを使用する場合

README.mdの「Cronでの定期実行」セクションを参照してください。

## systemd vs Cron

### systemdのメリット

- ログ管理が容易（`journalctl`で確認可能）
- 依存関係の管理が可能（ネットワーク起動後など）
- サービスとして管理できる
- エラー時の自動再試行設定が可能

### Cronのメリット

- シンプルで軽量
- 既存のCron環境でそのまま使用可能
- 細かいスケジュール設定が容易

## 設定

### 環境変数ファイル（.env）

インストール後、`.env`ファイルを作成して設定してください：

```bash
sudo nano /opt/telegram-crawler/.env
```

設定例は`README.md`を参照してください。

### サービスファイルのカスタマイズ

`/etc/systemd/system/telegram-crawler.service`を編集して、以下をカスタマイズできます：

- `User`: 実行ユーザー
- `WorkingDirectory`: 作業ディレクトリ
- `ExecStart`: ラッパースクリプトのパス（デフォルト: `/opt/telegram-crawler/deploy/telegram-crawler-wrapper.sh`）
- `EnvironmentFile`: 環境変数ファイルのパス

**注意**: telegram-crawlerに引数を渡す場合は、`ExecStart`を編集してください：

```ini
ExecStart=/opt/telegram-crawler/deploy/telegram-crawler-wrapper.sh --channel example_channel
```

**実行間隔の変更**: タイマーの実行間隔を変更する場合は、`/etc/systemd/system/telegram-crawler.timer`を編集：

```ini
[Timer]
OnCalendar=*:0/10  # 10分ごと（変更する場合はこの値を変更）
```

## トラブルシューティング

### ログの確認

```bash
# systemdサービスのログを確認
sudo journalctl -u telegram-crawler.service -f

# タイマーの状態を確認
sudo systemctl status telegram-crawler.timer
```

### 手動実行

```bash
# サービスを手動で実行
sudo systemctl start telegram-crawler.service

# 実行結果を確認
sudo journalctl -u telegram-crawler.service
```
