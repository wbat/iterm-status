#!/usr/bin/env bash
# iTerm2 user variable integration for bash
# Source this file in your ~/.bashrc to export environment variables to iTerm2

# Function to set iTerm2 user variables
iterm2_set_user_var() {
    if [[ -n "$ITERM_SESSION_ID" ]]; then
        printf "\033]1337;SetUserVar=%s=%s\007" "$1" "$(printf "%s" "$2" | base64)"
    fi
}

# Update iTerm2 user variables when environment changes
iterm2_update_user_vars() {
    # AWS variables
    if [[ -n "$AWS_PROFILE" ]]; then
        iterm2_set_user_var awsProfile "$AWS_PROFILE"
    fi
    if [[ -n "$AWS_REGION" ]]; then
        iterm2_set_user_var awsRegion "$AWS_REGION"
    fi
    
    # GCP variables
    if [[ -n "$CLOUDSDK_CORE_PROJECT" ]]; then
        iterm2_set_user_var gcpProject "$CLOUDSDK_CORE_PROJECT"
    fi
    
    # Kubernetes context (if kubectl is available)
    if command -v kubectl >/dev/null 2>&1; then
        local kube_context=$(kubectl config current-context 2>/dev/null)
        if [[ -n "$kube_context" ]]; then
            iterm2_set_user_var kubeContext "$kube_context"
        fi
    fi
}

# Update on prompt (PROMPT_COMMAND)
if [[ -z "$PROMPT_COMMAND" ]]; then
    PROMPT_COMMAND="iterm2_update_user_vars"
else
    PROMPT_COMMAND="$PROMPT_COMMAND; iterm2_update_user_vars"
fi

# Initial update
iterm2_update_user_vars
