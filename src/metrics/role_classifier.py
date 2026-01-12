"""
Role Classifier v2.2
Strict rule-based role detection with granular anchor split.

Roles:
- Entry = takes first fights with success + flash/trade support
- AWPer = primary AWP user
- Support = utility focused (flashes OR blinded enemies)
- Lurker = plays alone (>800u avg distance)
- Rotator = mid-distance (600-800u), trades often
- Trader = close-mid distance (250-600u), high trade involvement
- SiteAnchor = holds site, low movement (<250u)
"""

from typing import Dict, Any, List, Tuple

# Role quotas per team
MAX_AWPERS_PER_TEAM = 1
MAX_ENTRIES_PER_TEAM = 2

class RoleClassifier:
    """
    Assigns roles based on deterministic player stats.
    
    IMPROVED LOGIC v2.2:
    1. AWPer: AWP kills > 25% + >= 2 kills
    2. Entry: top entry attempts + success rate + trade/flash support
    3. Support: flashes > team_avg OR enemies_blinded > 3
    4. Lurker: plays alone (>800u)
    5. Rotator: mid-distance (600-800u), good trades
    6. Trader: close-mid (250-600u), high trade involvement
    7. SiteAnchor: holds site (<250u)
    """
    
    def classify_roles(self, players: Dict[str, Any]) -> Dict[str, str]:
        """
        Assigns a role to each player ID based on features.
        """
        results = {}
        
        count = len(players)
        if count == 0: 
            return {}
        
        # Calculate averages
        total_flashes = sum(p.flashes_thrown for p in players.values())
        avg_flashes = total_flashes / count if count > 0 else 0
        
        total_blinded = sum(p.enemies_blinded for p in players.values())
        avg_blinded = total_blinded / count if count > 0 else 0
        
        # Get entry thresholds - top 4 by entry_attempts
        entry_data = [(pid, p.entry_kills + p.entry_deaths) for pid, p in players.items()]
        entry_data.sort(key=lambda x: x[1], reverse=True)
        top_entry_pids = set(pid for pid, _ in entry_data[:4])
        
        # PHASE 1: Initial role assignment with scores
        role_candidates: Dict[str, Tuple[str, float]] = {}
        
        for pid, p in players.items():
            role = "SiteAnchor"  # New default
            score = 0.0
            
            total_kills = max(1, p.kills)
            awp_ratio = p.awp_kills / total_kills
            
            entry_attempts = p.entry_kills + p.entry_deaths
            entry_success_rate = p.entry_kills / max(1, entry_attempts)
            
            # Calculate trade involvement
            tradeable_ratio = p.tradeable_deaths / max(1, p.deaths)
            
            # Get distance category
            dist = p.avg_teammate_dist
            
            # Logic Hierarchy (Strict Priority)
            
            # 1. AWPer - clear weapon identity 
            if awp_ratio >= 0.25 and p.awp_kills >= 2:
                role = "AWPer"
                score = p.awp_kills * awp_ratio
                
            # 2. Entry - must have volume AND success
            elif pid in top_entry_pids and entry_attempts >= 3:
                if entry_success_rate >= 0.25 or p.entry_kills >= 2:
                    role = "Entry"
                    # Quality score: success rate + tradeable position + flash support
                    flash_bonus = 1.0 if p.flashes_thrown >= 2 else 0.5
                    score = (entry_success_rate * p.entry_kills) + (tradeable_ratio * 2) + flash_bonus
                else:
                    # Failed entry -> Trader
                    role = "Trader"
                    score = 0
                    
            # 3. Support - utility focused (FIXED: looser criteria)
            # Now: flashes > avg OR enemies_blinded > 3
            elif p.flashes_thrown > avg_flashes or p.enemies_blinded >= 3:
                role = "Support"
                score = p.flashes_thrown + (p.enemies_blinded * 2)
                
            # 4. Lurker - plays completely alone
            elif dist > 800:
                role = "Lurker"
                score = dist
            
            # 5. Rotator - mid-far distance (600-800u), good at trading
            elif 600 < dist <= 800 and tradeable_ratio >= 0.3:
                role = "Rotator"
                score = tradeable_ratio * dist
                
            # 6. Trader - close-mid distance (250-600u)
            elif 250 < dist <= 600:
                role = "Trader"
                score = tradeable_ratio * 10
                
            # 7. SiteAnchor - holds site (<250u), default
            else:
                role = "SiteAnchor"
                score = 0
                
            role_candidates[pid] = (role, score)
        
        # PHASE 2: Enforce per-team quotas
        all_pids = list(players.keys())
        team_size = len(all_pids) // 2
        
        team1_pids = set(all_pids[:team_size])
        team2_pids = set(all_pids[team_size:])
        
        def apply_quota_per_team(role_name: str, max_per_team: int, team_pids: set):
            """Demote excess role holders in a single team."""
            candidates = [(pid, score) for pid, (role, score) in role_candidates.items() 
                         if role == role_name and pid in team_pids]
            
            if len(candidates) <= max_per_team:
                return
            
            candidates.sort(key=lambda x: x[1], reverse=True)
            
            for pid, _ in candidates[max_per_team:]:
                # Demote to Trader instead of SiteAnchor
                role_candidates[pid] = ("Trader", 0)
        
        # Apply quotas
        apply_quota_per_team("AWPer", MAX_AWPERS_PER_TEAM, team1_pids)
        apply_quota_per_team("AWPer", MAX_AWPERS_PER_TEAM, team2_pids)
        apply_quota_per_team("Entry", MAX_ENTRIES_PER_TEAM, team1_pids)
        apply_quota_per_team("Entry", MAX_ENTRIES_PER_TEAM, team2_pids)
        
        # Extract final roles
        for pid, (role, _) in role_candidates.items():
            results[pid] = role
            
        return results
