# Aetheris Postman Demo

This folder contains the local Postman collections and environment for demonstrating Aetheris APIs.

## Files

- `aetheris-local.postman_environment.json`
- `aetheris-auth-tenancy.postman_collection.json`
- `aetheris-documents.postman_collection.json`
- `aetheris-ingestion.postman_collection.json`

## Usage

1. Start the local stack.
```powershell
   docker compose up --build
```

2. Apply database migrations.
```powershell
   uv run alembic upgrade head
```

3. Import all JSON files into Postman.

4. Select the **Aetheris Local** environment in the top right dropdown.

5. Run the **Aetheris Auth and Tenancy API** collection in the following order:
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

6. Re-run **Auth** / Login to restore the access token, then run the **Aetheris Documents API** collection in the following order:
   * **Documents** / Upload Document _(attach a .txt, .pdf, or .md file)_
   * **Documents** / Upload Document Rejected - Unsupported Type _(attach any non-supported file such as .png)_
   * **Documents** / Upload Document Rejected - Unauthenticated
   * **Documents** / List Documents
   * **Documents** / Get Document
   * **Documents** / Get Document Not Found
   * **Jobs** / Get Job Status
   * **Jobs** / Get Job Not Found

7. Re-run **Auth** / Login to restore the access token, then run the **Aetheris Ingestion Pipeline API** collection in the following order:
   * **Ingestion Pipeline** / Upload Document for Processing _(attach a .txt, .pdf, or .md file)_
   * **Ingestion Pipeline** / Poll Job Status _(run immediately after upload)_
   * **Ingestion Pipeline** / Verify Job Completed _(run after ~15 seconds to allow worker to finish)_
   * **Ingestion Pipeline** / Verify Document Ready
