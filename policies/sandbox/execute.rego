package ai_investor.sandbox.execute

# Default deny - all sandbox executions are denied unless explicitly allowed
default allow = false

# Allow sandbox execution for LOW risk tasks
allow {
    input.context.risk_level == "LOW"
    input.action == "execute"
    input.resource == "sandbox"
}

# Allow sandbox execution for MEDIUM risk tasks with restrictions
allow {
    input.context.risk_level == "MEDIUM"
    input.action == "execute"
    input.resource == "sandbox"
    input.context.network_access == false
    input.context.filesystem_readonly == true
}

# Allow sandbox execution for HIGH risk tasks with strict controls
allow {
    input.context.risk_level == "HIGH"
    input.action == "execute"
    input.resource == "sandbox"
    input.context.network_access == false
    input.context.filesystem_readonly == true
    input.context.approved_by != null
}

# Reasons for denial
reasons contains reason {
    not allow
    input.context.risk_level == "HIGH"
    input.context.approved_by == null
    reason := "HIGH risk execution requires approval"
}

reasons contains reason {
    not allow
    input.context.risk_level == "MEDIUM"
    input.context.network_access == true
    reason := "MEDIUM risk execution cannot have network access"
}

reasons contains reason {
    not allow
    input.context.risk_level == "MEDIUM"
    input.context.filesystem_readonly == false
    reason := "MEDIUM risk execution requires read-only filesystem"
}

reasons contains reason {
    not allow
    not input.context.risk_level
    reason := "risk_level must be specified"
}
