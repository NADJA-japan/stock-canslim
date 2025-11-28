"""
CAN-SLIM US Stock Hunter スクリーニングモジュールのテスト

このモジュールは以下のクラスをテストします：
- TechnicalFilter
- FundamentalFilter
- ExitStrategyCalculator
"""

import pytest
from modules.screener import FundamentalFilter, ExitStrategyCalculator
from config import Config


class TestFundamentalFilter:
    """FundamentalFilterクラスのテスト"""
    
    @pytest.fixture
    def filter(self):
        """テスト用のFundamentalFilterインスタンスを作成"""
        return FundamentalFilter(Config())
    
    def test_check_current_earnings_eps_growth_passes(self, filter):
        """EPS成長率が20%以上の場合、現在収益基準を満たす"""
        financial_data = {
            'quarterly_eps': [1.25, 1.10, 1.05, 1.00, 1.00],  # 25%成長
            'quarterly_revenue': [100, 95, 90, 85, 90]  # 11%成長（閾値未満）
        }
        
        passes, eps_growth, revenue_growth = filter.check_current_earnings(financial_data)
        
        assert passes is True
        assert eps_growth == pytest.approx(0.25, abs=0.01)
    
    def test_check_current_earnings_revenue_growth_passes(self, filter):
        """売上成長率が20%以上の場合、現在収益基準を満たす"""
        financial_data = {
            'quarterly_eps': [1.00, 0.95, 0.90, 0.85, 1.00],  # 0%成長
            'quarterly_revenue': [120, 110, 105, 100, 100]  # 20%成長
        }
        
        passes, eps_growth, revenue_growth = filter.check_current_earnings(financial_data)
        
        assert passes is True
        assert revenue_growth == pytest.approx(0.20, abs=0.01)
    
    def test_check_current_earnings_both_fail(self, filter):
        """EPS成長率も売上成長率も20%未満の場合、現在収益基準を満たさない"""
        financial_data = {
            'quarterly_eps': [1.10, 1.05, 1.00, 0.95, 1.00],  # 10%成長
            'quarterly_revenue': [110, 105, 100, 95, 100]  # 10%成長
        }
        
        passes, eps_growth, revenue_growth = filter.check_current_earnings(financial_data)
        
        assert passes is False
        assert eps_growth == pytest.approx(0.10, abs=0.01)
        assert revenue_growth == pytest.approx(0.10, abs=0.01)
    
    def test_check_current_earnings_insufficient_data(self, filter):
        """データが不足している場合、現在収益基準を満たさない"""
        financial_data = {
            'quarterly_eps': [1.20, 1.10],  # データ不足
            'quarterly_revenue': [120, 110]  # データ不足
        }
        
        passes, eps_growth, revenue_growth = filter.check_current_earnings(financial_data)
        
        assert passes is False
        assert eps_growth == 0.0
        assert revenue_growth == 0.0
    
    def test_check_annual_earnings_passes(self, filter):
        """ROEが15%以上の場合、年間収益基準を満たす"""
        financial_data = {
            'roe': 0.20  # 20%
        }
        
        passes, roe = filter.check_annual_earnings(financial_data)
        
        assert passes is True
        assert roe == 0.20
    
    def test_check_annual_earnings_fails(self, filter):
        """ROEが15%未満の場合、年間収益基準を満たさない"""
        financial_data = {
            'roe': 0.10  # 10%
        }
        
        passes, roe = filter.check_annual_earnings(financial_data)
        
        assert passes is False
        assert roe == 0.10
    
    def test_check_annual_earnings_no_data(self, filter):
        """ROEデータがない場合、年間収益基準を満たさない"""
        financial_data = {}
        
        passes, roe = filter.check_annual_earnings(financial_data)
        
        assert passes is False
        assert roe == 0.0
    
    def test_is_qualified_both_criteria_pass(self, filter):
        """C基準とA基準の両方を満たす場合、適格と判定される"""
        financial_data = {
            'quarterly_eps': [1.20, 1.10, 1.05, 1.00, 1.00],  # 20%成長
            'quarterly_revenue': [120, 110, 105, 100, 100],  # 20%成長
            'roe': 0.20,  # 20%
            'sector': 'Technology',
            'industry': 'Software'
        }
        
        is_qualified, metrics = filter.is_qualified(financial_data)
        
        assert is_qualified is True
        assert metrics['eps_growth_q'] == pytest.approx(0.20, abs=0.01)
        assert metrics['revenue_growth_q'] == pytest.approx(0.20, abs=0.01)
        assert metrics['roe'] == 0.20
        assert metrics['sector'] == 'Technology'
        assert metrics['industry'] == 'Software'
    
    def test_is_qualified_current_fails(self, filter):
        """C基準を満たさない場合、適格と判定されない"""
        financial_data = {
            'quarterly_eps': [1.10, 1.05, 1.00, 0.95, 1.00],  # 10%成長
            'quarterly_revenue': [110, 105, 100, 95, 100],  # 10%成長
            'roe': 0.20  # 20%
        }
        
        is_qualified, metrics = filter.is_qualified(financial_data)
        
        assert is_qualified is False
    
    def test_is_qualified_annual_fails(self, filter):
        """A基準を満たさない場合、適格と判定されない"""
        financial_data = {
            'quarterly_eps': [1.20, 1.10, 1.05, 1.00, 1.00],  # 20%成長
            'quarterly_revenue': [120, 110, 105, 100, 100],  # 20%成長
            'roe': 0.10  # 10%
        }
        
        is_qualified, metrics = filter.is_qualified(financial_data)
        
        assert is_qualified is False
    
    def test_is_qualified_both_fail(self, filter):
        """C基準とA基準の両方を満たさない場合、適格と判定されない"""
        financial_data = {
            'quarterly_eps': [1.10, 1.05, 1.00, 0.95, 1.00],  # 10%成長
            'quarterly_revenue': [110, 105, 100, 95, 100],  # 10%成長
            'roe': 0.10  # 10%
        }
        
        is_qualified, metrics = filter.is_qualified(financial_data)
        
        assert is_qualified is False


class TestExitStrategyCalculator:
    """ExitStrategyCalculatorクラスのテスト"""
    
    @pytest.fixture
    def calculator(self):
        """テスト用のExitStrategyCalculatorインスタンスを作成"""
        return ExitStrategyCalculator(Config())
    
    def test_calculate_profit_target_basic(self, calculator):
        """利益確定目標価格が正しく計算される（現在価格の120%）"""
        current_price = 100.0
        ma_10 = 95.0
        
        result = calculator.calculate_profit_target(current_price, ma_10)
        
        # 目標価格は現在価格の120%
        assert result['target_price'] == pytest.approx(120.0, abs=0.01)
        assert 'condition' in result
        assert 'reason' in result
        assert '10日移動平均線' in result['condition']
        assert '10日移動平均線' in result['reason']
    
    def test_calculate_profit_target_different_prices(self, calculator):
        """異なる株価でも利益確定目標価格が正しく計算される"""
        test_cases = [
            (50.0, 60.0),    # 50 * 1.20 = 60
            (150.0, 180.0),  # 150 * 1.20 = 180
            (25.5, 30.6),    # 25.5 * 1.20 = 30.6
        ]
        
        for current_price, expected_target in test_cases:
            result = calculator.calculate_profit_target(current_price, current_price * 0.95)
            assert result['target_price'] == pytest.approx(expected_target, abs=0.01)
    
    def test_calculate_profit_target_includes_ma_10_in_condition(self, calculator):
        """Exit条件に10日移動平均線の値が含まれる"""
        current_price = 100.0
        ma_10 = 95.5
        
        result = calculator.calculate_profit_target(current_price, ma_10)
        
        # 条件に10日移動平均線の値が含まれることを確認
        assert '$95.50' in result['condition'] or '95.5' in result['condition']
    
    def test_calculate_stop_loss_basic(self, calculator):
        """損切り価格が正しく計算される（現在価格の93%）"""
        current_price = 100.0
        ma_50 = 90.0
        
        result = calculator.calculate_stop_loss(current_price, ma_50)
        
        # 損切り価格は現在価格の93%
        assert result['stop_price'] == pytest.approx(93.0, abs=0.01)
        assert 'ma_stop_condition' in result
        assert 'reason' in result
        assert '50日移動平均線' in result['ma_stop_condition']
        assert '7%' in result['reason']
    
    def test_calculate_stop_loss_different_prices(self, calculator):
        """異なる株価でも損切り価格が正しく計算される"""
        test_cases = [
            (50.0, 46.5),    # 50 * 0.93 = 46.5
            (150.0, 139.5),  # 150 * 0.93 = 139.5
            (25.0, 23.25),   # 25 * 0.93 = 23.25
        ]
        
        for current_price, expected_stop in test_cases:
            result = calculator.calculate_stop_loss(current_price, current_price * 0.9)
            assert result['stop_price'] == pytest.approx(expected_stop, abs=0.01)
    
    def test_calculate_stop_loss_ma_50_threshold(self, calculator):
        """50日移動平均線の3%下の閾値が正しく計算される"""
        current_price = 100.0
        ma_50 = 90.0
        
        result = calculator.calculate_stop_loss(current_price, ma_50)
        
        # 50日移動平均線の3%下 = 90 * 0.97 = 87.3
        expected_threshold = ma_50 * 0.97
        assert f'${expected_threshold:.2f}' in result['ma_stop_condition']
    
    def test_calculate_stop_loss_includes_both_conditions(self, calculator):
        """損切り理由に7%下落と50日移動平均線の両方の条件が含まれる"""
        current_price = 100.0
        ma_50 = 90.0
        
        result = calculator.calculate_stop_loss(current_price, ma_50)
        
        # 両方の条件が理由に含まれることを確認
        assert '7%' in result['reason']
        assert '50日移動平均線' in result['reason']
        assert '3%' in result['reason']
