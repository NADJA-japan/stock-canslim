"""
SlackNotifierクラスのユニットテスト
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from slack_sdk.errors import SlackApiError

from modules.notifier import SlackNotifier
from modules.models import ExitStrategy, NewsItem


@pytest.fixture
def mock_slack_client():
    """モックされたSlack WebClientを返す"""
    with patch('modules.notifier.WebClient') as mock_client:
        yield mock_client


@pytest.fixture
def sample_exit_strategy():
    """サンプルのExit戦略データを返す"""
    return ExitStrategy(
        profit_target_price=120.0,
        profit_condition="株価が10日移動平均線を下回ったら利益確定を検討",
        profit_reason="目標価格（現在価格+20%）に到達",
        stop_loss_price=93.0,
        stop_loss_condition="株価が50日移動平均線を3%以上下回ったら損切り",
        stop_loss_reason="株価が購入価格から7%下落"
    )


@pytest.fixture
def sample_news():
    """サンプルのニュースデータを返す"""
    return [
        NewsItem(
            title="Company announces record earnings",
            url="https://example.com/news1",
            published_date=datetime(2024, 1, 15, 10, 30)
        ),
        NewsItem(
            title="New product launch expected",
            url="https://example.com/news2",
            published_date=datetime(2024, 1, 14, 14, 20)
        )
    ]


@pytest.fixture
def sample_metrics():
    """サンプルの財務指標を返す"""
    return {
        'eps_growth_q': 0.25,  # 25%
        'revenue_growth_q': 0.30,  # 30%
        'roe': 0.18,  # 18%
        'rs_rating': 'A+'
    }


@pytest.fixture
def sample_company_info():
    """サンプルの企業情報を返す"""
    return {
        'sector': 'Technology',
        'industry': 'Software'
    }


class TestSlackNotifierInit:
    """SlackNotifierの初期化テスト"""
    
    def test_init_creates_client(self, mock_slack_client):
        """初期化時にWebClientが作成されることを確認"""
        notifier = SlackNotifier(token="test-token", channel="#test")
        
        mock_slack_client.assert_called_once_with(token="test-token")
        assert notifier.channel == "#test"


class TestFormatMessage:
    """_format_messageメソッドのテスト"""
    
    def test_format_message_includes_ticker_and_company(
        self, mock_slack_client, sample_exit_strategy, sample_news,
        sample_metrics, sample_company_info
    ):
        """メッセージにティッカーシンボルと企業名が含まれることを確認"""
        notifier = SlackNotifier(token="test-token", channel="#test")
        
        message = notifier._format_message(
            ticker="AAPL",
            company_name="Apple Inc.",
            current_price=150.0,
            metrics=sample_metrics,
            exit_strategy=sample_exit_strategy,
            news=sample_news,
            company_info=sample_company_info
        )
        
        assert "AAPL" in message['text']
        assert "Apple Inc." in message['text']
        assert message['blocks'][0]['text']['text'] == "AAPL - Apple Inc."
    
    def test_format_message_includes_current_price(
        self, mock_slack_client, sample_exit_strategy, sample_news,
        sample_metrics, sample_company_info
    ):
        """メッセージに現在株価が含まれることを確認"""
        notifier = SlackNotifier(token="test-token", channel="#test")
        
        message = notifier._format_message(
            ticker="AAPL",
            company_name="Apple Inc.",
            current_price=150.50,
            metrics=sample_metrics,
            exit_strategy=sample_exit_strategy,
            news=sample_news,
            company_info=sample_company_info
        )
        
        assert "$150.50" in message['text']
        assert "$150.50" in message['blocks'][1]['text']['text']
    
    def test_format_message_includes_financial_metrics(
        self, mock_slack_client, sample_exit_strategy, sample_news,
        sample_metrics, sample_company_info
    ):
        """メッセージに財務指標が含まれることを確認"""
        notifier = SlackNotifier(token="test-token", channel="#test")
        
        message = notifier._format_message(
            ticker="AAPL",
            company_name="Apple Inc.",
            current_price=150.0,
            metrics=sample_metrics,
            exit_strategy=sample_exit_strategy,
            news=sample_news,
            company_info=sample_company_info
        )
        
        text = message['text']
        assert "25.0%" in text  # EPS成長率
        assert "30.0%" in text  # 売上成長率
        assert "18.0%" in text  # ROE
        assert "A+" in text  # 相対力評価
    
    def test_format_message_includes_exit_strategy(
        self, mock_slack_client, sample_exit_strategy, sample_news,
        sample_metrics, sample_company_info
    ):
        """メッセージにExit戦略情報が含まれることを確認"""
        notifier = SlackNotifier(token="test-token", channel="#test")
        
        message = notifier._format_message(
            ticker="AAPL",
            company_name="Apple Inc.",
            current_price=150.0,
            metrics=sample_metrics,
            exit_strategy=sample_exit_strategy,
            news=sample_news,
            company_info=sample_company_info
        )
        
        text = message['text']
        assert "$120.00" in text  # 利益確定目標価格
        assert "$93.00" in text  # 損切り価格
        assert "10日移動平均線" in text  # 利益確定条件
        assert "50日移動平均線" in text  # 損切り条件
    
    def test_format_message_includes_links(
        self, mock_slack_client, sample_exit_strategy, sample_news,
        sample_metrics, sample_company_info
    ):
        """メッセージにYahoo FinanceとTradingViewのリンクが含まれることを確認"""
        notifier = SlackNotifier(token="test-token", channel="#test")
        
        message = notifier._format_message(
            ticker="AAPL",
            company_name="Apple Inc.",
            current_price=150.0,
            metrics=sample_metrics,
            exit_strategy=sample_exit_strategy,
            news=sample_news,
            company_info=sample_company_info
        )
        
        text = message['text']
        assert "https://finance.yahoo.com/quote/AAPL" in text
        assert "https://www.tradingview.com/symbols/AAPL" in text
    
    def test_format_message_includes_news(
        self, mock_slack_client, sample_exit_strategy, sample_news,
        sample_metrics, sample_company_info
    ):
        """メッセージにニュース項目が含まれることを確認"""
        notifier = SlackNotifier(token="test-token", channel="#test")
        
        message = notifier._format_message(
            ticker="AAPL",
            company_name="Apple Inc.",
            current_price=150.0,
            metrics=sample_metrics,
            exit_strategy=sample_exit_strategy,
            news=sample_news,
            company_info=sample_company_info
        )
        
        text = message['text']
        assert "Company announces record earnings" in text
        assert "https://example.com/news1" in text
        assert "New product launch expected" in text
        assert "https://example.com/news2" in text
    
    def test_format_message_handles_empty_news(
        self, mock_slack_client, sample_exit_strategy,
        sample_metrics, sample_company_info
    ):
        """ニュースが空の場合でもメッセージが正しくフォーマットされることを確認"""
        notifier = SlackNotifier(token="test-token", channel="#test")
        
        message = notifier._format_message(
            ticker="AAPL",
            company_name="Apple Inc.",
            current_price=150.0,
            metrics=sample_metrics,
            exit_strategy=sample_exit_strategy,
            news=[],
            company_info=sample_company_info
        )
        
        text = message['text']
        assert "ニュースデータなし" in text
    
    def test_format_message_includes_company_info(
        self, mock_slack_client, sample_exit_strategy, sample_news,
        sample_metrics, sample_company_info
    ):
        """メッセージに企業情報が含まれることを確認"""
        notifier = SlackNotifier(token="test-token", channel="#test")
        
        message = notifier._format_message(
            ticker="AAPL",
            company_name="Apple Inc.",
            current_price=150.0,
            metrics=sample_metrics,
            exit_strategy=sample_exit_strategy,
            news=sample_news,
            company_info=sample_company_info
        )
        
        text = message['text']
        assert "Technology" in text
        assert "Software" in text


class TestUploadChart:
    """_upload_chartメソッドのテスト"""
    
    def test_upload_chart_success(self, mock_slack_client):
        """チャート画像が正常にアップロードされることを確認"""
        mock_instance = mock_slack_client.return_value
        mock_instance.files_upload_v2.return_value = {
            'file': {
                'permalink': 'https://files.slack.com/test-chart.png'
            }
        }
        
        notifier = SlackNotifier(token="test-token", channel="#test")
        file_url = notifier._upload_chart("output/chart_AAPL.png", "AAPL")
        
        assert file_url == 'https://files.slack.com/test-chart.png'
        mock_instance.files_upload_v2.assert_called_once_with(
            channel="#test",
            file="output/chart_AAPL.png",
            title="AAPL チャート",
            initial_comment="AAPLの株価チャート"
        )
    
    def test_upload_chart_handles_api_error(self, mock_slack_client):
        """Slack APIエラーが適切に処理されることを確認"""
        mock_instance = mock_slack_client.return_value
        mock_response = {'error': 'file_upload_failed'}
        mock_instance.files_upload_v2.side_effect = SlackApiError(
            message="File upload failed",
            response=mock_response
        )
        
        notifier = SlackNotifier(token="test-token", channel="#test")
        
        with pytest.raises(SlackApiError):
            notifier._upload_chart("output/chart_AAPL.png", "AAPL")


class TestPostStockAlert:
    """post_stock_alertメソッドのテスト"""
    
    def test_post_stock_alert_success(
        self, mock_slack_client, sample_exit_strategy, sample_news,
        sample_metrics, sample_company_info
    ):
        """株式アラートが正常に投稿されることを確認"""
        mock_instance = mock_slack_client.return_value
        mock_instance.files_upload_v2.return_value = {
            'file': {'permalink': 'https://files.slack.com/test.png'}
        }
        mock_instance.chat_postMessage.return_value = {'ts': '1234567890.123456'}
        
        notifier = SlackNotifier(token="test-token", channel="#test")
        
        # エラーが発生しないことを確認
        notifier.post_stock_alert(
            ticker="AAPL",
            company_name="Apple Inc.",
            current_price=150.0,
            metrics=sample_metrics,
            exit_strategy=sample_exit_strategy,
            chart_path="output/chart_AAPL.png",
            news=sample_news,
            company_info=sample_company_info
        )
        
        # メソッドが呼び出されたことを確認
        mock_instance.files_upload_v2.assert_called_once()
        mock_instance.chat_postMessage.assert_called_once()
    
    def test_post_stock_alert_handles_invalid_auth(
        self, mock_slack_client, sample_exit_strategy, sample_news,
        sample_metrics, sample_company_info
    ):
        """認証エラーが適切に処理されることを確認"""
        mock_instance = mock_slack_client.return_value
        mock_instance.files_upload_v2.return_value = {
            'file': {'permalink': 'https://files.slack.com/test.png'}
        }
        mock_response = {'error': 'invalid_auth'}
        mock_instance.chat_postMessage.side_effect = SlackApiError(
            message="Invalid auth",
            response=mock_response
        )
        
        notifier = SlackNotifier(token="test-token", channel="#test")
        
        with pytest.raises(SlackApiError):
            notifier.post_stock_alert(
                ticker="AAPL",
                company_name="Apple Inc.",
                current_price=150.0,
                metrics=sample_metrics,
                exit_strategy=sample_exit_strategy,
                chart_path="output/chart_AAPL.png",
                news=sample_news,
                company_info=sample_company_info
            )
    
    def test_post_stock_alert_handles_channel_not_found(
        self, mock_slack_client, sample_exit_strategy, sample_news,
        sample_metrics, sample_company_info
    ):
        """チャンネルが見つからないエラーが適切に処理されることを確認"""
        mock_instance = mock_slack_client.return_value
        mock_instance.files_upload_v2.return_value = {
            'file': {'permalink': 'https://files.slack.com/test.png'}
        }
        mock_response = {'error': 'channel_not_found'}
        mock_instance.chat_postMessage.side_effect = SlackApiError(
            message="Channel not found",
            response=mock_response
        )
        
        notifier = SlackNotifier(token="test-token", channel="#test")
        
        with pytest.raises(SlackApiError):
            notifier.post_stock_alert(
                ticker="AAPL",
                company_name="Apple Inc.",
                current_price=150.0,
                metrics=sample_metrics,
                exit_strategy=sample_exit_strategy,
                chart_path="output/chart_AAPL.png",
                news=sample_news,
                company_info=sample_company_info
            )

