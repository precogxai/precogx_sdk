from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db, get_current_tenant
from app.core.telemetry.models import Agent, Interaction
from app.core.validation.validator import ValidationLayer
from app.core.database import Tenant

router = APIRouter()

@router.post("/agents/{agent_id}/validate")
async def validate_agent_interaction(
    agent_id: str,
    interaction_id: Optional[int] = None,
    force_approval: bool = False,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant)
) -> Dict[str, Any]:
    """
    Validate an agent's interaction based on trust score.
    
    Args:
        agent_id: ID of the agent to validate
        interaction_id: Optional ID of the interaction to validate
        force_approval: If True, skip trust score check and require manual approval
    
    Returns:
        Dict containing validation result and required actions
    """
    # Get the agent
    agent = db.query(Agent).filter(
        Agent.agent_id == agent_id,
        Agent.tenant_id == tenant.id
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    # Get the interaction if provided
    interaction = None
    if interaction_id:
        interaction = db.query(Interaction).filter(
            Interaction.id == interaction_id,
            Interaction.agent_id == agent.id,
            Interaction.tenant_id == tenant.id
        ).first()
        
        if not interaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interaction not found"
            )

    # Create validation layer and validate
    validator = ValidationLayer(db, tenant)
    return validator.validate_interaction(agent, interaction, force_approval)

@router.post("/agents/{agent_id}/approve")
async def approve_agent_action(
    agent_id: str,
    interaction_id: Optional[int] = None,
    approved: bool = True,
    approver: str = Query(..., description="Username of the approver"),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant)
) -> Dict[str, Any]:
    """
    Handle approval or rejection of an agent's action.
    
    Args:
        agent_id: ID of the agent being approved
        interaction_id: Optional ID of the interaction being approved
        approved: Whether the action was approved
        approver: Username of the approver
    
    Returns:
        Dict containing the result of the approval
    """
    validator = ValidationLayer(db, tenant)
    result = validator.handle_approval(agent_id, interaction_id, approved, approver)
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["message"]
        )
    
    return result

@router.get("/pending-approvals")
async def get_pending_approvals(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant)
) -> Dict[str, Any]:
    """
    Get a list of pending approvals for the current tenant.
    
    Returns:
        List of pending approval items
    """
    validator = ValidationLayer(db, tenant)
    pending_approvals = validator.get_pending_approvals()
    
    return {
        "count": len(pending_approvals),
        "items": pending_approvals
    } 