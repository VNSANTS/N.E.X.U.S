# N.E.X.U.S. — Access and autonomy model

## Owner authorization

The owner may call `PermissionManager.grant_standard_access()` to enable the
ordinary capabilities of the personal agent. This includes memory and cognitive
profile read/write, web research, knowledge organization, skill creation,
agent execution, tool use, authorized file read/write, local execution, and
project read/write.

This is a permission policy layer, not a magic unlock of integrations. A module
still needs an implemented adapter and the operating system/account must grant
the required access. N.E.X.U.S. cannot access a phone, computer, account, file,
or service merely because a scope is enabled.

## Confirmation-only actions

The following always require a fresh, action-specific confirmation:
- sending messages or other external communications;
- publishing content publicly;
- deleting external or user data;
- installing software or modifying system/security settings;
- reading credentials or exporting data.

A broad owner grant never turns these into silent background actions. The
confirmation must be tied to the exact pending action and supplied by a
trusted interactive UI, not by the agent itself.

## Revocation and audit

Individual scopes can be revoked with `revoke(scope)`. Decisions are recorded
in the SQLite audit log. Integrations must call `require(scope)` immediately
before performing an operation; checking permissions only at startup is not
sufficient.

## Current limitations

This manager does not itself connect a model provider, browser, filesystem,
shell, email account, or other external service. It establishes the common
authorization contract that those modules must enforce. Until each adapter
uses this manager, its operations are not governed by this policy.
