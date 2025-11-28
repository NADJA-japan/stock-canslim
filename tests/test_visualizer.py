"""
ChartGeneratorクラスのテスト

このモジュールはChartGeneratorクラスの機能をテストします。
"""

import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from modules.visualizer import ChartGenerator


@pytest.fixture
def temp_output_dir(tmp_path):
    """一時的な出力ディレクトリを作成するフィクスチャ"""
    output_dir = tmp_path / "output"
    return str(output_dir)


@pytest.fixture
def sample_stock_data():
    """サンプル株価データを生成するフィクスチャ"""
    # 252取引日分のデータを生成
    dates = pd.date_range(end=datetime.now(), periods=252, freq='B')
    
    # ランダムな株価データを生成
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(252) * 2)
    
    data = pd.DataFrame({
        'Open': close_prices + np.random.randn(252) * 0.5,
        'High': close_prices + np.abs(np.random.randn(252) * 1.5),
        'Low': close_prices - np.abs(np.random.randn(252) * 1.5),
        'Close': close_prices,
        'Volume': np.random.randint(1000000, 10000000, 252)
    }, index=dates)
    
    return data


class TestChartGenerator:
    """ChartGeneratorクラスのテストスイート"""
    
    def test_init_creates_output_directory(self, temp_output_dir):
        """初期化時に出力ディレクトリが作成されることをテスト"""
        generator = ChartGenerator(temp_output_dir)
        assert os.path.exists(temp_output_dir)
        assert generator.output_dir == temp_output_dir
    
    def test_generate_chart_creates_file(self, temp_output_dir, sample_stock_data):
        """チャート生成がファイルを作成することをテスト"""
        generator = ChartGenerator(temp_output_dir)
        ticker = "AAPL"
        
        file_path = generator.generate_chart(ticker, sample_stock_data)
        
        # ファイルが作成されたことを確認
        assert os.path.exists(file_path)
        assert file_path == os.path.join(temp_output_dir, f"chart_{ticker}.png")
    
    def test_generate_chart_filename_format(self, temp_output_dir, sample_stock_data):
        """チャートファイル名が正しい形式であることをテスト（要件4.6）"""
        generator = ChartGenerator(temp_output_dir)
        tickers = ["AAPL", "NVDA", "MSFT"]
        
        for ticker in tickers:
            file_path = generator.generate_chart(ticker, sample_stock_data)
            expected_filename = f"chart_{ticker}.png"
            assert os.path.basename(file_path) == expected_filename
    
    def test_generate_chart_with_empty_data_raises_error(self, temp_output_dir):
        """空のデータでチャート生成するとエラーが発生することをテスト"""
        generator = ChartGenerator(temp_output_dir)
        empty_data = pd.DataFrame()
        
        with pytest.raises(ValueError, match="株価データが空です"):
            generator.generate_chart("AAPL", empty_data)
    
    def test_generate_chart_with_missing_columns_raises_error(self, temp_output_dir):
        """必須カラムが不足している場合にエラーが発生することをテスト"""
        generator = ChartGenerator(temp_output_dir)
        
        # Volumeカラムが欠けているデータ
        dates = pd.date_range(end=datetime.now(), periods=10, freq='B')
        incomplete_data = pd.DataFrame({
            'Open': [100] * 10,
            'High': [105] * 10,
            'Low': [95] * 10,
            'Close': [102] * 10
        }, index=dates)
        
        with pytest.raises(ValueError, match="必須カラムが不足しています"):
            generator.generate_chart("AAPL", incomplete_data)
    
    def test_generate_chart_with_non_datetime_index_raises_error(self, temp_output_dir):
        """DatetimeIndexでない場合にエラーが発生することをテスト"""
        generator = ChartGenerator(temp_output_dir)
        
        # 整数インデックスのデータ
        data = pd.DataFrame({
            'Open': [100] * 10,
            'High': [105] * 10,
            'Low': [95] * 10,
            'Close': [102] * 10,
            'Volume': [1000000] * 10
        })
        
        with pytest.raises(ValueError, match="DatetimeIndexである必要があります"):
            generator.generate_chart("AAPL", data)
    
    def test_generate_chart_multiple_tickers(self, temp_output_dir, sample_stock_data):
        """複数のティッカーに対してチャートを生成できることをテスト"""
        generator = ChartGenerator(temp_output_dir)
        tickers = ["AAPL", "NVDA", "MSFT"]
        
        for ticker in tickers:
            file_path = generator.generate_chart(ticker, sample_stock_data)
            assert os.path.exists(file_path)
        
        # すべてのファイルが作成されたことを確認
        files = os.listdir(temp_output_dir)
        assert len(files) == len(tickers)
        for ticker in tickers:
            assert f"chart_{ticker}.png" in files
