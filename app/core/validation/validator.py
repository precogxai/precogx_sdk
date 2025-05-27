from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.telemetry.models import Agent, Interaction
from app.core.trust.calculator import TrustScoreCalculator
from app.core.validation.slack import SlackNotifier
from app.core.database import Tenant

class ValidationLayer:
    def __init__(self, db: Session, tenant: Tenant):
        self.db = db
        self.tenant = tenant
        self.slack_notifier = SlackNotifier()
        self.trust_threshold = 0.7  # Default threshold, can be configured per tenant

    def validate_interaction(
        self,
        agent: Agent,
        interaction: Interaction,
        force_approval: bool = False
    ) -> Dict[str, Any]:
        """
        Validate an interaction based on trust score and approval requirements.
        
        Args:
            agent: The agent being validated
            interaction: The interaction to validate
            force_approval: If True, skip trust score check and require manual approval
        
        Returns:
            Dict containing validation result and required actions
        """
        # Calculate trust score
        calculator = TrustScoreCalculator(self.db, agent, self.tenant.id)
        trust_score = calculator.calculate_trust_score()

        # Determine if manual approval is required
        requires_approval = force_approval or trust_score["overall_score"] < self.trust_threshold

        if requires_approval:
            # Send Slack notification for approval
            self.slack_notifier.send_trust_score_alert(agent, trust_score, interaction)
            
            return {
                "status": "pending_approval",
                "trust_score": trust_score,
                "requires_approval": True,
                "message": "Manual approval required due to low trust score"
            }
        else:
            return {
                "status": "approved",
                "trust_score": trust_score,
                "requires_approval": False,
                "message": "Automatically approved based on trust score"
            }

    def handle_approval(
        self,
        agent_id: str,
        interaction_id: Optional[int],
        approved: bool,
        approver: str
    ) -> Dict[str, Any]:
        """
        Handle an approval decision.
        
        Args:
            agent_id: ID of the agent being approved
            interaction_id: Optional ID of the interaction being approved
            approved: Whether the action was approved
            approver: Username of the approver
        
        Returns:
            Dict containing the result of the approval
        """
        # Get the agent
        agent = self.db.query(Agent).filter(
            Agent.agent_id == agent_id,
            Agent.tenant_id == self.tenant.id
        ).first()
        
        if not agent:
            return {
                "status": "error",
                "message": "Agent not found"
            }

        # Get the interaction if provided
        interaction = None
        if interaction_id:
            interaction = self.db.query(Interaction).filter(
                Interaction.id == interaction_id,
                Interaction.agent_id == agent.id,
                Interaction.tenant_id == self.tenant.id
            ).first()

        # Send approval notification
        self.slack_notifier.send_approval_notification(
            agent=agent,
            interaction=interaction,
            approved=approved,
            approver=approver
        )

        # Update interaction status if available
        if interaction:
            interaction.approval_status = "approved" if approved else "rejected"
            interaction.approved_by = approver
            interaction.approval_timestamp = datetime.utcnow()
            self.db.commit()

        return {
            "status": "approved" if approved else "rejected",
            "agent_id": agent_id,
            "interaction_id": interaction_id,
            "approver": approver,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """
        Get a list of pending approvals for the current tenant.
        
        Returns:
            List of pending approval items
        """
        # Get interactions pending approval
        pending_interactions = self.db.query(Interaction).filter(
            Interaction.tenant_id == self.tenant.id,
            Interaction.approval_status == "pending"
        ).all()

        result = []
        for interaction in pending_interactions:
            agent = self.db.query(Agent).filter(Agent.id == interaction.agent_id).first()
            if not agent:
                continue

            # Calculate trust score
            calculator = TrustScoreCalculator(self.db, agent, self.tenant.id)
            trust_score = calculator.calculate_trust_score()

            result.append({
                "agent_id": agent.agent_id,
                "agent_name": agent.name,
                "interaction_id": interaction.id,
                "timestamp": interaction.timestamp.isoformat(),
                "input": interaction.input,
                "response": interaction.response,
                "trust_score": trust_score
            })

        return result 