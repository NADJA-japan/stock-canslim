"""
CAN-SLIM US Stock Hunter チャート生成モジュール

このモジュールはmplfinanceを使用してローソク足チャートを生成します。
- 50日・200日移動平均線の表示
- 出来高バーの表示
- ダークテーマスタイルの適用
"""

import os
import logging
from typing import Optional
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # GUIなしのバックエンドを使用
import mplfinance as mpf

logger = logging.getLogger(__name__)


class ChartGenerator:
    """
    株価チャート生成クラス
    
    mplfinanceを使用してローソク足チャートを生成し、
    移動平均線と出来高を含む視覚的なチャート画像を作成します。
    
    Attributes:
        output_dir: チャート画像の保存先ディレクトリ
    """
    
    def __init__(self, output_dir: str):
        """
        ChartGeneratorを初期化する
        
        Args:
            output_dir: チャート画像を保存するディレクトリパス
        """
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self) -> None:
        """
        出力ディレクトリが存在することを確認し、存在しない場合は作成する
        
        Raises:
            OSError: ディレクトリの作成に失敗した場合
        """
        try:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
                logger.info(f"出力ディレクトリを作成しました: {self.output_dir}")
        except OSError as e:
            logger.error(f"出力ディレクトリの作成に失敗しました: {e}")
            raise
    
    def generate_chart(self, ticker: str, data: pd.DataFrame) -> str:
        """
        ローソク足チャートを生成してファイルに保存する
        
        過去252取引日の株価データを使用して、以下を含むチャートを生成します：
        - ローソク足
        - 50日移動平均線（青色）
        - 200日移動平均線（赤色）
        - 出来高バー（下部パネル）
        
        Args:
            ticker: ティッカーシンボル（例: "AAPL"）
            data: 株価データ（OHLCV形式のDataFrame）
                  必須カラム: Open, High, Low, Close, Volume
                  インデックス: DatetimeIndex
        
        Returns:
            str: 生成されたチャート画像のファイルパス
        
        Raises:
            ValueError: データが不正な形式の場合
            OSError: ファイルの保存に失敗した場合（ディスク容量不足など）
        """
        # データの検証
        if data.empty:
            raise ValueError(f"株価データが空です: {ticker}")
        
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"必須カラムが不足しています: {missing_columns}")
        
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("データのインデックスはDatetimeIndexである必要があります")
        
        # 移動平均線を追加
        data_with_ma = self._add_moving_averages(data.copy())
        
        # ファイルパスを生成
        file_path = os.path.join(self.output_dir, f"chart_{ticker}.png")
        
        try:
            # ダークテーマスタイルを設定
            mc = mpf.make_marketcolors(
                up='#00ff00',      # 陽線: 緑
                down='#ff0000',    # 陰線: 赤
                edge='inherit',
                wick='inherit',
                volume='in',
                alpha=0.9
            )
            
            style = mpf.make_mpf_style(
                marketcolors=mc,
                gridcolor='#444444',
                gridstyle='--',
                y_on_right=False,
                rc={
                    'axes.facecolor': '#1e1e1e',
                    'axes.edgecolor': '#666666',
                    'axes.labelcolor': '#cccccc',
                    'figure.facecolor': '#1e1e1e',
                    'xtick.color': '#cccccc',
                    'ytick.color': '#cccccc'
                }
            )
            
            # 移動平均線の設定
            mav_colors = ['#3399ff', '#ff3333']  # 50日: 青、200日: 赤
            
            # チャートを生成
            mpf.plot(
                data_with_ma,
                type='candle',
                style=style,
                volume=True,
                mav=(50, 200),
                mavcolors=mav_colors,
                title=f'{ticker} - CAN-SLIM Stock Chart',
                ylabel='Price (USD)',
                ylabel_lower='Volume',
                figsize=(12, 8),
                savefig=file_path
            )
            
            logger.info(f"チャート画像を生成しました: {file_path}")
            return file_path
            
        except OSError as e:
            logger.error(f"チャート画像の保存に失敗しました: {e}")
            raise OSError(f"ディスク容量不足またはファイル保存エラー: {e}")
        except Exception as e:
            logger.error(f"チャート生成中にエラーが発生しました: {e}")
            raise
    
    def _add_moving_averages(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        50日・200日移動平均線をデータに追加する
        
        Args:
            data: 株価データ（OHLCV形式のDataFrame）
        
        Returns:
            pd.DataFrame: 移動平均線が追加されたデータ
        """
        # mplfinanceは内部で移動平均線を計算するため、
        # このメソッドは将来的な拡張のために残しておく
        return data
