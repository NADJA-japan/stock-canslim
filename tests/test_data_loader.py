"""
CAN-SLIM US Stock Hunter DataLoaderのテスト

DataLoaderクラスの基本的な機能をテストします。
"""

import pytest
import tempfile
import os
from modules.data_loader import DataLoader
from config import Config


class TestDataLoader:
    """DataLoaderクラスのテスト"""
    
    def test_load_ticker_list_from_csv(self):
        """CSVファイルからティッカーリストを読み込む"""
        # 一時CSVファイルを作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("AAPL\n")
            f.write("NVDA\n")
            f.write("MSFT\n")
            temp_path = f.name
        
        try:
            loader = DataLoader()
            tickers = loader.load_ticker_list(temp_path)
            
            assert len(tickers) == 3
            assert "AAPL" in tickers
            assert "NVDA" in tickers
            assert "MSFT" in tickers
        finally:
            os.unlink(temp_path)
    
    def test_load_ticker_list_from_list(self):
        """Pythonリストからティッカーリストを読み込む"""
        loader = DataLoader()
        tickers = loader.load_ticker_list(["aapl", "nvda", "msft"])
        
        assert len(tickers) == 3
        assert "AAPL" in tickers
        assert "NVDA" in tickers
        assert "MSFT" in tickers
    
    def test_load_ticker_list_filters_invalid_tickers(self):
        """無効なティッカーがフィルタリングされることを確認"""
        loader = DataLoader()
        tickers = loader.load_ticker_list(["AAPL", "", "  ", "NVDA", "あいう"])
        
        assert len(tickers) == 2
        assert "AAPL" in tickers
        assert "NVDA" in tickers
    
    def test_load_ticker_list_removes_duplicates(self):
        """重複するティッカーが削除されることを確認"""
        loader = DataLoader()
        tickers = loader.load_ticker_list(["AAPL", "NVDA", "AAPL", "MSFT", "nvda"])
        
        assert len(tickers) == 3
        assert tickers.count("AAPL") == 1
        assert tickers.count("NVDA") == 1
        assert tickers.count("MSFT") == 1
    
    def test_load_ticker_list_file_not_found(self):
        """存在しないファイルでFileNotFoundErrorが発生することを確認"""
        loader = DataLoader()
        
        with pytest.raises(FileNotFoundError):
            loader.load_ticker_list("nonexistent_file.csv")
    
    def test_is_valid_ticker(self):
        """ティッカー検証ロジックのテスト"""
        loader = DataLoader()
        
        # 有効なティッカー
        assert loader._is_valid_ticker("AAPL") == True
        assert loader._is_valid_ticker("NVDA") == True
        assert loader._is_valid_ticker("BRK.B") == True
        assert loader._is_valid_ticker("BRK-B") == True
        
        # 無効なティッカー
        assert loader._is_valid_ticker("") == False
        assert loader._is_valid_ticker("  ") == False
        assert loader._is_valid_ticker("あいう") == False
        assert loader._is_valid_ticker("A" * 11) == False  # 長すぎる
