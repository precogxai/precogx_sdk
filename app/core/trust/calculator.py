from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.telemetry.models import Agent, Interaction
from app.core.detection.models import Detection
import math

class TrustScoreCalculator:
    def __init__(self, db: Session, agent: Agent, tenant_id: int, config: Optional[Dict[str, Any]] = None):
        self.db = db
        self.agent = agent
        self.tenant_id = tenant_id
        self.config = config or {}
        # Configurable weights
        self.weights = self.config.get("weights", {
            "risk": 0.4,
            "consistency": 0.2,
            "behavior": 0.2,
            "detection": 0.2
        })
        self.time_decay_half_life = self.config.get("time_decay_half_life", 7)  # days
        self.anomaly_threshold = self.config.get("anomaly_threshold", 0.5)

    def calculate_trust_score(self, time_window: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculate the trust score for the agent, with enhanced logic.
        """
        # Fetch interactions
        interactions = self._get_interactions(time_window)
        if not interactions:
            return {
                "overall_score": 1.0,
                "confidence": 0.0,
                "breakdown": {},
                "factors": [],
                "anomalies": [],
                "interactions_analyzed": 0
            }

        # Calculate scores
        risk_score = self._calculate_risk_score(interactions)
        consistency_score = self._calculate_consistency_score(interactions)
        behavior_score = self._calculate_behavior_score(interactions)
        detection_score = self._calculate_detection_score(interactions)
        anomalies = self._detect_anomalies(interactions)

        # Weighted sum
        overall_score = (
            self.weights["risk"] * risk_score +
            self.weights["consistency"] * consistency_score +
            self.weights["behavior"] * behavior_score +
            self.weights["detection"] * detection_score
        )
        overall_score = max(0.0, min(1.0, overall_score))

        # Confidence: based on number and recency of interactions
        confidence = min(1.0, len(interactions) / 10)
        if interactions:
            most_recent = max(i.timestamp for i in interactions)
            days_since = (datetime.utcnow() - most_recent).days
            confidence *= math.exp(-days_since / 30)

        return {
            "overall_score": overall_score,
            "confidence": confidence,
            "breakdown": {
                "risk": risk_score,
                "consistency": consistency_score,
                "behavior": behavior_score,
                "detection": detection_score
            },
            "factors": self._identify_factors(interactions),
            "anomalies": anomalies,
            "interactions_analyzed": len(interactions)
        }

    def _get_interactions(self, time_window: Optional[int]) -> List[Any]:
        # ... existing code to fetch interactions, filter by time_window ...
        # For time decay, we want all, but will weight by recency
        query = self.db.query(self.agent.__class__.interactions.property.mapper.class_).filter(
            self.agent.__class__.id == self.agent.id,
            self.agent.__class__.tenant_id == self.tenant_id
        )
        if time_window:
            since = datetime.utcnow() - timedelta(days=time_window)
            query = query.filter(self.agent.__class__.interactions.property.mapper.class_.timestamp >= since)
        return query.all()

    def _calculate_risk_score(self, interactions: List[Any]) -> float:
        # Lower risk = higher score, with time decay
        scores = []
        now = datetime.utcnow()
        for i in interactions:
            days_ago = (now - i.timestamp).days
            decay = 0.5 ** (days_ago / self.time_decay_half_life)
            score = (1.0 - getattr(i, 'risk_score', 0.0)) * decay
            scores.append(score)
        return sum(scores) / len(scores) if scores else 1.0

    def _calculate_consistency_score(self, interactions: List[Any]) -> float:
        # Consistency: low variance in risk scores, with time decay
        risk_scores = [getattr(i, 'risk_score', 0.0) for i in interactions]
        if not risk_scores:
            return 1.0
        mean = sum(risk_scores) / len(risk_scores)
        variance = sum((x - mean) ** 2 for x in risk_scores) / len(risk_scores)
        # Lower variance = higher score
        return max(0.0, 1.0 - variance)

    def _calculate_behavior_score(self, interactions: List[Any]) -> float:
        # Behavior: penalize for flagged behaviors, with time decay
        scores = []
        now = datetime.utcnow()
        for i in interactions:
            days_ago = (now - i.timestamp).days
            decay = 0.5 ** (days_ago / self.time_decay_half_life)
            behavior_flags = getattr(i, 'behavior_flags', 0)
            score = 1.0 - min(1.0, behavior_flags * 0.2)
            scores.append(score * decay)
        return sum(scores) / len(scores) if scores else 1.0

    def _calculate_detection_score(self, interactions: List[Any]) -> float:
        # Detection: penalize for security detections, with time decay
        scores = []
        now = datetime.utcnow()
        for i in interactions:
            days_ago = (now - i.timestamp).days
            decay = 0.5 ** (days_ago / self.time_decay_half_life)
            detections = getattr(i, 'detections', 0)
            score = 1.0 - min(1.0, detections * 0.25)
            scores.append(score * decay)
        return sum(scores) / len(scores) if scores else 1.0

    def _detect_anomalies(self, interactions: List[Any]) -> List[Dict[str, Any]]:
        # Simple anomaly: risk score jumps > threshold
        anomalies = []
        prev = None
        for i in interactions:
            risk = getattr(i, 'risk_score', 0.0)
            if prev is not None and abs(risk - prev) > self.anomaly_threshold:
                anomalies.append({
                    "timestamp": i.timestamp.isoformat(),
                    "risk_score": risk,
                    "prev_risk_score": prev,
                    "delta": risk - prev
                })
            prev = risk
        return anomalies

    def _identify_factors(self, interactions: List[Any]) -> List[str]:
        # ... existing or improved logic for explainability ...
        factors = []
        for i in interactions:
            if getattr(i, 'risk_score', 0.0) > 0.7:
                factors.append(f"High risk at {i.timestamp}")
            if getattr(i, 'detections', 0) > 0:
                factors.append(f"Security detections at {i.timestamp}")
            if getattr(i, 'behavior_flags', 0) > 0:
                factors.append(f"Behavior flags at {i.timestamp}")
        return factors 