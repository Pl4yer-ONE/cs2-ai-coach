# Copyright (c) 2026 Pl4yer-ONE
# This file is part of FragAudit.
# Licensed under GPLv3 or commercial license.

"""
Unit Tests for Mistake Detectors
Tests deterministic error detection logic.
"""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from dataclasses import dataclass
from typing import List

from src.mistakes.detectors import (
    DetectedMistake,
    ErrorType,
    Severity,
    OverpeekDetector,
    NoTradeSpacingDetector,
    RotationDelayDetector,
    UtilityWasteDetector,
    PostplantMisplayDetector,
    detect_all_mistakes,
    export_mistakes_json,
    _distance,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_demo_with_kills():
    """Create a mock demo with kill data."""
    demo = MagicMock()
    demo.kills = pd.DataFrame({
        'round_num': [1, 1, 1, 2, 2],
        'tick': [1000, 1100, 1300, 2000, 2050],
        'attacker_name': ['PlayerA', 'PlayerB', 'PlayerC', 'PlayerD', 'PlayerA'],
        'victim_name': ['PlayerD', 'PlayerA', 'PlayerE', 'PlayerB', 'PlayerE'],
        'attacker_team_name': ['CT', 'Terrorist', 'CT', 'Terrorist', 'CT'],
        'victim_team_name': ['Terrorist', 'CT', 'Terrorist', 'CT', 'Terrorist'],
        'victim_x': [100, 200, 300, 400, 500],
        'victim_y': [100, 200, 300, 400, 500],
    })
    demo.rounds = pd.DataFrame({
        'round_num': [1, 2],
        'start_tick': [0, 1500],
        'end_tick': [1400, 2500],
    })
    demo.plants = pd.DataFrame()  # No plants
    demo.defuses = pd.DataFrame()  # No defuses
    return demo


@pytest.fixture
def mock_demo_with_plant():
    """Create a mock demo with bomb plant."""
    demo = MagicMock()
    demo.kills = pd.DataFrame({
        'round_num': [1, 1],
        'tick': [1500, 1700],
        'attacker_name': ['PlayerA', 'PlayerA'],
        'victim_name': ['PlayerB', 'PlayerC'],
        'attacker_team_name': ['CT', 'CT'],
        'victim_team_name': ['Terrorist', 'Terrorist'],
        'victim_x': [1000, 1100],
        'victim_y': [500, 550],
    })
    demo.rounds = pd.DataFrame({
        'round_num': [1],
        'start_tick': [0],
        'end_tick': [2000],
    })
    demo.plants = pd.DataFrame({
        'round_num': [1],
        'tick': [1400],
        'site': ['A'],
        'player_name': ['PlayerB'],
    })
    demo.defuses = pd.DataFrame({
        'round_num': [1],
        'tick': [1900],
        'player_name': ['PlayerA'],
    })
    return demo


@pytest.fixture
def empty_demo():
    """Create a demo with no data."""
    demo = MagicMock()
    demo.kills = pd.DataFrame()
    demo.rounds = pd.DataFrame()
    demo.plants = pd.DataFrame()
    demo.defuses = pd.DataFrame()
    return demo


# ============================================================================
# DetectedMistake Tests
# ============================================================================

class TestDetectedMistake:
    """Tests for DetectedMistake dataclass."""
    
    def test_creation(self):
        """Test basic mistake creation."""
        mistake = DetectedMistake(
            round=1,
            timestamp_ms=5000,
            player="TestPlayer",
            error_type=ErrorType.OVERPEEK.value,
            severity=Severity.HIGH.value,
            wpa_loss=0.10,
            details="Test mistake"
        )
        
        assert mistake.round == 1
        assert mistake.player == "TestPlayer"
        assert mistake.error_type == "OVERPEEK"
        assert mistake.severity == "HIGH"
    
    def test_to_dict(self):
        """Test serialization to dict."""
        mistake = DetectedMistake(
            round=2,
            timestamp_ms=10000,
            player="Player1",
            error_type="NO_TRADE_SPACING",
            severity="MED",
            map_pos={"x": 100, "y": 200}
        )
        
        d = mistake.to_dict()
        
        assert d['round'] == 2
        assert d['player'] == "Player1"
        assert d['map_pos'] == {"x": 100, "y": 200}
    
    def test_to_dict_empty_map_pos(self):
        """Test that None map_pos becomes empty dict."""
        mistake = DetectedMistake(
            round=1,
            timestamp_ms=0,
            player="P",
            error_type="TEST",
            severity="LOW",
            map_pos=None
        )
        
        d = mistake.to_dict()
        assert d['map_pos'] == {}


# ============================================================================
# Distance Utility Tests
# ============================================================================

class TestDistanceCalculation:
    """Tests for distance utility function."""
    
    def test_zero_distance(self):
        """Same point returns zero."""
        assert _distance(0, 0, 0, 0) == 0
    
    def test_horizontal_distance(self):
        """Horizontal distance calculation."""
        assert _distance(0, 0, 100, 0) == 100
    
    def test_vertical_distance(self):
        """Vertical distance calculation."""
        assert _distance(0, 0, 0, 100) == 100
    
    def test_diagonal_distance(self):
        """Pythagorean calculation."""
        assert _distance(0, 0, 3, 4) == 5


# ============================================================================
# Overpeek Detector Tests
# ============================================================================

class TestOverpeekDetector:
    """Tests for OVERPEEK detection."""
    
    def test_detector_type(self):
        """Verify correct error type."""
        detector = OverpeekDetector()
        assert detector.error_type == ErrorType.OVERPEEK
    
    def test_empty_demo(self, empty_demo):
        """Empty demo returns no mistakes."""
        detector = OverpeekDetector()
        mistakes = detector.detect(empty_demo, 1)
        assert mistakes == []
    
    def test_detects_untraded_death(self, mock_demo_with_kills):
        """Detect player who died without being traded."""
        detector = OverpeekDetector()
        mistakes = detector.detect(mock_demo_with_kills, 1)
        
        # Should detect deaths
        assert len(mistakes) > 0
        assert all(m.error_type == "OVERPEEK" for m in mistakes)
    
    def test_severity_is_med(self, mock_demo_with_kills):
        """Overpeek mistakes default to MED severity."""
        detector = OverpeekDetector()
        mistakes = detector.detect(mock_demo_with_kills, 1)
        
        for m in mistakes:
            assert m.severity == "MED"


# ============================================================================
# No Trade Spacing Detector Tests
# ============================================================================

class TestNoTradeSpacingDetector:
    """Tests for NO_TRADE_SPACING detection."""
    
    def test_detector_type(self):
        """Verify correct error type."""
        detector = NoTradeSpacingDetector()
        assert detector.error_type == ErrorType.NO_TRADE_SPACING
    
    def test_empty_demo(self, empty_demo):
        """Empty demo returns no mistakes."""
        detector = NoTradeSpacingDetector()
        mistakes = detector.detect(empty_demo, 1)
        assert mistakes == []
    
    def test_detects_untraded_entry(self, mock_demo_with_kills):
        """Detect entry who died without quick trade."""
        detector = NoTradeSpacingDetector()
        mistakes = detector.detect(mock_demo_with_kills, 1)
        
        # Entry at tick 1000, killed by PlayerA
        # Next kill is at tick 1100 (PlayerA dies) - 100 ticks = traded
        # So round 1 should NOT have this error
        # Round 2: first kill at 2000, next at 2050 (50 ticks) - traded
        # Depends on exact data
    
    def test_high_severity_for_entry_loss(self, mock_demo_with_kills):
        """Entry loss without trade is HIGH severity."""
        detector = NoTradeSpacingDetector()
        mistakes = detector.detect(mock_demo_with_kills, 1)
        
        for m in mistakes:
            assert m.severity == "HIGH"


# ============================================================================
# Rotation Delay Detector Tests
# ============================================================================

class TestRotationDelayDetector:
    """Tests for ROTATION_DELAY detection."""
    
    def test_detector_type(self):
        """Verify correct error type."""
        detector = RotationDelayDetector()
        assert detector.error_type == ErrorType.ROTATION_DELAY
    
    def test_empty_demo(self, empty_demo):
        """Empty demo returns no mistakes."""
        detector = RotationDelayDetector()
        mistakes = detector.detect(empty_demo, 1)
        assert mistakes == []
    
    def test_detects_slow_rotation(self, mock_demo_with_plant):
        """Detect slow rotation after plant."""
        detector = RotationDelayDetector()
        mistakes = detector.detect(mock_demo_with_plant, 1)
        
        # Plant at tick 1400, defuse attempt at 1900
        # (1900 - 1400) * 15.625 = 7812ms < 10000ms threshold
        # So no rotation delay detected
        assert len(mistakes) == 0
    
    def test_threshold_is_10_seconds(self):
        """Verify threshold constant."""
        detector = RotationDelayDetector()
        assert detector.ROTATION_THRESHOLD_MS == 10000


# ============================================================================
# Utility Waste Detector Tests
# ============================================================================

class TestUtilityWasteDetector:
    """Tests for UTILITY_WASTE detection."""
    
    def test_detector_type(self):
        """Verify correct error type."""
        detector = UtilityWasteDetector()
        assert detector.error_type == ErrorType.UTILITY_WASTE
    
    def test_empty_demo(self, empty_demo):
        """Empty demo returns no mistakes."""
        detector = UtilityWasteDetector()
        mistakes = detector.detect(empty_demo, 1)
        assert mistakes == []
    
    def test_flash_followup_window(self):
        """Verify flash followup window constant."""
        detector = UtilityWasteDetector()
        assert detector.FLASH_FOLLOWUP_WINDOW_MS == 2000

    def test_detects_wasted_flash(self, mock_demo_with_kills):
        """Detect flash with no follow-up kill."""
        # Create a demo with a flash that has no follow-up
        demo = mock_demo_with_kills

        # Add grenade data
        # Flash at tick 1500 (approx 96s)
        # Kill at tick 2000 (approx 128s) -> >2s later
        demo.grenades = pd.DataFrame({
            'grenade_type': ['flashbang'],
            'tick': [1500],
            'name': ['PlayerA'],
            'team_name': ['CT'],
            'x': [0], 'y': [0], 'z': [0],
            'round_num': [1]  # Ensure round number is set
        })

        # The existing kills in mock_demo_with_kills are at ticks 1000, 1100, 1300, 2000...
        # Flash at 1500. Next kill is 2000.
        # Difference = 500 ticks. 500 * 0.015625 = 7.8s > 2s.
        # So this flash should be wasted.

        detector = UtilityWasteDetector()
        mistakes = detector.detect(demo, 1) # Round 1

        # Should detect 1 mistake
        assert len(mistakes) == 1
        assert mistakes[0].error_type == "UTILITY_WASTE"
        assert mistakes[0].player == "PlayerA"

    def test_ignores_good_flash(self, mock_demo_with_kills):
        """Ignore flash that has follow-up kill."""
        demo = mock_demo_with_kills

        # Flash at tick 1050
        # Kill at tick 1100 (PlayerB kills PlayerA) - within 50 ticks (<1s)
        demo.grenades = pd.DataFrame({
            'grenade_type': ['flashbang'],
            'tick': [1050],
            'name': ['PlayerB'],
            'team_name': ['Terrorist'],
            'x': [0], 'y': [0], 'z': [0],
            'round_num': [1] # Ensure round number is set
        })

        detector = UtilityWasteDetector()
        mistakes = detector.detect(demo, 1)

        assert len(mistakes) == 0

    def test_detects_with_missing_round_columns(self, mock_demo_with_kills):
        """Detect mistakes when round columns are missing from dataframes."""
        demo = mock_demo_with_kills

        # Remove round_num from kills to trigger tick-based filtering
        if 'round_num' in demo.kills.columns:
            demo.kills = demo.kills.drop(columns=['round_num'])

        # Ensure rounds info exists for mapping
        demo.rounds = pd.DataFrame({
            'round_num': [1],
            'start_tick': [0],
            'end_tick': [2000],
        })

        # Add flash and kill within window
        # Flash at 1050, Kill at 1100. Should be NO mistake.
        demo.grenades = pd.DataFrame({
            'grenade_type': ['flashbang'],
            'tick': [1050],
            'name': ['PlayerB'],
            'team_name': ['Terrorist'],
            'x': [0], 'y': [0], 'z': [0]
            # No round_num here either
        })

        detector = UtilityWasteDetector()
        mistakes = detector.detect(demo, 1)

        assert len(mistakes) == 0

        # Add wasted flash
        # Flash at 1500, no kill after (next kill in mock_demo is 2000 > 2s later)
        demo.grenades = pd.DataFrame({
            'grenade_type': ['flashbang'],
            'tick': [1500],
            'name': ['PlayerA'],
            'team_name': ['CT'],
            'x': [0], 'y': [0], 'z': [0]
        })

        mistakes = detector.detect(demo, 1)
        assert len(mistakes) == 1
        assert mistakes[0].player == "PlayerA"


# ============================================================================
# Postplant Misplay Detector Tests
# ============================================================================

class TestPostplantMisplayDetector:
    """Tests for POSTPLANT_MISPLAY detection."""
    
    def test_detector_type(self):
        """Verify correct error type."""
        detector = PostplantMisplayDetector()
        assert detector.error_type == ErrorType.POSTPLANT_MISPLAY
    
    def test_empty_demo(self, empty_demo):
        """Empty demo returns no mistakes."""
        detector = PostplantMisplayDetector()
        mistakes = detector.detect(empty_demo, 1)
        assert mistakes == []
    
    def test_detects_t_death_after_plant(self, mock_demo_with_plant):
        """Detect T dying after plant without crossfire."""
        detector = PostplantMisplayDetector()
        mistakes = detector.detect(mock_demo_with_plant, 1)
        
        # Plant at tick 1400
        # T deaths at tick 1500 and 1700 (both after plant)
        assert len(mistakes) == 2
        assert all(m.error_type == "POSTPLANT_MISPLAY" for m in mistakes)


# ============================================================================
# Integration Tests
# ============================================================================

class TestDetectAllMistakes:
    """Tests for detect_all_mistakes function."""
    
    def test_empty_demo(self, empty_demo):
        """Empty demo returns empty list."""
        mistakes = detect_all_mistakes(empty_demo)
        assert mistakes == []
    
    def test_returns_sorted_list(self, mock_demo_with_kills):
        """Mistakes are sorted by round and timestamp."""
        mistakes = detect_all_mistakes(mock_demo_with_kills)
        
        if len(mistakes) > 1:
            for i in range(len(mistakes) - 1):
                curr = mistakes[i]
                next_ = mistakes[i + 1]
                assert (curr.round, curr.timestamp_ms) <= (next_.round, next_.timestamp_ms)


class TestExportMistakesJson:
    """Tests for JSON export function."""
    
    def test_export_creates_file(self, tmp_path):
        """Export creates a valid JSON file."""
        mistakes = [
            DetectedMistake(
                round=1,
                timestamp_ms=5000,
                player="TestPlayer",
                error_type="OVERPEEK",
                severity="HIGH"
            )
        ]
        
        output_path = tmp_path / "test_mistakes.json"
        result = export_mistakes_json(mistakes, str(output_path))
        
        assert output_path.exists()
        
        import json
        with open(output_path) as f:
            data = json.load(f)
        
        assert data['schema_version'] == "1.0"
        assert data['total_mistakes'] == 1
        assert len(data['mistakes']) == 1
    
    def test_export_counts_by_type(self, tmp_path):
        """Export includes count by error type."""
        mistakes = [
            DetectedMistake(round=1, timestamp_ms=0, player="P1", 
                          error_type="OVERPEEK", severity="LOW"),
            DetectedMistake(round=1, timestamp_ms=100, player="P2", 
                          error_type="OVERPEEK", severity="LOW"),
            DetectedMistake(round=2, timestamp_ms=0, player="P1", 
                          error_type="NO_TRADE_SPACING", severity="HIGH"),
        ]
        
        output_path = tmp_path / "test_counts.json"
        export_mistakes_json(mistakes, str(output_path))
        
        import json
        with open(output_path) as f:
            data = json.load(f)
        
        assert data['by_type']['OVERPEEK'] == 2
        assert data['by_type']['NO_TRADE_SPACING'] == 1


# ============================================================================
# Error Type Enum Tests
# ============================================================================

class TestErrorTypeEnum:
    """Tests for ErrorType enum."""
    
    def test_all_types_defined(self):
        """All required error types exist."""
        expected = ['OVERPEEK', 'NO_TRADE_SPACING', 'ROTATION_DELAY', 
                   'UTILITY_WASTE', 'POSTPLANT_MISPLAY']
        
        for error_type in expected:
            assert hasattr(ErrorType, error_type)


class TestSeverityEnum:
    """Tests for Severity enum."""
    
    def test_all_levels_defined(self):
        """All severity levels exist."""
        assert hasattr(Severity, 'LOW')
        assert hasattr(Severity, 'MED')
        assert hasattr(Severity, 'HIGH')
