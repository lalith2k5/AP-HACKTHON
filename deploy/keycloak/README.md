# Local Keycloak for StoreSignal OIDC

    cd deploy/keycloak
    docker compose up -d

Keycloak: http://localhost:8080  (admin / admin)
Realm: storesignal
Client: storesignal-api (secret: storesignal-dev-secret)

Test users (all password: `password`):
    admin     -> role admin
    ops       -> role regional_ops_lead
    reviewer  -> role reviewer
    hr        -> role hr_sensitive

## Add the roles claim to tokens

After first boot, open the Keycloak admin console:
1. Clients -> storesignal-api -> Client scopes -> add "roles"
2. Clients -> storesignal-api -> Client scopes -> roles -> Mappers
   -> "realm roles" -> toggle "Add to ID token" ON, "Add to access token" ON
3. Optionally rename the claim to "roles".

Or import a preconfigured realm with mappers (TODO).

## Point StoreSignal at it

    export STORESIGNAL_OIDC_ENABLED=true
    export STORESIGNAL_OIDC_ISSUER=http://localhost:8080/realms/storesignal
    export STORESIGNAL_OIDC_AUDIENCE=storesignal-api
    export STORESIGNAL_OIDC_ROLE_CLAIM=realm_access.roles

Restart the API. Send a Bearer token from any client.

Get a token for testing:

    curl -s -X POST http://localhost:8080/realms/storesignal/protocol/openid-connect/token \
      -d "client_id=storesignal-api" \
      -d "client_secret=storesignal-dev-secret" \
      -d "grant_type=password" \
      -d "username=admin" -d "password=password" | jq -r .access_token

Then:

    TOKEN=$(...)
    curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8790/api/v1/incidents?limit=1
