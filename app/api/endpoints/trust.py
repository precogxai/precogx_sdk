, from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db, Tenant
from app.core.telemetry.models import Agent, Interaction
from app.utils.auth import get_tenant
from app.core.trust.calculator import TrustScoreCalculator
from datetime import timedelta
from typing import Optional

router = APIRouter()

@router.get("/agents/{agent_id}/trust-score")
def get_trust_score(
    agent_id: str,
    time_window: Optional[int] = Query(None, description="Time window in hours to consider for trust score calculation"),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant)
):
    """
    Get the trust score for an agent.
    
    Args:
        agent_id: The ID of the agent to get the trust score for
        time_window: Optional time window in hours to consider for the calculation
        db: Database session
        tenant: Current tenant
    
    Returns:
        Dict containing:
        - overall_score: float between 0 and 1
        - confidence: float between 0 and 1
        - breakdown: Dict with individual factor scores
        - factors: List of contributing factors
        - interactions_analyzed: Number of interactions analyzed
    """
    # Find the agent for the current tenant
    agent = db.query(Agent).filter(Agent.agent_id == agent_id, Agent.tenant_id == tenant.id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID '{agent_id}' not found for this tenant"
        )

    # Create calculator instance
    calculator = TrustScoreCalculator(db, agent, tenant.id)
    
    # Calculate trust score
    time_window_delta = timedelta(hours=time_window) if time_window else None
    trust_score = calculator.calculate_trust_score(time_window_delta)
    
    return trust_score 