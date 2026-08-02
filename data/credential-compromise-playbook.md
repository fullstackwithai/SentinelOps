# Credential Compromise Response Playbook

## Trigger conditions
Use this playbook when authentication telemetry indicates credential stuffing, password spraying, impossible travel, repeated MFA failure, or suspicious privileged-account access.

## Immediate actions
1. Preserve authentication, identity-provider, endpoint, and network evidence.
2. Disable or temporarily restrict the affected identity when risk is high.
3. Revoke active sessions and refresh tokens.
4. Require a password reset and phishing-resistant MFA enrollment.
5. Review recent privilege changes, mailbox rules, API tokens, and sensitive-data access.

## Analyst validation
Confirm whether the user recognizes the source device, location, and activity. Correlate the event with endpoint telemetry and other accounts using the same source IP. Escalate when privileged access, impossible travel, or multiple compromised identities are present.

## Closure
Document the evidence, containment actions, root cause, affected resources, and monitoring period. Do not claim attribution without sufficient evidence.
