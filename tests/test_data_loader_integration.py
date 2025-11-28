"""
CAN-SLIM US Stock Hunter DataLoader統合テスト

実際のyfinance APIを使用した統合テストです。
ネットワーク接続が必要です。
"""

import pytest
from modules.data_loader import DataLoader
from config import Config


class TestDataLoaderIntegration:
    """DataLoaderの統合テスト（実際のAPI呼び出し）"""
    
    @pytest.mark.integration
    def test_fetch_price_data_single_ticker(self):
        """単一ティッカーの株価データ取得"""
        loader = DataLoader()
        data = loader.fetch_price_data(["AAPL"], period="1mo")
        
        assert "AAPL" in data
        assert not data["AAPL"].empty
        assert "Close" in data["AAPL"].columns
        assert "Volume" in data["AAPL"].columns
    
    @pytest.mark.integration
    def test_fetch_price_data_multiple_tickers(self):
        """複数ティッカーの株価データ取得"""
        loader = DataLoader()
        data = loader.fetch_price_data(["AAPL", "MSFT"], period="1mo")
        
        assert len(data) >= 1  # 少なくとも1つは成功するはず
        for ticker, df in data.items():
            assert not df.empty
            assert "Close" in df.columns
    
    @pytest.mark.integration
    def test_fetch_price_data_invalid_ticker(self):
        """無効なティッカーでもエラーが発生しないことを確認"""
        loader = DataLoader()
        data = loader.fetch_price_data(["INVALID_TICKER_XYZ"], period="1mo")
        
        # 無効なティッカーはスキップされる
        assert len(data) == 0
    
    @pytest.mark.integration
    def test_fetch_financial_data(self):
        """財務データ取得"""
        loader = DataLoader()
        data = loader.fetch_financial_data("AAPL")
        
        if data:  # データが取得できた場合
            assert "quarterly_earnings" in data
            assert "quarterly_revenue" in data
            assert "info" in data
    
    @pytest.mark.integration
    def test_fetch_company_info(self):
        """企業情報取得"""
        loader = DataLoader()
        info = loader.fetch_company_info("AAPL")
        
        if info:  # データが取得できた場合
            assert "name" in info
            assert "sector" in info
            assert "industry" in info
            assert info["name"]  # 空でないことを確認
    
    @pytest.mark.integration
    def test_fetch_news(self):
        """ニュース取得"""
        loader = DataLoader()
        news = loader.fetch_news("AAPL", max_items=2)
        
        # ニュースは利用できない場合もあるので、空リストでもOK
        assert isinstance(news, list)
        assert len(news) <= 2
        
        if news:  # ニュースが取得できた場合
            assert "title" in news[0]
            assert "url" in news[0]
            assert "published_date" in news[0]
