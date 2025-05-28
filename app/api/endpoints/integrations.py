# Get or create agent
agent = db.query(Agent).filter(
    Agent.agent_id == data["agent_id"],
    Agent.tenant_id == tenant.id
).first()

# Only check agent count if agent does not exist (i.e., about to create a new one)
if not agent:
    agent_count = db.query(Agent).filter(Agent.tenant_id == tenant.id).count()
    print(f"Debug: Current agent count for tenant {tenant.id}: {agent_count}")
    tier_limits = TierRules.get_tier_limits(tenant.tier)
    max_agents = tier_limits.max_agents
    if max_agents != -1:  # -1 means unlimited
        if agent_count >= max_agents:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Agent limit reached for your tier ({agent_count}/{max_agents}). Please upgrade your plan."
            )
        elif (agent_count + 1) / max_agents >= 0.8:
            print(f"[ALERT] Tenant {tenant.id} is nearing agent limit: {agent_count+1}/{max_agents}") 