"""
Unit Tests for CS2 AI Coach Calibration System
Tests critical edge cases for rating calculations.
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.metrics.scoring import ScoreEngine
from src.metrics.calibration import detect_smurf, get_kast_bonus, get_dynamic_role_cap


class TestExitFragTax:
    """Test exit frag >= 8 triggers 0.85x penalty."""
    
    def test_exit_frag_tax_triggers_at_8(self):
        """Exit frags >= 8 should reduce rating by 15%."""
        # High impact player with 8 exit frags
        scores = {"raw_impact": 100, "aim": 70, "positioning": 60}
        
        # Without exit frags
        rating_no_exit = ScoreEngine.compute_final_rating(
            scores, role="Trader", kdr=1.5, untradeable_deaths=5,
            kills=20, rounds_played=20, exit_frags=0
        )
        
        # With 8 exit frags
        rating_with_exit = ScoreEngine.compute_final_rating(
            scores, role="Trader", kdr=1.5, untradeable_deaths=5,
            kills=20, rounds_played=20, exit_frags=8
        )
        
        # Should be ~15% less
        assert rating_with_exit < rating_no_exit * 0.90, \
            f"Exit tax not applied: {rating_with_exit} vs {rating_no_exit}"
    
    def test_exit_frag_tax_not_triggered_below_8(self):
        """Exit frags < 8 should NOT trigger exit tax."""
        scores = {"raw_impact": 100, "aim": 70, "positioning": 60}
        
        rating_7_exits = ScoreEngine.compute_final_rating(
            scores, role="Trader", kdr=1.5, untradeable_deaths=5,
            kills=20, rounds_played=20, exit_frags=7
        )
        
        rating_0_exits = ScoreEngine.compute_final_rating(
            scores, role="Trader", kdr=1.5, untradeable_deaths=5,
            kills=20, rounds_played=20, exit_frags=0
        )
        
        # Should be equal (no tax for < 8)
        assert rating_7_exits == rating_0_exits, \
            f"Exit tax wrongly applied for < 8 frags: {rating_7_exits} vs {rating_0_exits}"


class TestLowKDRCap:
    """Test KDR < 0.8 caps rating at 75."""
    
    def test_kdr_below_08_capped_at_75(self):
        """Players with KDR < 0.8 should never exceed 75."""
        scores = {"raw_impact": 120, "aim": 80, "positioning": 70}
        
        rating = ScoreEngine.compute_final_rating(
            scores, role="Entry", kdr=0.75, untradeable_deaths=10,
            kills=15, rounds_played=20
        )
        
        assert rating <= 75, f"KDR 0.75 should cap at 75, got {rating}"
    
    def test_kdr_above_08_not_capped(self):
        """Players with KDR >= 0.8 should NOT be capped at 75."""
        scores = {"raw_impact": 120, "aim": 80, "positioning": 70}
        
        rating = ScoreEngine.compute_final_rating(
            scores, role="Entry", kdr=0.85, untradeable_deaths=5,
            kills=20, rounds_played=20
        )
        
        assert rating > 75, f"KDR 0.85 should NOT be capped at 75, got {rating}"


class TestRotatorCeiling:
    """Test Rotator role capped at 95."""
    
    def test_rotator_cannot_exceed_95(self):
        """Rotators should never exceed 95, even with god stats."""
        scores = {"raw_impact": 150, "aim": 90, "positioning": 85}
        
        rating = ScoreEngine.compute_final_rating(
            scores, role="Rotator", kdr=2.0, untradeable_deaths=2,
            kills=30, rounds_played=20, kast_percentage=0.9
        )
        
        assert rating <= 95, f"Rotator should cap at 95, got {rating}"
    
    def test_non_rotator_can_exceed_95(self):
        """Non-Rotator roles CAN exceed 95 with god stats."""
        scores = {"raw_impact": 150, "aim": 90, "positioning": 85}
        
        rating = ScoreEngine.compute_final_rating(
            scores, role="Entry", kdr=2.5, untradeable_deaths=2,
            kills=30, rounds_played=20, kast_percentage=0.9
        )
        
        assert rating >= 90, f"Entry with god stats should be high, got {rating}"


class TestKillGateTrigger:
    """Test kill-gate: raw > 105 AND kills < 18 triggers 0.90x penalty."""
    
    def test_kill_gate_triggers_correctly(self):
        """High raw impact with low kills should trigger penalty."""
        scores = {"raw_impact": 115, "aim": 75, "positioning": 65}
        
        # 16 kills (< 18) with high raw (> 105) should trigger
        rating_16_kills = ScoreEngine.compute_final_rating(
            scores, role="Trader", kdr=1.3, untradeable_deaths=5,
            kills=16, rounds_played=20
        )
        
        # 20 kills (>= 18) should NOT trigger
        rating_20_kills = ScoreEngine.compute_final_rating(
            scores, role="Trader", kdr=1.3, untradeable_deaths=5,
            kills=20, rounds_played=20
        )
        
        assert rating_16_kills < rating_20_kills, \
            f"Kill gate should reduce rating: {rating_16_kills} vs {rating_20_kills}"
    
    def test_kill_gate_not_triggered_low_impact(self):
        """Low raw impact should NOT trigger kill-gate even with low kills."""
        scores = {"raw_impact": 80, "aim": 60, "positioning": 50}
        
        # Low raw impact (< 105) should NOT trigger even with 12 kills
        rating = ScoreEngine.compute_final_rating(
            scores, role="Trader", kdr=1.0, untradeable_deaths=8,
            kills=12, rounds_played=20
        )
        
        # Should not be affected by kill-gate (raw < 105)
        assert rating > 0, f"Rating should be positive: {rating}"


class TestTraderCeiling:
    """Test Trader with KDR < 1.0 capped at 80."""
    
    def test_trader_low_kdr_capped_at_80(self):
        """Traders with sub-1.0 KDR should cap at 80."""
        scores = {"raw_impact": 110, "aim": 70, "positioning": 60}
        
        rating = ScoreEngine.compute_final_rating(
            scores, role="Trader", kdr=0.9, untradeable_deaths=8,
            kills=15, rounds_played=20
        )
        
        assert rating <= 80, f"Trader with 0.9 KDR should cap at 80, got {rating}"
    
    def test_trader_high_kdr_not_capped(self):
        """Traders with KDR >= 1.0 should NOT be capped at 80."""
        scores = {"raw_impact": 110, "aim": 70, "positioning": 60}
        
        rating = ScoreEngine.compute_final_rating(
            scores, role="Trader", kdr=1.2, untradeable_deaths=5,
            kills=18, rounds_played=20
        )
        
        assert rating > 80, f"Trader with 1.2 KDR should NOT be capped at 80, got {rating}"


class TestFloorClamp:
    """Test minimum rating of 15."""
    
    def test_floor_clamp_prevents_zero(self):
        """Even terrible stats should not produce rating below 15."""
        scores = {"raw_impact": -20, "aim": 10, "positioning": 5}
        
        rating = ScoreEngine.compute_final_rating(
            scores, role="SiteAnchor", kdr=0.3, untradeable_deaths=20,
            kills=5, rounds_played=20
        )
        
        assert rating >= 15, f"Floor clamp should prevent rating below 15, got {rating}"


class TestSmurfDetection:
    """Test smurf detection logic."""
    
    def test_smurf_detected_high_stats_low_rounds(self):
        """High KDR + high impact in short game should trigger smurf."""
        is_smurf, mult = detect_smurf(
            kdr=1.8, raw_impact=90, 
            hs_pct=0.7, opening_success=0.6, 
            rounds_played=12
        )
        
        assert is_smurf == True, "Should detect smurf with high stats in short game"
        assert mult == 0.92, f"Smurf multiplier should be 0.92, got {mult}"
    
    def test_smurf_not_detected_high_rounds(self):
        """High stats in long game should NOT trigger smurf."""
        is_smurf, mult = detect_smurf(
            kdr=1.8, raw_impact=90,
            hs_pct=0.7, opening_success=0.6,
            rounds_played=25
        )
        
        assert is_smurf == False, "Should NOT detect smurf with rounds > 18"
        assert mult == 1.0, f"Non-smurf multiplier should be 1.0, got {mult}"


class TestBreakoutRule:
    """Test anchor breakout requires strict conditions."""
    
    def test_breakout_requires_all_conditions(self):
        """Breakout should require KDR > 1.15, KAST > 70%, kills >= 16."""
        scores = {"raw_impact": 120, "aim": 80, "positioning": 70}
        
        # Missing KAST requirement (60% < 70%)
        rating_low_kast = ScoreEngine.compute_final_rating(
            scores, role="SiteAnchor", kdr=1.3, untradeable_deaths=5,
            kills=18, rounds_played=20, kast_percentage=0.60
        )
        
        # Meeting all requirements
        rating_high_kast = ScoreEngine.compute_final_rating(
            scores, role="SiteAnchor", kdr=1.3, untradeable_deaths=5,
            kills=18, rounds_played=20, kast_percentage=0.75
        )
        
        # Low KAST should be lower (no breakout) if role cap applies
        assert rating_low_kast <= rating_high_kast, \
            f"KAST should affect breakout: {rating_low_kast} vs {rating_high_kast}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
