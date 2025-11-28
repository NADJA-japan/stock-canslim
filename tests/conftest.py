"""
CAN-SLIM US Stock Hunter テスト用のpytest設定とフィクスチャ
"""

import pytest
from hypothesis import settings

# Hypothesisプロファイルを登録
settings.register_profile("ci", max_examples=100, deadline=None)
settings.register_profile("dev", max_examples=20, deadline=None)

# デフォルトでdevプロファイルを読み込む（CIでは--hypothesis-profile=ciで上書き）
settings.load_profile("dev")
