# Data Classification

## Classes

### Public

Safe to store and export by default.

Examples:

- public project name
- public repository URL
- public technical preference

### Personal

User-specific but normally low-risk.

Examples:

- preferred editor
- explanation style
- current project
- learning goal

Default: allowed with provenance and user controls.

### Sensitive

Information that may create privacy or safety risk.

Examples:

- precise location
- health information
- financial circumstances
- legal issues
- private relationships

Default: require explicit consent category and conservative retention.

### Restricted

Must not be stored by the initial system.

Examples:

- passwords
- API keys
- access tokens
- private keys
- authentication cookies
- full payment-card data
- credentials in connection strings

Default: block and redact.

## Consent categories

- personalization
- project continuity
- persistent instructions
- sensitive personal context
- knowledge documents

## Retention policies

- session-only
- fixed expiry
- durable until correction
- durable until user deletion
- prohibited

The evaluator may recommend a policy, but explicit user control wins.
