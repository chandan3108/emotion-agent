"""
Reciprocity Ledger - Balance Tracking
Distribution-based balance computation with stochastic imbalance detection.
"""

import random
import math
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import numpy as np

# Entry type values (ranges, not fixed)
ENTRY_VALUES = {
    "vulnerability": {"small": (0.15, 0.05), "medium": (0.45, 0.1), "deep": (0.75, 0.15), "extremely": (0.95, 0.05)},
    "support": {"quick_checkin": (0.1, 0.05), "active_listening": (0.4, 0.1), "consistent": (0.6, 0.15), "significant_sacrifice": (0.9, 0.1)},
    "effort": {"minimal": (0.1, 0.05), "moderate": (0.5, 0.1), "significant": (0.8, 0.15)},
    "repair": {"surface_apology": (0.2, 0.1), "genuine": (0.6, 0.15), "with_behavior_change": (0.9, 0.1), "with_vulnerability": (1.0, 0.0)},
    "forgiveness": {"quick": (0.2, 0.1), "reluctant": (0.5, 0.15), "genuine": (0.8, 0.1), "with_continued_trust": (1.0, 0.0)},
    "celebration": {"polite": (0.1, 0.05), "genuine": (0.5, 0.15), "enthusiastic": (0.8, 0.1), "sacrifice": (1.0, 0.0)},
    "initiation": {"low_effort": (0.2, 0.1), "thoughtful": (0.5, 0.15), "despite_uncertainty": (0.8, 0.1), "vulnerable": (1.0, 0.0)}
}

LOOKBACK_DAYS = 30
RECENT_WEIGHT = 0.7  # Weight for recent entries


class ReciprocityLedger:
    """
    Tracks reciprocity balance with stochastic computation.
    """
    
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self._init_ledger()
    
    def _init_ledger(self):
        """Initialize ledger from state."""
        if "relationship_ledger" not in self.state:
            self.state["relationship_ledger"] = {"entries": [], "balance": 0.0}
        
        ledger = self.state["relationship_ledger"]
        self.entries = ledger.get("entries", [])
        self.balance = ledger.get("balance", 0.0)
    
    def add_entry(self, entry_type: str, subtype: str, from_entity: str,
                 emotional_weight: float = 0.5, context: Optional[Dict[str, Any]] = None):
        """
        Add entry to ledger with stochastic value.
        """
        # Get value distribution for this entry type/subtype
        if entry_type not in ENTRY_VALUES or subtype not in ENTRY_VALUES[entry_type]:
            # Default
            value_mean, value_std = 0.5, 0.15
        else:
            value_mean, value_std = ENTRY_VALUES[entry_type][subtype]
        
        # Sample effort value from distribution
        effort_value = max(0.0, min(1.0, np.random.normal(value_mean, value_std)))
        
        # Weighted value = effort × emotional_weight
        weighted_value = effort_value * emotional_weight
        
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": entry_type,
            "subtype": subtype,
            "from": from_entity,  # 'user' or 'ai'
            "effort_value": effort_value,
            "emotional_weight": emotional_weight,
            "weighted_value": weighted_value,
            "context": context or {}
        }
        
        self.entries.append(entry)
        
        # Recompute balance
        self._recompute_balance()
    
    def _recompute_balance(self):
        """
        Recompute balance score using stochastic weighting.
        Balance ∈ [-1, +1]: -1 (AI overextended), 0 (balanced), +1 (user overextended)
        """
        now = datetime.now(timezone.utc)
        cutoff_date = now - timedelta(days=LOOKBACK_DAYS)
        
        # Filter recent entries
        recent_entries = [e for e in self.entries 
                         if datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")) >= cutoff_date]
        
        if not recent_entries:
            self.balance = 0.0
            return
        
        # Compute weighted sums (stochastic weighting)
        ai_sum = 0.0
        user_sum = 0.0
        total_weight = 0.0
        
        for entry in recent_entries:
            entry_time = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
            days_ago = (now - entry_time).days
            
            # Time-based weight (recent = higher weight, but stochastic)
            time_weight_mean = RECENT_WEIGHT if days_ago < 7 else (1 - RECENT_WEIGHT)
            time_weight_std = 0.15
            time_weight = max(0.0, min(1.0, np.random.normal(time_weight_mean, time_weight_std)))
            
            # Exponential decay for older entries (stochastic decay rate)
            decay_rate_mean = 0.05
            decay_rate_std = 0.01
            decay_rate = max(0.0, np.random.normal(decay_rate_mean, decay_rate_std))
            time_weight *= math.exp(-decay_rate * days_ago)
            
            weighted_value = entry["weighted_value"] * time_weight
            
            if entry["from"] == "ai":
                ai_sum += weighted_value
            elif entry["from"] == "user":
                user_sum += weighted_value
            
            total_weight += time_weight
        
        # Normalize
        if total_weight > 0:
            ai_normalized = ai_sum / total_weight
            user_normalized = user_sum / total_weight
            
            # Balance = (user - ai) / max(user, ai, 1) to get [-1, +1]
            diff = user_normalized - ai_normalized
            max_val = max(user_normalized, ai_normalized, 0.1)  # Avoid division by zero
            
            # Add noise (uncertainty in balance calculation)
            noise = np.random.normal(0, 0.05)
            self.balance = max(-1.0, min(1.0, (diff / max_val) + noise))
        else:
            self.balance = 0.0
    
    def detect_imbalance(self) -> Dict[str, Any]:
        """
        Detect reciprocity imbalance (stochastic detection).
        """
        # Sample threshold from distribution (not fixed)
        imbalance_threshold_mean = 0.4
        imbalance_threshold_std = 0.1
        threshold = abs(np.random.normal(imbalance_threshold_mean, imbalance_threshold_std))
        
        is_imbalanced = abs(self.balance) > threshold
        
        result = {
            "is_imbalanced": is_imbalanced,
            "balance": self.balance,
            "threshold_used": threshold,
            "direction": None,
            "severity": 0.0
        }
        
        if is_imbalanced:
            if self.balance < -threshold:
                result["direction"] = "ai_overextended"
                result["severity"] = min(1.0, abs(self.balance))
            elif self.balance > threshold:
                result["direction"] = "user_overextended"
                result["severity"] = min(1.0, abs(self.balance))
        
        return result
    
    def get_imbalance_response(self, imbalance: Dict[str, Any],
                              psyche_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get response to imbalance (stochastic).
        AI overextended → gradually increase distance, reduce initiative.
        """
        if not imbalance["is_imbalanced"]:
            return {"action": "none", "distance_adjustment": 0.0, "initiative_reduction": 0.0}
        
        if imbalance["direction"] == "ai_overextended":
            # AI is overextended - increase distance, reduce initiative
            severity = imbalance["severity"]
            
            # Sample adjustments from distributions
            distance_adjustment_mean = 0.1 + 0.2 * severity  # More severe = more distance
            distance_adjustment_std = 0.05
            distance_adjustment = max(0.0, min(0.5, 
                np.random.normal(distance_adjustment_mean, distance_adjustment_std)))
            
            initiative_reduction_mean = 0.15 + 0.25 * severity
            initiative_reduction_std = 0.05
            initiative_reduction = max(0.0, min(0.5,
                np.random.normal(initiative_reduction_mean, initiative_reduction_std)))
            
            return {
                "action": "increase_distance",
                "distance_adjustment": distance_adjustment,
                "initiative_reduction": initiative_reduction,
                "reason": "reciprocity_imbalance_ai_overextended",
                "severity": severity
            }
        else:
            # User overextended - can be more generous (but not always)
            # Sometimes humans don't notice or don't care
            notice_probability = 0.6  # 60% chance to notice
            if random.random() < notice_probability:
                return {
                    "action": "maintain_generosity",
                    "distance_adjustment": 0.0,
                    "initiative_reduction": 0.0,
                    "reason": "user_overextended_but_maintaining"
                }
            else:
                return {"action": "none"}
    
    def get_recent_balance_trend(self, days: int = 7) -> Dict[str, Any]:
        """
        Get recent balance trend (stochastic analysis).
        """
        now = datetime.now(timezone.utc)
        cutoff_date = now - timedelta(days=days)
        
        recent_entries = [e for e in self.entries 
                         if datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")) >= cutoff_date]
        
        if len(recent_entries) < 3:
            return {"trend": "insufficient_data", "slope": 0.0}
        
        # Compute balance over time (with noise)
        time_balances = []
        for i in range(days):
            day_cutoff = now - timedelta(days=i+1)
            day_entries = [e for e in recent_entries 
                          if datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")) >= day_cutoff]
            
            if day_entries:
                ai_sum = sum(e["weighted_value"] for e in day_entries if e["from"] == "ai")
                user_sum = sum(e["weighted_value"] for e in day_entries if e["from"] == "user")
                day_balance = user_sum - ai_sum
                # Add noise
                day_balance += np.random.normal(0, 0.1)
                time_balances.append((i, day_balance))
        
        if len(time_balances) < 2:
            return {"trend": "insufficient_data", "slope": 0.0}
        
        # Compute slope (trend)
        x = [t[0] for t in time_balances]
        y = [t[1] for t in time_balances]
        
        if len(set(x)) > 1:
            slope = np.polyfit(x, y, 1)[0]
        else:
            slope = 0.0
        
        # Classify trend
        if slope > 0.05:
            trend = "improving_for_user"
        elif slope < -0.05:
            trend = "improving_for_ai"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "slope": slope,
            "current_balance": self.balance
        }
    
    def save_to_state(self):
        """Save ledger back to state."""
        # Keep only last 1000 entries (prevent unbounded growth)
        self.entries = self.entries[-1000:]
        
        self.state["relationship_ledger"] = {
            "entries": self.entries,
            "balance": self.balance
        }




