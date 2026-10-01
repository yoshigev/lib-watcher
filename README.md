# Library Availability Watcher

A FastAPI web app for monitoring public libraries that use the BuildaGate catalog system. Users can search the catalog, watch borrowed books, and receive email notifications through Brevo when a copy becomes available.

The app runs as a Docker web service on Render, stores data in MongoDB Atlas, and uses WatchCron Cloud Cron to trigger availability checks every 15 minutes. The GitHub repository is public; never commit credentials or local environment files.

## Local setup

1. Install Python 3.11 or later and install dependencies:

   ```sh
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in local settings. `.env` is ignored by Git. Set at least `MONGODB_URI`, `DATABASE_NAME`, `SECRET_KEY`, and `SEED_USERS`. For real email delivery, set `BREVO_API_KEY` and use a verified `BREVO_SENDER_EMAIL`.

3. Start the development server:

   ```sh
   python -m uvicorn app.main:app --reload --port 8000
   ```

4. Open http://localhost:8000. The initial user is configured through `SEED_USERS`; change its example credentials before using the app.

The health endpoint is available at `/health`. Cron checks are handled by `GET /api/cron/check` and require the `X-Cron-Secret` header to match `CRON_SECRET`.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `MONGODB_URI` | MongoDB Atlas connection string |
| `DATABASE_NAME` | MongoDB database name |
| `SECRET_KEY` | Application signing key |
| `CRON_SECRET` | Secret required by the scheduled check endpoint |
| `LIBRARY_BASE_URL` | Library catalog base URL |
| `LIBRARY_SITE_NAME` | Library site identifier used by BuildaGate |
| `LIBRARY_NEW_NAME_MADE` | BuildaGate catalog identifier |
| `LIBRARY_BUYER_ID` | Library buyer identifier |
| `LIBRARY_DISPLAY_NAME` | Name shown in notifications |
| `BREVO_API_KEY` | Brevo SMTP API key |
| `BREVO_SENDER_EMAIL` | Verified Brevo sender address |
| `BREVO_SENDER_NAME` | Sender name shown in email |
| `SEED_USERS` | JSON array of users created during initialization |

`WATCHCRON_API_BASE_URL` and `WATCHCRON_API_KEY` are credentials for the WatchCron management API; the app itself does not need them to receive scheduled calls. Keep them only in ignored local files or a secrets manager.

## Render deployment

The public repository is configured for the Render web service `lib-watcher` (`srv-dav2970u01pc7385kma0`). It builds from the root-level `Dockerfile`; the Render service root directory must be the repository root, not `app/`.

The Docker image installs `requirements.txt`, copies the app source, and listens on Render's `$PORT`. The health check path is `/health`. Set the application environment variables in the Render dashboard; do not commit `.env` or secret values. Ensure `MONGODB_URI`, `BREVO_API_KEY`, `BREVO_SENDER_EMAIL`, `SEED_USERS`, `SECRET_KEY`, and `CRON_SECRET` are configured on the service.

With the Render CLI installed and logged into the correct workspace, deploy the current `master` branch with:

```sh
render deploys create srv-dav2970u01pc7385kma0 --wait
```

## WatchCron scheduling

Use WatchCron **Cloud Cron** to invoke the app endpoint:

- **URL:** `https://lib-watcher.onrender.com/api/cron/check`
- **Method:** `GET`
- **Schedule:** `*/15 * * * *` (every 15 minutes)
- **Header:** `X-Cron-Secret: <the same CRON_SECRET configured in Render>`

Set this up as a Cloud Cron task in the WatchCron dashboard. The WatchCron management API key is separate from this request header; do not send that API key to the app endpoint. WatchCron documents its management API at `https://watchcron.com/api/v1` and uses `Authorization: Bearer <your-api-key>` for API requests. The documented API currently manages checks; Cloud Cron tasks are configured in the dashboard.

## Security

- `.env`, `.env.*`, `*.env`, and `.deployment-secrets` are ignored by Git. The Docker build context excludes them as well.
- `.env.example` contains placeholders only.
- This repository is public. Do not commit passwords, API keys, live connection strings, or user credentials.
- Replace all sample keys and passwords with strong unique values before deploying.
