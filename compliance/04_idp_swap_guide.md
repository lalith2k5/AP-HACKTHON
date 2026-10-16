# IdP Swap Guide

The code is provider-agnostic (see src/storesignal/auth_oidc.py and
web/auth.ts). Only environment variables change. No code edits required.

## The seven variables

Backend (.env):
    STORESIGNAL_OIDC_ENABLED=true
    STORESIGNAL_OIDC_ISSUER=<issuer URL>
    STORESIGNAL_OIDC_AUDIENCE=<audience>       (leave empty to skip check)
    STORESIGNAL_OIDC_ROLE_CLAIM=<dotted path>  (e.g. realm_access.roles)

Frontend (web/.env.local):
    AUTH_OIDC_ISSUER=<same as above>
    AUTH_OIDC_CLIENT_ID=<client id>
    AUTH_OIDC_CLIENT_SECRET=<client secret>
    AUTH_OIDC_ROLE_CLAIM=<same as above>

Plus AUTH_SECRET (random string for Auth.js session encryption) and AUTH_URL.

## Provider examples

### Auth0

    STORESIGNAL_OIDC_ISSUER=https://<tenant>.us.auth0.com/
    STORESIGNAL_OIDC_AUDIENCE=https://storesignal-api
    STORESIGNAL_OIDC_ROLE_CLAIM=https://storesignal/roles
    AUTH_OIDC_CLIENT_ID=<from Auth0 dashboard>
    AUTH_OIDC_CLIENT_SECRET=<from Auth0 dashboard>
Configure an Auth0 Action to add roles to the custom claim above.

### Google Workspace (via GCP Identity Platform)

    STORESIGNAL_OIDC_ISSUER=https://accounts.google.com
    STORESIGNAL_OIDC_AUDIENCE=<oauth client id>
    STORESIGNAL_OIDC_ROLE_CLAIM=hd
Note: role mapping uses the hosted-domain claim. Map hd -> storesignal role
in web/auth.ts if more granularity is needed.

### Azure AD / Microsoft Entra ID

    STORESIGNAL_OIDC_ISSUER=https://login.microsoftonline.com/<tenant-id>/v2.0
    STORESIGNAL_OIDC_AUDIENCE=<app registration client id>
    STORESIGNAL_OIDC_ROLE_CLAIM=roles
Add App Roles in the Entra portal; they appear in the `roles` claim.

### Okta

    STORESIGNAL_OIDC_ISSUER=https://<tenant>.okta.com/oauth2/default
    STORESIGNAL_OIDC_AUDIENCE=api://default
    STORESIGNAL_OIDC_ROLE_CLAIM=groups
Map Okta groups to roles in security.py's ROLE_PERMISSIONS table.

## Migration procedure

1. Provision an OIDC application in the target IdP
2. Populate the seven env vars above
3. touch web/.oidc-enabled
4. Restart backend via ./scripts/run-api.sh (NOT bare uvicorn)
5. Restart frontend
6. Run the SSO E2E: cd web && npx playwright test sso.spec.ts
7. Confirm 3/3 pass
8. Remove the local Keycloak container: cd deploy/keycloak && docker compose down

## Rollback

    rm web/.oidc-enabled
Remove STORESIGNAL_OIDC_ENABLED from .env
Restart both servers. Static-key mode resumes.
