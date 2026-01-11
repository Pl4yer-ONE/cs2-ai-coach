"""
Session Intelligence Analyzer
Detects patterns across the match: tilt, clusters, side differences.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class SessionFlag:
    """A detected session-level pattern."""
    flag_type: str  # tilt_streak, death_cluster, side_diff, eco_suicide
    description: str
    severity: str  # low, medium, high
    rounds_affected: List[int]
    evidence: Dict


class SessionAnalyzer:
    """
    Analyzes session-level patterns.
    
    Detects:
    - Tilt streaks (multiple deaths in quick succession)
    - Death clusters (same spot, same mistake)
    - CT vs T performance differences
    - Eco round suicides
    """
    
    # Thresholds
    TILT_DEATH_COUNT = 3  # 3+ deaths in window = tilt
    TILT_ROUND_WINDOW = 3  # Within 3 rounds
    CLUSTER_COUNT = 3  # 3+ deaths in same area
    SIDE_DIFF_THRESHOLD = 0.3  # 30% performance gap
    
    def analyze(
        self,
        death_contexts: List,  # DeathContext objects
        rounds_played: int,
        kills: int,
        deaths: int,
    ) -> List[SessionFlag]:
        """
        Run all session analyses.
        
        Returns list of detected flags.
        """
        flags = []
        
        # Detect tilt streaks
        tilt_flags = self._detect_tilt_streaks(death_contexts)
        flags.extend(tilt_flags)
        
        # Detect death clusters
        cluster_flags = self._detect_death_clusters(death_contexts)
        flags.extend(cluster_flags)
        
        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        flags.sort(key=lambda f: severity_order.get(f.severity, 3))
        
        return flags
    
    def _detect_tilt_streaks(self, death_contexts: List) -> List[SessionFlag]:
        """
        Detect tilt streaks: multiple deaths in consecutive rounds.
        """
        if len(death_contexts) < self.TILT_DEATH_COUNT:
            return []
        
        flags = []
        
        # Get death rounds
        death_rounds = [getattr(d, 'round_num', 0) for d in death_contexts]
        
        # Sliding window to find streaks
        for i in range(len(death_rounds) - self.TILT_DEATH_COUNT + 1):
            window = death_rounds[i:i + self.TILT_DEATH_COUNT]
            round_span = max(window) - min(window)
            
            if round_span <= self.TILT_ROUND_WINDOW:
                # Tilt streak detected
                affected_rounds = list(range(min(window), max(window) + 1))
                
                flags.append(SessionFlag(
                    flag_type="tilt_streak",
                    description=f"Died {len(window)} times across rounds {min(window)}-{max(window)}. Consider calling timeout.",
                    severity="medium",
                    rounds_affected=affected_rounds,
                    evidence={
                        "death_count": len(window),
                        "round_span": round_span,
                    }
                ))
                break  # Only report first tilt streak
        
        return flags
    
    def _detect_death_clusters(self, death_contexts: List) -> List[SessionFlag]:
        """
        Detect death clusters: repeated deaths in same area.
        """
        if len(death_contexts) < self.CLUSTER_COUNT:
            return []
        
        flags = []
        
        # Group by area
        area_deaths = defaultdict(list)
        for i, d in enumerate(death_contexts):
            area = getattr(d, 'map_area', 'unknown')
            if area != 'unknown':
                area_deaths[area].append({
                    'index': i,
                    'round': getattr(d, 'round_num', 0),
                    'traded': getattr(d, 'was_traded', False)
                })
        
        # Find clusters
        for area, deaths in area_deaths.items():
            if len(deaths) >= self.CLUSTER_COUNT:
                untraded = sum(1 for d in deaths if not d['traded'])
                rounds = [d['round'] for d in deaths]
                
                severity = "high" if untraded >= 3 else "medium"
                
                flags.append(SessionFlag(
                    flag_type="death_cluster",
                    description=f"{len(deaths)} deaths in {area} ({untraded} untraded). Avoid this position or change approach.",
                    severity=severity,
                    rounds_affected=rounds,
                    evidence={
                        "area": area,
                        "death_count": len(deaths),
                        "untraded_count": untraded,
                    }
                ))
        
        return flags
    
    def analyze_side_performance(
        self,
        ct_kills: int,
        ct_deaths: int,
        t_kills: int,
        t_deaths: int,
    ) -> Optional[SessionFlag]:
        """
        Analyze CT vs T side performance difference.
        """
        ct_kd = ct_kills / max(ct_deaths, 1)
        t_kd = t_kills / max(t_deaths, 1)
        
        if ct_kd == 0 and t_kd == 0:
            return None
        
        diff = abs(ct_kd - t_kd) / max(ct_kd, t_kd, 0.1)
        
        if diff < self.SIDE_DIFF_THRESHOLD:
            return None
        
        if ct_kd > t_kd:
            weak_side = "T"
            strong_side = "CT"
            weak_kd = t_kd
            strong_kd = ct_kd
        else:
            weak_side = "CT"
            strong_side = "T"
            weak_kd = ct_kd
            strong_kd = t_kd
        
        return SessionFlag(
            flag_type="side_diff",
            description=f"Underperforming on {weak_side} side ({weak_kd:.2f} K/D) vs {strong_side} ({strong_kd:.2f} K/D). Review {weak_side} strategy.",
            severity="medium" if diff < 0.5 else "high",
            rounds_affected=[],
            evidence={
                "ct_kd": round(ct_kd, 2),
                "t_kd": round(t_kd, 2),
                "weak_side": weak_side,
                "performance_gap": round(diff * 100, 1),
            }
        )
    
    def detect_eco_suicides(
        self,
        death_contexts: List,
        eco_rounds: List[int],  # Known eco rounds
    ) -> List[SessionFlag]:
        """
        Detect aggressive deaths during eco rounds.
        """
        if not eco_rounds:
            return []
        
        flags = []
        eco_deaths = []
        
        for d in death_contexts:
            round_num = getattr(d, 'round_num', 0)
            if round_num in eco_rounds:
                is_entry = getattr(d, 'is_entry_frag', False)
                if is_entry:
                    eco_deaths.append({
                        'round': round_num,
                        'area': getattr(d, 'map_area', 'unknown'),
                    })
        
        if len(eco_deaths) >= 2:
            areas = [d['area'] for d in eco_deaths]
            rounds = [d['round'] for d in eco_deaths]
            
            flags.append(SessionFlag(
                flag_type="eco_aggression",
                description=f"Pushed aggressively on {len(eco_deaths)} eco rounds. Save aggression for buy rounds.",
                severity="low",
                rounds_affected=rounds,
                evidence={
                    "eco_entry_deaths": len(eco_deaths),
                    "areas": areas,
                }
            ))
        
        return flags
