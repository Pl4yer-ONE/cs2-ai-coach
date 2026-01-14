# Copyright (c) 2026 Pl4yer-ONE
# This file is part of FragAudit.
# Licensed under GPLv3.

"""
Unit Tests for Prediction Models
Tests round win and player impact predictors.
"""

import pytest

from src.predict.win_model import (
    RoundFeatures,
    RoundPrediction,
    WinPredictor,
    predict_round_win,
    COEFFICIENTS,
    MIN_PROBABILITY,
    MAX_PROBABILITY,
)

from src.predict.player_model import (
    PlayerFeatures,
    PlayerPrediction,
    ImpactPredictor,
    predict_player_impact,
)


# ============================================================================
# Round Win Predictor Tests
# ============================================================================

class TestRoundFeatures:
    """Tests for RoundFeatures dataclass."""
    
    def test_default_values(self):
        """Features have sensible defaults."""
        f = RoundFeatures()
        assert f.team_alive == 5
        assert f.enemy_alive == 5
        assert f.mistake_count == 0
    
    def test_to_dict(self):
        """Serialization works."""
        f = RoundFeatures(team_economy=4500, mistake_count=2)
        d = f.to_dict()
        assert d['team_economy'] == 4500
        assert d['mistake_count'] == 2


class TestRoundPrediction:
    """Tests for RoundPrediction dataclass."""
    
    def test_to_dict(self):
        """Serialization includes all fields."""
        p = RoundPrediction(
            probability=0.65,
            confidence=0.8,
            features_used=4,
            dominant_factor="economy",
            factors={"economy": 0.1}
        )
        d = p.to_dict()
        assert d['probability'] == 0.65
        assert d['factors']['economy'] == 0.1


class TestWinPredictor:
    """Tests for WinPredictor."""
    
    def test_baseline_is_50_percent(self):
        """Equal conditions = ~50% win probability."""
        result = predict_round_win()
        assert 0.45 <= result.probability <= 0.55
    
    def test_economy_advantage_increases_probability(self):
        """Higher economy = higher win probability."""
        poor = predict_round_win(team_economy=1500, enemy_economy=4500)
        rich = predict_round_win(team_economy=4500, enemy_economy=1500)
        
        assert rich.probability > poor.probability
    
    def test_man_advantage_increases_probability(self):
        """More players = higher win probability."""
        down = predict_round_win(team_alive=3, enemy_alive=5)
        up = predict_round_win(team_alive=5, enemy_alive=3)
        
        assert up.probability > down.probability
    
    def test_mistakes_decrease_probability(self):
        """Mistakes = lower win probability."""
        clean = predict_round_win(mistake_count=0)
        sloppy = predict_round_win(mistake_count=3)
        
        assert clean.probability > sloppy.probability
    
    def test_probability_bounded(self):
        """Probability stays in bounds."""
        # Heavily favored
        favored = predict_round_win(
            team_economy=5000,
            enemy_economy=500,
            team_alive=5,
            enemy_alive=2
        )
        assert favored.probability <= MAX_PROBABILITY
        
        # Heavily unfavored
        unfavored = predict_round_win(
            team_economy=500,
            enemy_economy=5000,
            team_alive=2,
            enemy_alive=5,
            mistake_count=5
        )
        assert unfavored.probability >= MIN_PROBABILITY
    
    def test_dominant_factor_identified(self):
        """Identifies most impactful factor."""
        result = predict_round_win(team_alive=5, enemy_alive=2)
        assert result.dominant_factor in result.factors
    
    def test_custom_coefficients(self):
        """Custom coefficients can be passed."""
        custom = {"economy_diff": 0.30}  # Double economy weight
        predictor = WinPredictor(coefficients=custom)
        
        features = RoundFeatures(team_economy=5000, enemy_economy=2000)
        result = predictor.predict(features)
        
        # Should have higher economy factor
        assert result.factors["economy"] > 0.5


class TestExecuteStrategy:
    """Tests for strategy influence."""
    
    def test_execute_strategy_positive(self):
        """Execute strategy gives small boost."""
        no_strat = predict_round_win(strategy="")
        execute = predict_round_win(strategy="EXECUTE_A")
        
        assert execute.probability >= no_strat.probability
    
    def test_rush_strategy_risky(self):
        """Rush strategy is slightly negative."""
        no_strat = predict_round_win(strategy="")
        rush = predict_round_win(strategy="RUSH_B")
        
        assert rush.probability <= no_strat.probability


# ============================================================================
# Player Impact Predictor Tests
# ============================================================================

class TestPlayerFeatures:
    """Tests for PlayerFeatures dataclass."""
    
    def test_default_values(self):
        """Defaults are sensible."""
        f = PlayerFeatures()
        assert f.avg_rating == 1.0
        assert f.team_alive == 5
    
    def test_to_dict(self):
        """Serialization works."""
        f = PlayerFeatures(avg_rating=1.3, current_role="ENTRY")
        d = f.to_dict()
        assert d['avg_rating'] == 1.3


class TestPlayerPrediction:
    """Tests for PlayerPrediction dataclass."""
    
    def test_to_dict(self):
        """Serialization works."""
        p = PlayerPrediction(
            impact_probability=0.65,
            expected_rating=1.15,
            confidence=0.7,
            key_factors={"historical": 0.05}
        )
        d = p.to_dict()
        assert d['expected_rating'] == 1.15


class TestImpactPredictor:
    """Tests for ImpactPredictor."""
    
    def test_baseline_prediction(self):
        """Average player = ~50% impact."""
        result = predict_player_impact()
        assert 0.4 <= result.impact_probability <= 0.6
    
    def test_high_rating_increases_impact(self):
        """Better historical rating = higher predicted impact."""
        weak = predict_player_impact(avg_rating=0.7)
        strong = predict_player_impact(avg_rating=1.4)
        
        assert strong.impact_probability > weak.impact_probability
    
    def test_role_match_helps(self):
        """Playing primary role = higher impact."""
        mismatch = predict_player_impact(
            current_role="LURK",
            primary_role="ENTRY",
            role_frequency=0.8
        )
        match = predict_player_impact(
            current_role="ENTRY",
            primary_role="ENTRY",
            role_frequency=0.8
        )
        
        assert match.impact_probability >= mismatch.impact_probability
    
    def test_mistakes_hurt_impact(self):
        """Recent mistakes = lower predicted impact."""
        clean = predict_player_impact(recent_mistake_count=0)
        sloppy = predict_player_impact(recent_mistake_count=3)
        
        assert clean.impact_probability > sloppy.impact_probability
    
    def test_expected_rating_scaled(self):
        """Expected rating is on reasonable scale."""
        result = predict_player_impact(avg_rating=1.2)
        
        # Rating should be 0.5 + impact, so roughly 1.0-1.4 range
        assert 0.8 <= result.expected_rating <= 1.6
    
    def test_impact_bounded(self):
        """Impact stays in bounds."""
        result = predict_player_impact(
            avg_rating=2.0,
            equipment_value=5000
        )
        assert result.impact_probability <= 0.90


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Tests for model integration."""
    
    def test_predictions_are_explainable(self):
        """Both models expose factor breakdowns."""
        round_result = predict_round_win(
            team_economy=3000,
            enemy_economy=4000,
            mistake_count=1
        )
        
        player_result = predict_player_impact(
            avg_rating=1.1,
            current_role="SUPPORT"
        )
        
        # Both should have factor breakdowns
        assert len(round_result.factors) > 0
        assert len(player_result.key_factors) > 0
    
    def test_confidence_reflects_data_quality(self):
        """Confidence is higher with more data."""
        sparse = predict_round_win()  # Only defaults
        rich = predict_round_win(
            team_economy=4000,
            enemy_economy=3500,
            team_alive=4,
            enemy_alive=5,
            entry_count=1,
            mistake_count=1,
            strategy="EXECUTE_A"
        )
        
        assert rich.confidence >= sparse.confidence
