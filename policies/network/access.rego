package ai_investor.network.access

# Default deny - all network access is denied unless explicitly allowed
default allow = false

# Allow access to approved domains
allow {
    input.action == "network_access"
    input.resource == "network"
    approved_domains := [
        "github.com",
        "api.github.com",
        "pypi.org",
        "files.pythonhosted.org",
        "registry.npmjs.org",
    ]
    some domain in approved_domains
    contains(input.context.url, domain)
}

# Allow localhost access for development
allow {
    input.action == "network_access"
    input.resource == "network"
    input.context.environment == "development"
    localhost_patterns := ["localhost", "127.0.0.1", "0.0.0.0"]
    some pattern in localhost_patterns
    contains(input.context.url, pattern)
}

# Deny access to internal networks in production
deny {
    input.action == "network_access"
    input.resource == "network"
    input.context.environment == "production"
    internal_patterns := [
        "192.168.",
        "10.",
        "172.16.",
        "localhost",
        "127.0.0.1",
    ]
    some pattern in internal_patterns
    contains(input.context.url, pattern)
}

# Deny access to sensitive endpoints
deny {
    input.action == "network_access"
    input.resource == "network"
    sensitive_endpoints := [
        "metadata.google.internal",
        "169.254.169.254",  # AWS/Azure metadata service
        "metadata.azure.com",
    ]
    some endpoint in sensitive_endpoints
    contains(input.context.url, endpoint)
}

# Reasons for denial
reasons contains reason {
    deny
    sensitive_endpoints := [
        "metadata.google.internal",
        "169.254.169.254",
        "metadata.azure.com",
    ]
    some endpoint in sensitive_endpoints
    contains(input.context.url, endpoint)
    reason := sprintf("Cannot access sensitive endpoint: %s", [endpoint])
}

reasons contains reason {
    not allow
    not input.context.url
    reason := "URL must be specified for network access"
}

reasons contains reason {
    not allow
    input.context.url
    reason := sprintf("Domain not in approved list: %s", [input.context.url])
}
