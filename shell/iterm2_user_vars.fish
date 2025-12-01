#!/usr/bin/env fish
# iTerm2 user variable integration for fish
# Source this file in your ~/.config/fish/config.fish to export environment variables to iTerm2

# Function to set iTerm2 user variables
function iterm2_set_user_var
    if test -n "$ITERM_SESSION_ID"
        printf "\033]1337;SetUserVar=%s=%s\007" $argv[1] (printf "%s" $argv[2] | base64)
    end
end

# Update iTerm2 user variables when environment changes
function iterm2_update_user_vars
    # AWS variables
    if test -n "$AWS_PROFILE"
        iterm2_set_user_var awsProfile "$AWS_PROFILE"
    end
    if test -n "$AWS_REGION"
        iterm2_set_user_var awsRegion "$AWS_REGION"
    end
    
    # GCP variables
    if test -n "$CLOUDSDK_CORE_PROJECT"
        iterm2_set_user_var gcpProject "$CLOUDSDK_CORE_PROJECT"
    end
    
    # Kubernetes context (if kubectl is available)
    if command -v kubectl >/dev/null 2>&1
        set kube_context (kubectl config current-context 2>/dev/null)
        if test -n "$kube_context"
            iterm2_set_user_var kubeContext "$kube_context"
        end
    end
end

# Update on prompt
function fish_prompt
    iterm2_update_user_vars
    # Call default prompt (or your custom prompt)
    # This is a minimal implementation - adjust as needed
end

# Initial update
iterm2_update_user_vars
