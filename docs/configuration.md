# Configuration Guide

WBAT iTerm2 Status Bar uses a TOML configuration file located at:
- `~/.config/wbat-iterm-status/config.toml` (default)
- `~/Library/Application Support/wbat-iterm-status/config.toml` (fallback)

## Configuration Structure

```toml
[global]
update_cadence_seconds = 1      # How often to update (seconds)
render_timeout_ms = 50         # Max render time (milliseconds)
log_level = "info"             # Log level: debug, info, warning, error

[cycle]
enabled = true                 # Enable view cycling
interval_seconds = 8           # Time between cycles
mode = "round_robin"           # Cycle mode
start_view = "default"         # Initial view

[views.default]
template = "{path}  {git.summary}  {aws.short}  {gcp.short}"

[views.cloud]
template = "{aws.long}  {gcp.long}"

[views.git]
template = "{git.branch} {git.ahead_behind} {git.changes}"

[plugins.git]
enabled = true
mode = "fast"                  # fast or full
ttl_seconds = 2
max_repo_scan_ms = 50

[plugins.aws]
enabled = true
mode = "env_only"              # env_only or identity
ttl_seconds = 600
source = "user_vars"
profile_var = "user.awsProfile"
region_var = "user.awsRegion"

[plugins.gcp]
enabled = true
mode = "env_only"
ttl_seconds = 600
project_var = "user.gcpProject"

[plugins.kube]
enabled = false
ttl_seconds = 10

[plugins.cmd]
enabled = false
command = "echo 'custom'"
field_name = "output"
timeout = 5.0
max_output = 1024
```

## Global Settings

### `update_cadence_seconds`
How often the status bar updates (in seconds). Lower values = more frequent updates but more CPU usage.

### `render_timeout_ms`
Maximum time allowed for rendering (milliseconds). If exceeded, shows error message.

### `log_level`
Logging verbosity: `debug`, `info`, `warning`, `error`.

## View Cycling

### `enabled`
Enable automatic cycling through multiple views.

### `interval_seconds`
Time to show each view before cycling to the next.

### `mode`
- `round_robin`: Cycle through views in order
- Future: `sticky`, `context_override`

### `start_view`
Which view to show initially.

## Views

Views are templates that define what appears in the status bar.

### Template Syntax

Use `{plugin.field}` to reference plugin data:

- `{path}` - Current directory path
- `{git.branch}` - Git branch name
- `{git.summary}` - Git summary (branch + status)
- `{aws.short}` - AWS short format
- `{aws.long}` - AWS long format
- `{gcp.short}` - GCP short format
- `{gcp.long}` - GCP long format
- `{kube.context}` - Kubernetes context
- `{clock}` - Current time

### Example Views

```toml
[views.minimal]
template = "{path_short}  {git.branch}"

[views.detailed]
template = "{path}  {git.summary}  {aws.long}  {gcp.long}  {kube.short}"

[views.cloud_focus]
template = "{aws.profile}/{aws.region}  {gcp.project}"
```

## Plugin Configuration

### Git Plugin

- `mode`: `fast` (quick status) or `full` (detailed status)
- `ttl_seconds`: Cache TTL (how long to cache git status)
- `max_repo_scan_ms`: Maximum time to scan repository

### AWS Plugin

- `mode`: 
  - `env_only`: Read from environment variables only
  - `identity`: Also query AWS CLI for account/role info
- `ttl_seconds`: Cache TTL for identity queries
- `profile_var`: User variable name for AWS profile
- `region_var`: User variable name for AWS region

### GCP Plugin

- `mode`: `env_only` or `identity`
- `ttl_seconds`: Cache TTL
- `project_var`: User variable name for GCP project

### Kubernetes Plugin

- `enabled`: Enable/disable plugin
- `ttl_seconds`: Cache TTL (usually short, like 10s)

### Command Plugin

- `enabled`: Enable/disable plugin
- `command`: Command to execute
- `field_name`: Field name for output
- `timeout`: Command timeout (seconds)
- `max_output`: Maximum output size (bytes)

## Environment Variable Overrides

You can override some settings via environment variables:

- `WBAT_LOG_LEVEL`: Override log level
- `WBAT_UPDATE_CADENCE`: Override update cadence
- `WBAT_CYCLE_ENABLED`: Enable/disable cycling (true/false)
- `WBAT_CYCLE_INTERVAL`: Override cycle interval

## Reloading Configuration

Configuration is loaded at startup. To apply changes:

1. Disable the script in AutoLaunch
2. Re-enable it
3. Or restart iTerm2
