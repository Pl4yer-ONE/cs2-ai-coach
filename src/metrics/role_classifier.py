"""
Role Classifier
Strict rule-based role detection - PERFECTED.

Entry = intentionally takes first fights AND has success
Anchor = plays for trades/late round
AWPer = primary AWP user
Support = utility focus
Lurker = plays alone
"""

from typing import Dict, Any

class RoleClassifier:
    """
    Assigns roles based on deterministic player stats.
    
    IMPROVED LOGIC:
    1. AWP Kills > 30% of total -> AWPer
    2. Entry role requires BOTH:
       - High entry attempts (top 4 in lobby)
       - Entry success rate > 25% (not just dying first)
       OR entry_kills >= 2 (proven opener)
    3. Utility Usage > Team Avg -> Support
    4. Avg Distance from Team > Threshold -> Lurker
    5. Default -> Anchor (plays for trades)
    """
    
    def classify_roles(self, players: Dict[str, Any]) -> Dict[str, str]:
        """
        Assigns a role to each player ID based on features.
        Expects 'players' to be a dict of PlayerFeatures objects.
        """
        results = {}
        
        count = len(players)
        if count == 0: 
            return {}
        
        # Calculate averages
        total_flashes = sum(p.flashes_thrown for p in players.values())
        avg_flashes = total_flashes / count
        
        # Get entry thresholds - top 4 by entry_attempts (2 per team approx)
        entry_data = [(pid, p.entry_kills + p.entry_deaths) for pid, p in players.items()]
        entry_data.sort(key=lambda x: x[1], reverse=True)
        
        # Top 4 entry attempt players
        top_entry_pids = set(pid for pid, _ in entry_data[:4])
        
        # Assign Roles
        for pid, p in players.items():
            role = "Anchor"  # Default
            
            # Safe division
            total_kills = max(1, p.kills)
            awp_ratio = p.awp_kills / total_kills
            
            # Entry attempts = kills + deaths in opening duels
            entry_attempts = p.entry_kills + p.entry_deaths
            entry_success_rate = p.entry_kills / max(1, entry_attempts)
            
            # Logic Hierarchy (Strict Priority)
            
            # 1. AWPer - clear weapon identity 
            # Lowered threshold to 25% to better catch primary AWPers
            # Also check if they have reasonable AWP volume
            if awp_ratio >= 0.25 and p.awp_kills >= 2:
                role = "AWPer"
                
            # 2. Entry - must have BOTH volume AND success
            #    Options:
            #    a) High attempts + decent success rate (not just dying)
            #    b) At least 2 entry kills (proven opener regardless of deaths)
            elif pid in top_entry_pids and entry_attempts >= 3:
                if entry_success_rate >= 0.25 or p.entry_kills >= 2:
                    role = "Entry"
                else:
                    # High attempts but terrible success = NOT a real entry
                    # They're just dying first due to bad positioning
                    role = "Anchor"  # Re-classify as anchor (died in bad spots)
                    
            # 3. Support - utility focused
            elif p.flashes_thrown > avg_flashes * 1.2 and p.flashes_thrown >= 3:
                role = "Support"
                
            # 4. Lurker - plays alone
            elif p.avg_teammate_dist > 800:
                role = "Lurker"
                
            # 5. Default - Anchor
            else:
                role = "Anchor"
                
            results[pid] = role
            
        return results
