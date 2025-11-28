"""
CAN-SLIM US Stock Hunter 設定モジュール

このモジュールは以下の設定値を一元管理します：
- スクリーニング基準の閾値
- Exit戦略パラメータ
- Slack設定
- データソース設定
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()


class Config:
    """CAN-SLIMスクリーナーの中央設定クラス"""
    
    # ==================== スクリーニング基準 ====================
    
    # テクニカルフィルター閾値
    MIN_PRICE: float = 10.0  # 最低株価（USD）
    MIN_VOL_AVG: int = 200_000  # 最低50日平均出来高
    NEAR_HIGH_PCT: float = 0.85  # 52週高値に対する割合（85%）
    
    # ファンダメンタルフィルター閾値
    EPS_GROWTH_THRESHOLD: float = 0.20  # 四半期EPS成長率（20%）
    REV_GROWTH_THRESHOLD: float = 0.20  # 四半期売上成長率（20%）
    ROE_THRESHOLD: float = 0.15  # 年間ROE（15%）
    
    # ==================== Exit戦略パラメータ ====================
    
    PROFIT_TARGET_PCT: float = 0.20  # 利益確定目標（20%）
    STOP_LOSS_PCT: float = 0.07  # 損切り（7%）
    MA_STOP_LOSS_PCT: float = 0.03  # 50日移動平均線下回り損切り（3%）
    
    # 移動平均線期間
    MA_10_PERIOD: int = 10  # 10日移動平均線（利益確定Exit用）
    MA_50_PERIOD: int = 50  # 50日移動平均線
    MA_200_PERIOD: int = 200  # 200日移動平均線
    
    # ==================== Slack設定 ====================
    
    SLACK_BOT_TOKEN: Optional[str] = os.getenv("SLACK_BOT_TOKEN")
    SLACK_CHANNEL: str = os.getenv("SLACK_CHANNEL", "#stock-alerts")  # 通知先のSlackチャンネル
    
    # ==================== データソース設定 ====================
    
    TICKER_LIST_PATH: str = "tickers.csv"
    CHART_OUTPUT_DIR: str = "output"
    
    # データ取得パラメータ
    PRICE_DATA_PERIOD: str = "1y"  # 252取引日（約1年）
    BENCHMARK_TICKER: str = "SPY"  # 相対力比較用のS&P 500 ETF
    
    # ==================== APIレート制限 ====================
    
    API_CALL_DELAY: float = 1.0  # API呼び出し間隔（秒）
    MAX_RETRIES: int = 3  # ネットワークエラー時の最大リトライ回数
    RETRY_BACKOFF_BASE: float = 2.0  # 指数バックオフの基数
    
    # ==================== ニュース設定 ====================
    
    MAX_NEWS_ITEMS: int = 2  # ティッカーあたりの最大ニュース取得数
    MIN_NEWS_ITEMS: int = 1  # ティッカーあたりの最小ニュース取得数（利用可能な場合）
    
    # ==================== ロギング設定 ====================
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    
    @classmethod
    def validate(cls) -> bool:
        """
        設定値を検証する
        
        Returns:
            bool: 設定が有効な場合True、そうでない場合False
        """
        if not cls.SLACK_BOT_TOKEN:
            logging.warning("環境変数にSLACK_BOT_TOKENが設定されていません")
            return False
        
        if cls.MIN_PRICE <= 0:
            logging.error("MIN_PRICEは正の値である必要があります")
            return False
        
        if cls.MIN_VOL_AVG <= 0:
            logging.error("MIN_VOL_AVGは正の値である必要があります")
            return False
        
        return True
    
    @classmethod
    def get_log_level(cls) -> int:
        """
        文字列のログレベルをlogging定数に変換する
        
        Returns:
            int: ロギングレベル定数
        """
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return level_map.get(cls.LOG_LEVEL.upper(), logging.INFO)


def setup_logging() -> None:
    """
    アプリケーションのロギングを設定する
    
    設定されたフォーマットとレベルでコンソールハンドラーをセットアップします。
    """
    logging.basicConfig(
        level=Config.get_log_level(),
        format=Config.LOG_FORMAT,
        datefmt=Config.LOG_DATE_FORMAT,
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # サードパーティライブラリのログレベルをWARNINGに設定してノイズを削減
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


# モジュールインポート時にロギングを初期化
setup_logging()
