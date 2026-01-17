#!/usr/bin/env python3
"""
JSONLファイルの各行をsyslog経由で送信するツール
RFC 5424形式のsyslogメッセージを送信します
"""

import argparse
import json
import os
import socket
import ssl
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List


class SyslogSender:
    """
    RFC 5424形式のsyslogメッセージを送信するクラス
    
    UDP、TCP、TLSプロトコルに対応しており、syslogサーバにメッセージを送信します。
    TLS接続時は証明書検証とクライアント認証にも対応しています。
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5140,
        protocol: str = "tcp",
        facility: int = 16,  # local0
        severity: int = 6,   # informational
        app_name: str = "jsonl-over-syslog",
        msgid: str = "-",
        ca_cert: Optional[str] = None,
        client_cert: Optional[str] = None,
        client_key: Optional[str] = None,
        verify: bool = True
    ):
        """
        SyslogSenderを初期化し、syslogサーバへの接続を確立します
        
        Args:
            host: syslogサーバのホスト名（デフォルト: localhost）
            port: syslogサーバのポート番号（デフォルト: 5140）
            protocol: プロトコル（"udp"、"tcp"、または"tls"、デフォルト: tcp）
            facility: syslog facility（0-23、デフォルト: 16 = local0）
            severity: syslog severity（0-7、デフォルト: 6 = informational）
            app_name: アプリケーション名（デフォルト: jsonl-over-syslog）
            msgid: メッセージID（デフォルト: "-"）
            ca_cert: CA証明書ファイルのパス（TLS用、オプション）
            client_cert: クライアント証明書ファイルのパス（TLS用、オプション）
            client_key: クライアント秘密鍵ファイルのパス（TLS用、オプション）
            verify: 証明書検証を有効にするか（デフォルト: True）
        """
        self.host = host
        self.port = port
        self.protocol = protocol.lower()
        self.facility = facility
        self.severity = severity
        self.app_name = app_name
        self.msgid = msgid
        self.ca_cert = ca_cert
        self.client_cert = client_cert
        self.client_key = client_key
        self.verify = verify
        
        try:
            if self.protocol == "tls":
                # TLS接続を確立
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                context = ssl.create_default_context()
                
                # CA証明書を設定
                if self.ca_cert:
                    # 指定されたCA証明書を使用
                    if not Path(self.ca_cert).exists():
                        raise FileNotFoundError(f"CA証明書ファイルが見つかりません: {self.ca_cert}")
                    context.load_verify_locations(self.ca_cert)
                elif not self.verify:
                    # 証明書検証を無効化（--no-verifyが指定された場合）
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                # CA証明書が指定されていないがverifyがTrueの場合は、
                # create_default_context()がシステムのデフォルトCA証明書を使用する
                
                # クライアント証明書を設定
                if self.client_cert and self.client_key:
                    if not Path(self.client_cert).exists():
                        raise FileNotFoundError(f"クライアント証明書ファイルが見つかりません: {self.client_cert}")
                    if not Path(self.client_key).exists():
                        raise FileNotFoundError(f"クライアント秘密鍵ファイルが見つかりません: {self.client_key}")
                    context.load_cert_chain(self.client_cert, self.client_key)
                elif self.client_cert or self.client_key:
                    # 片方だけ指定されている場合はエラー
                    raise ValueError("クライアント証明書と秘密鍵は両方指定する必要があります")
                
                # 接続後にTLSでラップ
                sock.connect((self.host, self.port))
                self.sock = context.wrap_socket(sock, server_hostname=self.host)
            elif self.protocol == "tcp":
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))
            else:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except (socket.error, ssl.SSLError, OSError) as e:
            raise ConnectionError(f"syslogサーバへの接続に失敗しました ({self.host}:{self.port}): {e}")
    
    def _format_syslog_message(self, message: str, structured_data: Optional[str] = None) -> bytes:
        """
        RFC 5424形式のsyslogメッセージを生成
        
        RFC 5424に準拠したsyslogメッセージフォーマットでメッセージを生成します。
        各メッセージには優先度、タイムスタンプ、ホスト名、アプリケーション名などの
        メタデータが含まれます。
        
        Args:
            message: 送信するメッセージ本文
            structured_data: 構造化データ（オプション、RFC 5424形式）
            
        Returns:
            RFC 5424形式のsyslogメッセージ（UTF-8エンコードされたバイト列）
            
        Format: <PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID [STRUCTURED-DATA] MSG
        """
        # Priority = (Facility * 8) + Severity
        priority = (self.facility * 8) + self.severity
        
        # Version
        version = "1"
        
        # Timestamp (RFC 3339 format)
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        
        # Hostname
        hostname = socket.gethostname()
        
        # App-name
        app_name = self.app_name
        
        # ProcID (process ID)
        procid = str(os.getpid())
        
        # MSGID
        msgid = self.msgid
        
        # Structured Data (optional)
        if structured_data:
            sd = f"[{structured_data}]"
        else:
            sd = "-"
        
        # Build message
        syslog_msg = (
            f"<{priority}>{version} {timestamp} {hostname} "
            f"{app_name} {procid} {msgid} {sd} {message}"
        )
        
        return syslog_msg.encode('utf-8')
    
    def send(self, message: str, structured_data: Optional[str] = None):
        """
        syslogメッセージを送信
        
        RFC 5424形式のsyslogメッセージを生成し、設定されたプロトコル（UDP/TCP/TLS）
        でsyslogサーバに送信します。
        
        Args:
            message: 送信するメッセージ本文
            structured_data: 構造化データ（オプション、RFC 5424形式）
            
        Raises:
            OSError: 送信に失敗した場合
        """
        msg_bytes = self._format_syslog_message(message, structured_data)
        
        try:
            if self.protocol in ("tcp", "tls"):
                # TCP/TLSの場合は改行を追加（syslog over TCPの一般的な実装）
                msg_bytes += b"\n"
                self.sock.sendall(msg_bytes)
            else:
                # UDPの場合はそのまま送信
                self.sock.sendto(msg_bytes, (self.host, self.port))
        except (socket.error, OSError) as e:
            raise OSError(f"syslogメッセージの送信に失敗しました: {e}")
    
    def send_json(self, json_data: dict, message: Optional[str] = None):
        """
        JSONデータをsyslog経由で送信
        
        JSONデータをJSON文字列に変換し、syslogメッセージのメッセージ部分として送信します。
        複雑なJSON構造（ネストしたオブジェクト、配列など）も破損せずに送信できます。
        
        Args:
            json_data: 送信するJSONデータ（辞書形式）
            message: カスタムメッセージ（指定しない場合、json_dataをJSON文字列化したものを使用）
        """
        # メッセージ部分にJSON文字列をそのまま入れる（データ破損を防ぐ）
        if message:
            msg = message
        else:
            # JSONを文字列として送信（メッセージ部分）
            # ensure_ascii=Falseで日本語などの非ASCII文字もそのまま送信
            msg = json.dumps(json_data, ensure_ascii=False)
        
        # Structured Dataは使わず、メッセージ部分にJSON文字列をそのまま送信
        # これにより、複雑なJSON構造（ネストしたオブジェクト、配列など）も破損せず送信できる
        self.send(msg, structured_data=None)
    
    def close(self):
        """
        ソケット接続を閉じる
        
        syslogサーバへの接続を切断します。使用後は必ずこのメソッドを呼び出してください。
        """
        try:
            self.sock.close()
        except (OSError, AttributeError):
            # ソケットが既に閉じられている、または属性エラーの場合は無視
            pass


def send_jsonl_file(
    file_path: str,
    syslog_host: str = "localhost",
    syslog_port: int = 5140,
    protocol: str = "tcp",
    facility: int = 16,
    severity: int = 6,
    app_name: str = "jsonl-over-syslog",
        delay: float = 0.0,
        verbose: bool = False,  # 未使用（互換性のため残す）
    ca_cert: Optional[str] = None,
    client_cert: Optional[str] = None,
    client_key: Optional[str] = None,
    verify: bool = True
):
    """
    JSONLファイルを読み込んでsyslog経由で送信
    
    Args:
        file_path: JSONLファイルのパス（"-"の場合は標準入力）
        syslog_host: syslogサーバのホスト名
        syslog_port: syslogサーバのポート番号
        protocol: プロトコル（"udp"、"tcp"、または"tls"）
        facility: syslog facility (0-23)
        severity: syslog severity (0-7)
        app_name: アプリケーション名
        delay: 各行送信間の遅延（秒）
        verbose: 詳細出力を有効にする
        ca_cert: CA証明書ファイルのパス（TLS用）
        client_cert: クライアント証明書ファイルのパス（TLS用、オプション）
        client_key: クライアント秘密鍵ファイルのパス（TLS用、オプション）
        verify: 証明書検証を有効にするか（デフォルト: True）
    """
    sender = SyslogSender(
        host=syslog_host,
        port=syslog_port,
        protocol=protocol,
        facility=facility,
        severity=severity,
        app_name=app_name,
        ca_cert=ca_cert,
        client_cert=client_cert,
        client_key=client_key,
        verify=verify
    )
    
    try:
        # ファイルまたは標準入力から読み込み
        if file_path == "-":
            file_handle = sys.stdin
            should_close = False
        else:
            file_handle = open(file_path, 'r', encoding='utf-8')
            should_close = True
        
        try:
            for line in file_handle:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # JSONをパース
                    json_data = json.loads(line)
                    
                    # syslog経由で送信
                    sender.send_json(json_data)
                    
                    # 遅延を追加
                    if delay > 0:
                        time.sleep(delay)
                        
                except json.JSONDecodeError:
                    # JSONパースエラーは無視して続行
                    pass
                except (OSError, ConnectionError) as e:
                    # 接続エラーや送信エラーは無視して続行（ログ出力なし）
                    pass
        finally:
            if should_close:
                file_handle.close()
        
    finally:
        sender.close()


def get_last_processed_date(state_file: str) -> Optional[datetime]:
    """
    前回処理した日時を状態ファイルから読み込む
    
    状態ファイル（.last_runなど）から前回処理した日時を読み込みます。
    ファイルが存在しない場合は、空のファイルを作成してNoneを返します。
    読み込みに失敗した場合もNoneを返します。
    
    Args:
        state_file: 状態ファイルのパス
        
    Returns:
        前回処理した日時（datetimeオブジェクト）、ファイルが存在しないか
        読み込みに失敗した場合はNone
        
    Note:
        日時はISO形式（datetime.isoformat()）で保存されていることを前提とします。
        ファイルが存在しない場合は、親ディレクトリも含めて自動的に作成します。
    """
    state_path = Path(state_file)
    if not state_path.exists():
        # ファイルが存在しない場合は、空のファイルを作成
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.touch()
        return None
    
    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            date_str = f.read().strip()
            if date_str:
                return datetime.fromisoformat(date_str)
    except (ValueError, IOError):
        pass
    
    return None


def save_last_processed_date(state_file: str, date: datetime):
    """
    処理した日時を状態ファイルに保存
    
    処理完了後の最新日時を状態ファイルに保存します。親ディレクトリが
    存在しない場合は自動的に作成します。
    
    Args:
        state_file: 状態ファイルのパス（例: .last_run）
        date: 保存する日時（datetimeオブジェクト）
        
    Note:
        日時はISO形式（datetime.isoformat()）で保存されます。
        次回実行時にget_last_processed_date()で読み込むことができます。
        
    Raises:
        OSError: ファイルの書き込みに失敗した場合
    """
    state_path = Path(state_file)
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, 'w', encoding='utf-8') as f:
            f.write(date.isoformat())
    except (OSError, IOError) as e:
        # ファイル書き込みエラーは無視（ログ出力なし）
        pass


def get_files_since_date(directory: str, since_date: Optional[datetime], pattern: str = "*.jsonl") -> List[Path]:
    """
    指定日時以降に作成されたJSONLファイルを取得
    
    指定されたディレクトリ内で、パターンに一致し、指定日時以降に作成された
    ファイルのリストを取得します。ファイルは作成日時の昇順でソートされます。
    
    Args:
        directory: 検索対象のディレクトリのパス
        since_date: 基準となる日時（Noneの場合はすべてのファイルを対象）
        pattern: ファイル名のパターン（glob形式、デフォルト: *.jsonl）
        
    Returns:
        条件に合致するファイルのPathオブジェクトのリスト（作成日時の昇順でソート）
        
    Note:
        ディレクトリが存在しない、またはディレクトリでない場合は空のリストを返します。
        ファイルの作成日時は`st_mtime`（最終更新日時）を使用します。
    """
    dir_path = Path(directory)
    if not dir_path.exists() or not dir_path.is_dir():
        return []
    
    files = []
    for file_path in dir_path.glob(pattern):
        if file_path.is_file():
            try:
                # ファイルの作成日時（mtime）を取得
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                # since_dateが指定されている場合、それ以降のファイルのみ
                if since_date is None or file_mtime >= since_date:
                    files.append((file_path, file_mtime))
            except (OSError, PermissionError):
                # ファイルアクセスエラーは無視して続行
                pass
    
    # 作成日時の昇順でソート
    files.sort(key=lambda x: x[1])
    
    return [file_path for file_path, _ in files]


def send_jsonl_from_directory(
    directory: str,
    syslog_host: str = "localhost",
    syslog_port: int = 5140,
    protocol: str = "tcp",
    facility: int = 16,
    severity: int = 6,
    app_name: str = "jsonl-over-syslog",
    delay: float = 0.0,
    ca_cert: Optional[str] = None,
    client_cert: Optional[str] = None,
    client_key: Optional[str] = None,
    verify: bool = True,
    state_file: Optional[str] = None,
    pattern: str = "*.jsonl"
):
    """
    指定ディレクトリ内のJSONLファイルを日付ベースで処理してsyslog経由で送信
    
    Args:
        directory: ディレクトリのパス
        syslog_host: syslogサーバのホスト名
        syslog_port: syslogサーバのポート番号
        protocol: プロトコル（"udp"、"tcp"、または"tls"）
        facility: syslog facility (0-23)
        severity: syslog severity (0-7)
        app_name: アプリケーション名
        delay: 各行送信間の遅延（秒）
        ca_cert: CA証明書ファイルのパス（TLS用）
        client_cert: クライアント証明書ファイルのパス（TLS用、オプション）
        client_key: クライアント秘密鍵ファイルのパス（TLS用、オプション）
        verify: 証明書検証を有効にするか（デフォルト: True）
        state_file: 状態ファイルのパス（前回処理日時を記録、Noneの場合は記録しない）
        pattern: ファイル名のパターン（デフォルト: *.jsonl）
    """
    # 前回処理日時を読み込む
    last_date = None
    if state_file:
        last_date = get_last_processed_date(state_file)
    
    # 処理対象のファイルを取得
    files = get_files_since_date(directory, last_date, pattern)
    
    if not files:
        return
    
    # 最新の処理日時を記録（処理開始時点）
    latest_date = None
    
    # 各ファイルを処理
    for file_path in files:
        try:
            # ファイルの作成日時を取得
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            # 最新の日時を更新
            if latest_date is None or file_mtime > latest_date:
                latest_date = file_mtime
            
            # ファイルを送信
            send_jsonl_file(
                file_path=str(file_path),
                syslog_host=syslog_host,
                syslog_port=syslog_port,
                protocol=protocol,
                facility=facility,
                severity=severity,
                app_name=app_name,
                delay=delay,
                ca_cert=ca_cert,
                client_cert=client_cert,
                client_key=client_key,
                verify=verify
            )
        except (OSError, PermissionError, FileNotFoundError):
            # ファイルアクセスエラーは無視して続行
            pass
    
    # 処理完了後、最新の日時を保存
    if state_file and latest_date:
        save_last_processed_date(state_file, latest_date)


def load_env_file(env_path: str = ".env") -> dict:
    """
    .envファイルを読み込んで環境変数として設定
    
    .envファイルから環境変数を読み込み、os.environに設定します。
    既存の環境変数は上書きしません（.envファイルの値が優先されない）。
    
    Args:
        env_path: .envファイルのパス（デフォルト: .env）
        
    Returns:
        読み込んだ環境変数の辞書（キー: 環境変数名、値: 環境変数の値）
        
    Note:
        - ファイルが存在しない場合は空の辞書を返します
        - コメント行（#で始まる行）と空行は無視されます
        - KEY=VALUE形式の行を解析します
        - 値の前後のクォート（"または'）は自動的に削除されます
    """
    env_vars = {}
    env_file = Path(env_path)
    
    if not env_file.exists():
        return env_vars
    
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 空行やコメント行をスキップ
                if not line or line.startswith('#'):
                    continue
                
                # KEY=VALUE形式をパース
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # クォートを削除
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    env_vars[key] = value
                    # 環境変数としても設定（既存の環境変数は上書きしない）
                    if key not in os.environ:
                        os.environ[key] = value
    except (OSError, IOError):
        # ファイル読み込みエラーは無視
        pass
    
    return env_vars


def get_env_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    環境変数から値を取得（.envファイルから読み込まれた値も含む）
    
    os.environから環境変数の値を取得します。.envファイルから読み込まれた
    値も含まれます（load_env_file()で事前に読み込む必要があります）。
    
    Args:
        key: 取得する環境変数名
        default: 環境変数が存在しない場合のデフォルト値（デフォルト: None）
        
    Returns:
        環境変数の値（存在する場合）、またはデフォルト値
    """
    return os.environ.get(key, default)


def main():
    # .envファイルを読み込む
    load_env_file()
    
    parser = argparse.ArgumentParser(
        description="JSONLファイルの各行をsyslog経由で送信",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  # ローカルのsyslogサーバにTCPで送信（デフォルト: ポート5140）
  %(prog)s data.jsonl

  # リモートサーバに送信
  %(prog)s data.jsonl --host logs.example.com --port 5140

  # UDPプロトコルを使用
  %(prog)s data.jsonl --host logs.example.com --port 5140 --protocol udp

  # TLSで送信（CA証明書を使用）
  %(prog)s data.jsonl --host logs.example.com --port 6514 --protocol tls --ca-cert ca.crt

  # TLSで送信（クライアント証明書も使用）
  %(prog)s data.jsonl --host logs.example.com --port 6514 --protocol tls --ca-cert ca.crt --client-cert client.crt --client-key client.key

  # 標準入力から読み込み
  cat data.jsonl | %(prog)s -

  # .envファイルの設定を使用
  # .envファイルにSYSLOG_HOST, SYSLOG_PORTなどを設定しておく
  %(prog)s data.jsonl

  # ディレクトリを指定して、前回実行以降に作成されたファイルを自動的に処理
  %(prog)s --dir /path/to/output

  # 状態ファイルのパスを指定
  %(prog)s --dir /path/to/output --state-file /tmp/.last_run
        """
    )
    
    parser.add_argument(
        "file",
        nargs="?",
        help="JSONLファイルのパス（'-'の場合は標準入力、--dirが指定されている場合は不要）"
    )
    
    parser.add_argument(
        "--dir",
        help="ディレクトリパス（指定すると、前回実行以降に作成されたJSONLファイルを自動的に処理）"
    )
    
    parser.add_argument(
        "--state-file",
        default=".last_run",
        help="状態ファイルのパス（前回処理日時を記録、デフォルト: .last_run）"
    )
    
    parser.add_argument(
        "--pattern",
        default="*.jsonl",
        help="ファイル名のパターン（--dir使用時、デフォルト: *.jsonl）"
    )
    
    parser.add_argument(
        "--host",
        default=get_env_value("SYSLOG_HOST", "localhost"),
        help="syslogサーバのホスト名（デフォルト: localhost、環境変数: SYSLOG_HOST）"
    )
    
    def get_int_env(key: str, default: int) -> int:
        """環境変数から整数値を取得"""
        try:
            return int(get_env_value(key, str(default)))
        except (ValueError, TypeError):
            return default
    
    def get_float_env(key: str, default: float) -> float:
        """環境変数から浮動小数点値を取得"""
        try:
            return float(get_env_value(key, str(default)))
        except (ValueError, TypeError):
            return default
    
    parser.add_argument(
        "--port",
        type=int,
        default=get_int_env("SYSLOG_PORT", 5140),
        help="syslogサーバのポート番号（デフォルト: 5140、環境変数: SYSLOG_PORT）"
    )
    
    parser.add_argument(
        "--protocol",
        choices=["udp", "tcp", "tls"],
        default=get_env_value("SYSLOG_PROTOCOL", "tcp"),
        help="プロトコル（デフォルト: tcp、環境変数: SYSLOG_PROTOCOL）"
    )
    
    parser.add_argument(
        "--facility",
        type=int,
        default=get_int_env("SYSLOG_FACILITY", 16),
        choices=range(0, 24),
        metavar="0-23",
        help="syslog facility（デフォルト: 16 = local0、環境変数: SYSLOG_FACILITY）"
    )
    
    parser.add_argument(
        "--severity",
        type=int,
        default=get_int_env("SYSLOG_SEVERITY", 6),
        choices=range(0, 8),
        metavar="0-7",
        help="syslog severity（デフォルト: 6 = informational、環境変数: SYSLOG_SEVERITY）"
    )
    
    parser.add_argument(
        "--app-name",
        default=get_env_value("SYSLOG_APP_NAME", "jsonl-over-syslog"),
        help="アプリケーション名（デフォルト: jsonl-over-syslog、環境変数: SYSLOG_APP_NAME）"
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        default=get_float_env("SYSLOG_DELAY", 0.0),
        help="各行送信間の遅延（秒、デフォルト: 0.0、環境変数: SYSLOG_DELAY）"
    )
    
    parser.add_argument(
        "--ca-cert",
        default=get_env_value("SYSLOG_CA_CERT"),
        help="CA証明書ファイルのパス（TLS用、環境変数: SYSLOG_CA_CERT）"
    )
    
    parser.add_argument(
        "--client-cert",
        default=get_env_value("SYSLOG_CLIENT_CERT"),
        help="クライアント証明書ファイルのパス（TLS用、環境変数: SYSLOG_CLIENT_CERT）"
    )
    
    parser.add_argument(
        "--client-key",
        default=get_env_value("SYSLOG_CLIENT_KEY"),
        help="クライアント秘密鍵ファイルのパス（TLS用、環境変数: SYSLOG_CLIENT_KEY）"
    )
    
    # --no-verifyのデフォルト値を環境変数から取得
    no_verify_default = get_env_value("SYSLOG_NO_VERIFY", "false").lower() == "true"
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="証明書検証を無効化（TLS用、非推奨、環境変数: SYSLOG_NO_VERIFY）"
    )
    
    args = parser.parse_args()
    
    # --no-verifyが指定されていない場合、環境変数の値を使用
    no_verify = args.no_verify if args.no_verify else no_verify_default
    
    # ディレクトリモード
    if args.dir:
        send_jsonl_from_directory(
            directory=args.dir,
            syslog_host=args.host,
            syslog_port=args.port,
            protocol=args.protocol,
            facility=args.facility,
            severity=args.severity,
            app_name=args.app_name,
            delay=args.delay,
            ca_cert=args.ca_cert,
            client_cert=args.client_cert,
            client_key=args.client_key,
            verify=not no_verify,
            state_file=args.state_file,
            pattern=args.pattern
        )
    else:
        # ファイルモード（従来通り）
        if not args.file:
            parser.error("ファイルパスまたは--dirオプションが必要です")
        
        send_jsonl_file(
            file_path=args.file,
            syslog_host=args.host,
            syslog_port=args.port,
            protocol=args.protocol,
            facility=args.facility,
            severity=args.severity,
            app_name=args.app_name,
            delay=args.delay,
            verbose=False,  # ログ出力は常に無効
            ca_cert=args.ca_cert,
            client_cert=args.client_cert,
            client_key=args.client_key,
            verify=not no_verify
        )


if __name__ == "__main__":
    import os
    main()
