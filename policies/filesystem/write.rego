package ai_investor.filesystem.write

# Default deny - all filesystem writes are denied unless explicitly allowed
default allow = false

# Allow writes to workspace directory
allow {
    input.action == "file_write"
    input.resource == "filesystem"
    startswith(input.context.path, "/workspace/")
}

# Allow writes to temporary directory
allow {
    input.action == "file_write"
    input.resource == "filesystem"
    startswith(input.context.path, "/tmp/")
}

# Deny writes to system directories
deny {
    input.action == "file_write"
    input.resource == "filesystem"
    system_paths := ["/etc/", "/bin/", "/usr/", "/sys/", "/proc/"]
    some path in system_paths
    startswith(input.context.path, path)
}

# Deny writes to sensitive files
deny {
    input.action == "file_write"
    input.resource == "filesystem"
    sensitive_files := [".ssh/", ".aws/", ".env", "credentials", "secrets"]
    some pattern in sensitive_files
    contains(input.context.path, pattern)
}

# Reasons for denial
reasons contains reason {
    deny
    system_paths := ["/etc/", "/bin/", "/usr/", "/sys/", "/proc/"]
    some path in system_paths
    startswith(input.context.path, path)
    reason := sprintf("Cannot write to system directory: %s", [path])
}

reasons contains reason {
    deny
    sensitive_files := [".ssh/", ".aws/", ".env", "credentials", "secrets"]
    some pattern in sensitive_files
    contains(input.context.path, pattern)
    reason := sprintf("Cannot write to sensitive file pattern: %s", [pattern])
}

reasons contains reason {
    not allow
    not startswith(input.context.path, "/workspace/")
    not startswith(input.context.path, "/tmp/")
    reason := "File writes only allowed in /workspace/ or /tmp/"
}
