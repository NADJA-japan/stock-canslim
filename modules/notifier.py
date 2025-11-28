"""
CAN-SLIM US Stock Hunter Slack通知モジュール

このモジュールは適格銘柄をSlackに投稿する機能を提供します。
"""

import logging
from typing import Dict, List, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from modules.models import ExitStrategy, NewsItem

logger = logging.getLogger(__name__)


class SlackNotifier:
    """
    Slack通知を担当するクラス
    
    適格なCAN-SLIM銘柄の情報をSlackチャンネルに投稿します。
    チャート画像のアップロードとメッセージフォーマットを処理します。
    
    Attributes:
        client: Slack WebClientインスタンス
        channel: 投稿先のSlackチャンネル名
    """
    
    def __init__(self, token: str, channel: str):
        """
        SlackNotifierを初期化する
        
        Args:
            token: Slack Bot Token
            channel: 投稿先のSlackチャンネル名（例: "#stock-alerts"）
        """
        self.client = WebClient(token=token)
        self.channel = channel
        logger.info(f"SlackNotifier初期化完了: チャンネル={channel}")
    
    def post_stock_alert(
        self,
        ticker: str,
        company_name: str,
        current_price: float,
        metrics: Dict[str, float],
        exit_strategy: ExitStrategy,
        chart_path: str,
        news: List[NewsItem],
        company_info: Dict[str, str]
    ) -> None:
        """
        適格銘柄をSlackに投稿する
        
        Args:
            ticker: ティッカーシンボル
            company_name: 企業名
            current_price: 現在の株価
            metrics: 財務指標の辞書（eps_growth_q, revenue_growth_q, roe, rs_rating）
            exit_strategy: Exit戦略情報
            chart_path: チャート画像のファイルパス
            news: ニュース項目のリスト
            company_info: 企業情報の辞書（sector, industry）
            
        Raises:
            SlackApiError: Slack API呼び出しが失敗した場合
        """
        try:
            # メッセージをフォーマット
            message = self._format_message(
                ticker=ticker,
                company_name=company_name,
                current_price=current_price,
                metrics=metrics,
                exit_strategy=exit_strategy,
                news=news,
                company_info=company_info
            )
            
            # チャート画像をアップロード
            file_url = self._upload_chart(chart_path, ticker)
            
            # Slackにメッセージを投稿
            response = self.client.chat_postMessage(
                channel=self.channel,
                text=message['text'],
                blocks=message['blocks']
            )
            
            logger.info(f"Slack投稿成功: {ticker} (ts={response['ts']})")
            
        except SlackApiError as e:
            error_message = e.response.get('error', 'unknown_error')
            
            if error_message == 'invalid_auth':
                logger.error(f"Slack認証エラー: トークンが無効です")
                raise
            elif error_message == 'channel_not_found':
                logger.error(f"Slackチャンネルが見つかりません: {self.channel}")
                raise
            else:
                logger.error(f"Slack API エラー ({ticker}): {error_message}")
                raise
        except Exception as e:
            logger.error(f"Slack投稿中に予期しないエラーが発生しました ({ticker}): {e}")
            raise
    
    def _format_message(
        self,
        ticker: str,
        company_name: str,
        current_price: float,
        metrics: Dict[str, float],
        exit_strategy: ExitStrategy,
        news: List[NewsItem],
        company_info: Dict[str, str]
    ) -> Dict:
        """
        Slackメッセージをフォーマットする
        
        Args:
            ticker: ティッカーシンボル
            company_name: 企業名
            current_price: 現在の株価
            metrics: 財務指標の辞書
            exit_strategy: Exit戦略情報
            news: ニュース項目のリスト
            company_info: 企業情報の辞書
            
        Returns:
            Dict: Slackメッセージのペイロード（text, blocks）
        """
        # タイトル: ティッカーシンボル、企業名、現在株価
        title = f"🎯 *{ticker} - {company_name}* | ${current_price:.2f}"
        
        # Yahoo FinanceとTradingViewへのリンク
        yahoo_link = f"https://finance.yahoo.com/quote/{ticker}"
        tradingview_link = f"https://www.tradingview.com/symbols/{ticker}"
        
        # 財務指標セクション
        eps_growth = metrics.get('eps_growth_q', 0) * 100
        revenue_growth = metrics.get('revenue_growth_q', 0) * 100
        roe = metrics.get('roe', 0) * 100
        rs_rating = metrics.get('rs_rating', 'N/A')
        
        metrics_text = (
            f"📊 *財務指標*\n"
            f"• 四半期EPS成長率: {eps_growth:.1f}%\n"
            f"• 四半期売上成長率: {revenue_growth:.1f}%\n"
            f"• 年間ROE: {roe:.1f}%\n"
            f"• 相対力評価: {rs_rating}"
        )
        
        # Exit戦略セクション
        exit_text = (
            f"🎯 *Exit戦略*\n"
            f"*利益確定:*\n"
            f"• 目標価格: ${exit_strategy.profit_target_price:.2f}\n"
            f"• 条件: {exit_strategy.profit_condition}\n"
            f"• 理由: {exit_strategy.profit_reason}\n\n"
            f"*損切り:*\n"
            f"• 損切り価格: ${exit_strategy.stop_loss_price:.2f}\n"
            f"• 条件: {exit_strategy.stop_loss_condition}\n"
            f"• 理由: {exit_strategy.stop_loss_reason}"
        )
        
        # 企業情報セクション
        sector = company_info.get('sector', 'N/A')
        industry = company_info.get('industry', 'N/A')
        company_text = f"🏢 *企業情報*\n• セクター: {sector}\n• 業種: {industry}"
        
        # ニュースセクション
        news_text = "📰 *最新ニュース*\n"
        if news:
            for item in news[:2]:  # 最大2件
                news_text += f"• <{item.url}|{item.title}>\n"
        else:
            news_text += "• ニュースデータなし\n"
        
        # リンクセクション
        links_text = f"🔗 *リンク*\n• <{yahoo_link}|Yahoo Finance>\n• <{tradingview_link}|TradingView>"
        
        # プレーンテキスト版（通知用）
        plain_text = f"{title}\n\n{metrics_text}\n\n{exit_text}\n\n{company_text}\n\n{news_text}\n{links_text}"
        
        # Block Kit形式のメッセージ
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{ticker} - {company_name}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*現在株価:* ${current_price:.2f}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": metrics_text
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": exit_text
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": company_text
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": news_text
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": links_text
                }
            }
        ]
        
        return {
            'text': plain_text,
            'blocks': blocks
        }
    
    def _upload_chart(self, chart_path: str, ticker: str) -> str:
        """
        チャート画像をSlackにアップロードする
        
        Args:
            chart_path: チャート画像のファイルパス
            ticker: ティッカーシンボル
            
        Returns:
            str: アップロードされたファイルのURL
            
        Raises:
            SlackApiError: ファイルアップロードが失敗した場合
        """
        try:
            response = self.client.files_upload_v2(
                channel=self.channel,
                file=chart_path,
                title=f"{ticker} チャート",
                initial_comment=f"{ticker}の株価チャート"
            )
            
            file_url = response['file']['permalink']
            logger.info(f"チャート画像アップロード成功: {ticker}")
            return file_url
            
        except SlackApiError as e:
            logger.error(f"チャート画像アップロード失敗 ({ticker}): {e.response.get('error', 'unknown_error')}")
            raise
        except Exception as e:
            logger.error(f"チャート画像アップロード中に予期しないエラーが発生しました ({ticker}): {e}")
            raise

