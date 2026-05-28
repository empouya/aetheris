# Aetheris Postman Demo

This folder contains the local Postman collection and environment for demonstrating Aetheris authentication and tenancy APIs.

## Files

- `aetheris-local.postman_environment.json`
- `aetheris-auth-tenancy.postman_collection.json`

## Usage

1. Start the local stack.
   ```powershell
   docker compose up --build
   ```

2. Apply database migrations.
   ```powershell
   uv run alembic upgrade head
   ```

3. Import both JSON files into Postman.

4. Select the **Aetheris Local** environment in the top right dropdown.

5. Run requests in the following sequential order:
   * **Health** / Health
   * **Auth** / Login
   * **Organizations** / Create Organization
   * **Organizations** / List Organizations
   * **Organizations** / List Members
   * **API Keys** / Create API Key
   * **API Keys** / List API Keys
   * **API Keys** / Revoke API Key
   * **Auth** / Refresh Token
   * **Auth** / Logout
