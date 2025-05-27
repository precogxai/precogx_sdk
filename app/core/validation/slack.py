from typing import Dict, Any, Optional
import os
import json
import requests
from datetime import datetime
from app.core.telemetry.models import Agent, Interaction
from app.core.trust.calculator import TrustScoreCalculator

class SlackNotifier:
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("Slack webhook URL must be provided or set in environment variables")

    def send_trust_score_alert(
        self,
        agent: Agent,
        trust_score: Dict[str, Any],
        interaction: Optional[Interaction] = None
    ) -> bool:
        """
        Send a trust score alert to Slack.
        
        Args:
            agent: The agent being evaluated
            trust_score: The trust score data
            interaction: Optional interaction that triggered the alert
        
        Returns:
            bool: True if message was sent successfully
        """
        # Determine alert level based on trust score
        alert_level = "warning" if trust_score["overall_score"] < 0.7 else "info"
        if trust_score["overall_score"] < 0.4:
            alert_level = "danger"

        # Prepare message blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🔔 Trust Score Alert: {agent.name} ({agent.agent_id})"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Trust Score:*\n{trust_score['overall_score']:.2f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Confidence:*\n{trust_score['confidence']:.2f}"
                    }
                ]
            }
        ]

        # Add breakdown if available
        if "breakdown" in trust_score:
            breakdown_text = "\n".join(
                f"• {k}: {v:.2f}" for k, v in trust_score["breakdown"].items()
            )
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Score Breakdown:*\n{breakdown_text}"
                }
            })

        # Add factors if available
        if "factors" in trust_score and trust_score["factors"]:
            factors_text = "\n".join(f"• {factor}" for factor in trust_score["factors"])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Contributing Factors:*\n{factors_text}"
                }
            })

        # Add interaction details if available
        if interaction:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Latest Interaction:*\n• Input: {interaction.input[:100]}...\n• Response: {interaction.response[:100]}..."
                }
            })

        # Add approval buttons if trust score is low
        if trust_score["overall_score"] < 0.7:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Approve",
                            "emoji": True
                        },
                        "style": "primary",
                        "value": f"approve_{agent.id}_{interaction.id if interaction else 'none'}"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Reject",
                            "emoji": True
                        },
                        "style": "danger",
                        "value": f"reject_{agent.id}_{interaction.id if interaction else 'none'}"
                    }
                ]
            })

        # Prepare the message payload
        payload = {
            "blocks": blocks,
            "attachments": [{
                "color": {
                    "info": "#36a64f",
                    "warning": "#ffcc00",
                    "danger": "#ff0000"
                }[alert_level]
            }]
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending Slack notification: {e}")
            return False

    def send_approval_notification(
        self,
        agent: Agent,
        interaction: Optional[Interaction],
        approved: bool,
        approver: str
    ) -> bool:
        """
        Send an approval notification to Slack.
        
        Args:
            agent: The agent being approved/rejected
            interaction: Optional interaction being approved/rejected
            approved: Whether the action was approved
            approver: Username of the approver
        
        Returns:
            bool: True if message was sent successfully
        """
        status = "Approved ✅" if approved else "Rejected ❌"
        color = "#36a64f" if approved else "#ff0000"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Action {status}: {agent.name} ({agent.agent_id})"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Approver:*\n{approver}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{datetime.utcnow().isoformat()}"
                    }
                ]
            }
        ]

        if interaction:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Interaction Details:*\n• Input: {interaction.input[:100]}...\n• Response: {interaction.response[:100]}..."
                }
            })

        payload = {
            "blocks": blocks,
            "attachments": [{"color": color}]
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending Slack approval notification: {e}")
            return False 