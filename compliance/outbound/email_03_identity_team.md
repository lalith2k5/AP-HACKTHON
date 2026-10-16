# Email — IT / Identity Team

**Subject:** SSO swap request — StoreSignal AI (OIDC, no code change required)

Dear [Identity team],

StoreSignal AI is ready to switch from the local demo identity provider to
our corporate IdP. The integration is fully provider-agnostic and the swap
requires only environment variables — no code changes.

Attached: `04_idp_swap_guide.md` with exact steps for Auth0, Google
Workspace, Azure AD / Entra ID, and Okta.

**What we need from you:**
1. An OIDC application registration for StoreSignal AI
2. Client ID and client secret
3. Issuer URL
4. A decision on the role claim (we support any dotted path — for example
   `realm_access.roles`, `roles`, or a namespaced custom claim)
5. Confirmation of the allowed redirect URI: `http://localhost:3300/api/auth/callback/oidc`
   for local testing; production URI when we have it

Once we have these, the swap takes under 10 minutes and can be verified with
our existing SSO end-to-end test suite.

Best regards,
[Name]
[Title]
