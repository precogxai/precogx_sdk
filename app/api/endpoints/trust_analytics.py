from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.core.database import get_db, get_current_tenant
from app.core.telemetry.models import Agent, Interaction
from app.core.trust.calculator import TrustScoreCalculator
from app.core.database import Tenant

router = APIRouter()

@router.get("/agents/{agent_id}/trust-score/history")
def trust_score_history(
    agent_id: str,
    days: int = Query(30, description="Number of days to look back for history"),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant)
) -> Dict[str, Any]:
    """
    Get the time series of trust scores for an agent.
    """
    agent = db.query(Agent).filter(Agent.agent_id == agent_id, Agent.tenant_id == tenant.id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    # Get all interactions in the window
    since = datetime.utcnow() - timedelta(days=days)
    interactions = db.query(Interaction).filter(
        Interaction.agent_id == agent.id,
        Interaction.tenant_id == tenant.id,
        Interaction.timestamp >= since
    ).order_by(Interaction.timestamp.asc()).all()
    # Calculate trust score for each day
    history = []
    for day in range(days):
        window_start = since + timedelta(days=day)
        window_end = window_start + timedelta(days=1)
        day_interactions = [i for i in interactions if window_start <= i.timestamp < window_end]
        if not day_interactions:
            score = None
        else:
            calc = TrustScoreCalculator(db, agent, tenant.id)
            calc._get_interactions = lambda tw=None: day_interactions
            score = calc.calculate_trust_score()
        history.append({
            "date": window_start.date().isoformat(),
            "score": score["overall_score"] if score else None,
            "confidence": score["confidence"] if score else 0.0,
            "interactions": len(day_interactions)
        })
    return {"agent_id": agent_id, "history": history}

@router.get("/agents/{agent_id}/trust-score/analytics")
def trust_score_analytics(
    agent_id: str,
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant)
) -> Dict[str, Any]:
    """
    Get analytics/statistics for an agent's trust score.
    """
    agent = db.query(Agent).filter(Agent.agent_id == agent_id, Agent.tenant_id == tenant.id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    since = datetime.utcnow() - timedelta(days=days)
    interactions = db.query(Interaction).filter(
        Interaction.agent_id == agent.id,
        Interaction.tenant_id == tenant.id,
        Interaction.timestamp >= since
    ).order_by(Interaction.timestamp.asc()).all()
    if not interactions:
        return {"agent_id": agent_id, "analytics": {}}
    # Calculate trust scores for each interaction
    calc = TrustScoreCalculator(db, agent, tenant.id)
    scores = []
    for i in interactions:
        calc._get_interactions = lambda tw=None, i=i: [i]
        score = calc.calculate_trust_score()
        scores.append(score["overall_score"])
    analytics = {
        "mean": sum(scores) / len(scores),
        "min": min(scores),
        "max": max(scores),
        "stddev": (sum((s - sum(scores)/len(scores))**2 for s in scores)/len(scores))**0.5 if len(scores) > 1 else 0.0,
        "count": len(scores),
        "anomaly_count": sum(1 for idx in range(1, len(scores)) if abs(scores[idx] - scores[idx-1]) > 0.5)
    }
    return {"agent_id": agent_id, "analytics": analytics}

@router.get("/tenants/{tenant_id}/trust-score/summary")
def tenant_trust_score_summary(
    tenant_id: str,
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get aggregated trust score statistics for all agents in a tenant.
    """
    agents = db.query(Agent).filter(Agent.tenant_id == tenant_id).all()
    if not agents:
        return {"tenant_id": tenant_id, "summary": {}}
    all_scores = []
    for agent in agents:
        since = datetime.utcnow() - timedelta(days=days)
        interactions = db.query(Interaction).filter(
            Interaction.agent_id == agent.id,
            Interaction.tenant_id == tenant_id,
            Interaction.timestamp >= since
        ).all()
        if not interactions:
            continue
        calc = TrustScoreCalculator(db, agent, tenant_id)
        calc._get_interactions = lambda tw=None: interactions
        score = calc.calculate_trust_score()
        all_scores.append(score["overall_score"])
    if not all_scores:
        return {"tenant_id": tenant_id, "summary": {}}
    summary = {
        "mean": sum(all_scores) / len(all_scores),
        "min": min(all_scores),
        "max": max(all_scores),
        "stddev": (sum((s - sum(all_scores)/len(all_scores))**2 for s in all_scores)/len(all_scores))**0.5 if len(all_scores) > 1 else 0.0,
        "count": len(all_scores)
    }
    return {"tenant_id": tenant_id, "summary": summary} 