"""
CAN-SLIM US Stock Hunter データモデルのテスト

データクラスの基本的な機能と検証ロジックをテストします。
"""

import pytest
from datetime import datetime
from modules.models import StockData, FinancialMetrics, ExitStrategy, NewsItem


class TestStockData:
    """StockDataデータクラスのテスト"""
    
    def test_stock_data_creation(self):
        """正常なStockDataインスタンスの作成"""
        stock = StockData(
            ticker="AAPL",
            current_price=150.0,
            volume_50d_avg=50_000_000.0,
            sma_50=145.0,
            sma_200=140.0,
            high_52w=180.0,
            return_1y=0.25
        )
        
        assert stock.ticker == "AAPL"
        assert stock.current_price == 150.0
        assert stock.volume_50d_avg == 50_000_000.0
        assert stock.sma_50 == 145.0
        assert stock.sma_200 == 140.0
        assert stock.high_52w == 180.0
        assert stock.return_1y == 0.25
    
    def test_stock_data_negative_price_raises_error(self):
        """負の株価でエラーが発生することを確認"""
        with pytest.raises(ValueError, match="current_price must be non-negative"):
            StockData(
                ticker="AAPL",
                current_price=-10.0,
                volume_50d_avg=50_000_000.0,
                sma_50=145.0,
                sma_200=140.0,
                high_52w=180.0,
                return_1y=0.25
            )
    
    def test_stock_data_negative_volume_raises_error(self):
        """負の出来高でエラーが発生することを確認"""
        with pytest.raises(ValueError, match="volume_50d_avg must be non-negative"):
            StockData(
                ticker="AAPL",
                current_price=150.0,
                volume_50d_avg=-1000.0,
                sma_50=145.0,
                sma_200=140.0,
                high_52w=180.0,
                return_1y=0.25
            )


class TestFinancialMetrics:
    """FinancialMetricsデータクラスのテスト"""
    
    def test_financial_metrics_creation(self):
        """正常なFinancialMetricsインスタンスの作成"""
        metrics = FinancialMetrics(
            eps_growth_q=0.25,
            revenue_growth_q=0.30,
            roe=0.18,
            sector="Technology",
            industry="Software"
        )
        
        assert metrics.eps_growth_q == 0.25
        assert metrics.revenue_growth_q == 0.30
        assert metrics.roe == 0.18
        assert metrics.sector == "Technology"
        assert metrics.industry == "Software"


class TestExitStrategy:
    """ExitStrategyデータクラスのテスト"""
    
    def test_exit_strategy_creation(self):
        """正常なExitStrategyインスタンスの作成"""
        strategy = ExitStrategy(
            profit_target_price=180.0,
            profit_condition="株価が10日移動平均線を下回る",
            profit_reason="20%利益確定",
            stop_loss_price=139.5,
            stop_loss_condition="株価が購入価格から7%下落",
            stop_loss_reason="損失を最小限に抑える"
        )
        
        assert strategy.profit_target_price == 180.0
        assert strategy.profit_condition == "株価が10日移動平均線を下回る"
        assert strategy.profit_reason == "20%利益確定"
        assert strategy.stop_loss_price == 139.5
        assert strategy.stop_loss_condition == "株価が購入価格から7%下落"
        assert strategy.stop_loss_reason == "損失を最小限に抑える"
    
    def test_exit_strategy_negative_profit_target_raises_error(self):
        """負の利益確定価格でエラーが発生することを確認"""
        with pytest.raises(ValueError, match="profit_target_price must be non-negative"):
            ExitStrategy(
                profit_target_price=-180.0,
                profit_condition="株価が10日移動平均線を下回る",
                profit_reason="20%利益確定",
                stop_loss_price=139.5,
                stop_loss_condition="株価が購入価格から7%下落",
                stop_loss_reason="損失を最小限に抑える"
            )
    
    def test_exit_strategy_negative_stop_loss_raises_error(self):
        """負の損切り価格でエラーが発生することを確認"""
        with pytest.raises(ValueError, match="stop_loss_price must be non-negative"):
            ExitStrategy(
                profit_target_price=180.0,
                profit_condition="株価が10日移動平均線を下回る",
                profit_reason="20%利益確定",
                stop_loss_price=-139.5,
                stop_loss_condition="株価が購入価格から7%下落",
                stop_loss_reason="損失を最小限に抑える"
            )


class TestNewsItem:
    """NewsItemデータクラスのテスト"""
    
    def test_news_item_creation(self):
        """正常なNewsItemインスタンスの作成"""
        news = NewsItem(
            title="Apple announces new product",
            url="https://example.com/news/apple",
            published_date=datetime(2024, 1, 15, 10, 30)
        )
        
        assert news.title == "Apple announces new product"
        assert news.url == "https://example.com/news/apple"
        assert news.published_date == datetime(2024, 1, 15, 10, 30)
    
    def test_news_item_empty_title_raises_error(self):
        """空のタイトルでエラーが発生することを確認"""
        with pytest.raises(ValueError, match="title cannot be empty"):
            NewsItem(
                title="",
                url="https://example.com/news/apple",
                published_date=datetime(2024, 1, 15, 10, 30)
            )
    
    def test_news_item_empty_url_raises_error(self):
        """空のURLでエラーが発生することを確認"""
        with pytest.raises(ValueError, match="url cannot be empty"):
            NewsItem(
                title="Apple announces new product",
                url="",
                published_date=datetime(2024, 1, 15, 10, 30)
            )
    
    def test_news_item_invalid_date_raises_error(self):
        """無効な日付型でエラーが発生することを確認"""
        with pytest.raises(ValueError, match="published_date must be datetime"):
            NewsItem(
                title="Apple announces new product",
                url="https://example.com/news/apple",
                published_date="2024-01-15"  # 文字列は無効
            )
