"""
CAN-SLIM US Stock Hunter データモデル

このモジュールは以下のデータクラスを定義します：
- StockData: 株価データ
- FinancialMetrics: 財務指標
- ExitStrategy: Exit戦略情報
- NewsItem: ニュース項目
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class StockData:
    """
    株価データを表すデータクラス
    
    テクニカルフィルタリングに必要な株価情報を保持します。
    
    Attributes:
        ticker: ティッカーシンボル（例: "AAPL", "NVDA"）
        current_price: 現在の株価（USD）
        volume_50d_avg: 50日平均出来高
        sma_50: 50日単純移動平均線
        sma_200: 200日単純移動平均線
        high_52w: 52週高値
        return_1y: 1年間リターン（小数表記、例: 0.25 = 25%）
    """
    ticker: str
    current_price: float
    volume_50d_avg: float
    sma_50: float
    sma_200: float
    high_52w: float
    return_1y: float
    
    def __post_init__(self):
        """データクラス初期化後の検証"""
        if self.current_price < 0:
            raise ValueError(f"current_price must be non-negative, got {self.current_price}")
        if self.volume_50d_avg < 0:
            raise ValueError(f"volume_50d_avg must be non-negative, got {self.volume_50d_avg}")
        if self.sma_50 < 0:
            raise ValueError(f"sma_50 must be non-negative, got {self.sma_50}")
        if self.sma_200 < 0:
            raise ValueError(f"sma_200 must be non-negative, got {self.sma_200}")
        if self.high_52w < 0:
            raise ValueError(f"high_52w must be non-negative, got {self.high_52w}")


@dataclass
class FinancialMetrics:
    """
    財務指標を表すデータクラス
    
    ファンダメンタルフィルタリングに必要な財務情報を保持します。
    
    Attributes:
        eps_growth_q: 四半期EPS成長率（小数表記、例: 0.25 = 25%）
        revenue_growth_q: 四半期売上成長率（小数表記、例: 0.25 = 25%）
        roe: 年間ROE（自己資本利益率、小数表記、例: 0.15 = 15%）
        sector: セクター（例: "Technology", "Healthcare"）
        industry: 業種（例: "Software", "Biotechnology"）
    """
    eps_growth_q: float
    revenue_growth_q: float
    roe: float
    sector: str
    industry: str


@dataclass
class ExitStrategy:
    """
    Exit戦略情報を表すデータクラス
    
    利益確定と損切りの判断基準を保持します。
    
    Attributes:
        profit_target_price: 利益確定目標価格（USD）
        profit_condition: 利益確定条件の説明
        profit_reason: 利益確定の理由
        stop_loss_price: 損切り価格（USD）
        stop_loss_condition: 損切り条件の説明
        stop_loss_reason: 損切りの理由
    """
    profit_target_price: float
    profit_condition: str
    profit_reason: str
    stop_loss_price: float
    stop_loss_condition: str
    stop_loss_reason: str
    
    def __post_init__(self):
        """データクラス初期化後の検証"""
        if self.profit_target_price < 0:
            raise ValueError(f"profit_target_price must be non-negative, got {self.profit_target_price}")
        if self.stop_loss_price < 0:
            raise ValueError(f"stop_loss_price must be non-negative, got {self.stop_loss_price}")


@dataclass
class NewsItem:
    """
    ニュース項目を表すデータクラス
    
    銘柄に関連するニュース情報を保持します。
    
    Attributes:
        title: ニュースのタイトル
        url: ニュース記事のURL
        published_date: 公開日時
    """
    title: str
    url: str
    published_date: datetime
    
    def __post_init__(self):
        """データクラス初期化後の検証"""
        if not self.title:
            raise ValueError("title cannot be empty")
        if not self.url:
            raise ValueError("url cannot be empty")
        if not isinstance(self.published_date, datetime):
            raise ValueError(f"published_date must be datetime, got {type(self.published_date)}")
