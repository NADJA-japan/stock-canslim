"""
CAN-SLIM US Stock Hunter メインモジュールのテスト

このテストモジュールは以下をテストします：
- fetch_with_retry()ヘルパー関数
- safe_process_ticker()ヘルパー関数
"""

import pytest
import time
from unittest.mock import Mock, patch
from requests.exceptions import Timeout, RequestException
import pandas as pd

from main import fetch_with_retry, safe_process_ticker


class TestFetchWithRetry:
    """fetch_with_retry()関数のテスト"""
    
    def test_successful_fetch_on_first_attempt(self):
        """最初の試行で成功する場合"""
        mock_func = Mock(return_value="success")
        
        result = fetch_with_retry(mock_func, max_retries=3)
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_on_timeout(self):
        """タイムアウト時にリトライする"""
        mock_func = Mock(side_effect=[Timeout(), Timeout(), "success"])
        
        result = fetch_with_retry(mock_func, max_retries=3, backoff_base=0.1)
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_max_retries_exceeded_on_timeout(self):
        """最大リトライ回数を超えた場合"""
        mock_func = Mock(side_effect=Timeout())
        
        result = fetch_with_retry(mock_func, max_retries=3, backoff_base=0.1)
        
        assert result is None
        assert mock_func.call_count == 3
    
    def test_retry_on_request_exception(self):
        """RequestException時にリトライする"""
        mock_func = Mock(side_effect=[RequestException("Rate limit"), "success"])
        
        result = fetch_with_retry(mock_func, max_retries=3, backoff_base=0.1)
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_no_retry_on_unexpected_exception(self):
        """予期しない例外の場合はリトライしない"""
        mock_func = Mock(side_effect=ValueError("Invalid data"))
        
        result = fetch_with_retry(mock_func, max_retries=3)
        
        assert result is None
        assert mock_func.call_count == 1
    
    def test_exponential_backoff(self):
        """指数バックオフが正しく動作する"""
        mock_func = Mock(side_effect=[Timeout(), Timeout(), "success"])
        
        start_time = time.time()
        result = fetch_with_retry(mock_func, max_retries=3, backoff_base=2.0)
        elapsed_time = time.time() - start_time
        
        assert result == "success"
        # 2^0 + 2^1 = 1 + 2 = 3秒以上待機するはず（わずかな誤差を許容）
        assert elapsed_time >= 2.9


class TestSafeProcessTicker:
    """safe_process_ticker()関数のテスト"""
    
    def test_successful_processing(self):
        """正常に処理が完了する場合"""
        mock_func = Mock(return_value={"data": "value"})
        
        result = safe_process_ticker("AAPL", mock_func, "テスト処理")
        
        assert result == {"data": "value"}
        mock_func.assert_called_once_with("AAPL")
    
    def test_none_result(self):
        """処理関数がNoneを返す場合"""
        mock_func = Mock(return_value=None)
        
        result = safe_process_ticker("AAPL", mock_func, "テスト処理")
        
        assert result is None
        mock_func.assert_called_once_with("AAPL")
    
    def test_empty_dataframe(self):
        """空のDataFrameを返す場合"""
        mock_func = Mock(return_value=pd.DataFrame())
        
        result = safe_process_ticker("AAPL", mock_func, "テスト処理")
        
        assert result is None
        mock_func.assert_called_once_with("AAPL")
    
    def test_empty_dict(self):
        """空の辞書を返す場合"""
        mock_func = Mock(return_value={})
        
        result = safe_process_ticker("AAPL", mock_func, "テスト処理")
        
        assert result is None
        mock_func.assert_called_once_with("AAPL")
    
    def test_value_error_handling(self):
        """ValueError（無効なティッカー）を処理する"""
        mock_func = Mock(side_effect=ValueError("Invalid ticker"))
        
        result = safe_process_ticker("INVALID", mock_func, "テスト処理")
        
        assert result is None
        mock_func.assert_called_once_with("INVALID")
    
    def test_generic_exception_handling(self):
        """一般的な例外を処理する"""
        mock_func = Mock(side_effect=Exception("Unexpected error"))
        
        result = safe_process_ticker("AAPL", mock_func, "テスト処理")
        
        assert result is None
        mock_func.assert_called_once_with("AAPL")
    
    def test_non_empty_dataframe(self):
        """空でないDataFrameを返す場合"""
        df = pd.DataFrame({"col": [1, 2, 3]})
        mock_func = Mock(return_value=df)
        
        result = safe_process_ticker("AAPL", mock_func, "テスト処理")
        
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
    
    def test_non_empty_dict(self):
        """空でない辞書を返す場合"""
        data = {"key": "value"}
        mock_func = Mock(return_value=data)
        
        result = safe_process_ticker("AAPL", mock_func, "テスト処理")
        
        assert result == data
