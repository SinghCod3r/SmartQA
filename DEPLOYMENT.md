# Deploying to Vercel

The application is configured to be "Build Ready" for Vercel deployment.

## Prerequisites

1.  **Vercel Account**: Sign up at [vercel.com](https://vercel.com).
2.  **Vercel CLI**: Install via npm:
    ```bash
    npm install -g vercel
    ```

## Deployment Steps

1.  **Login to Vercel** (if using CLI):
    ```bash
    vercel login
    ```

2.  **Deploy**:
    Run the following command in the project root (`e:\QA_test_Case_writeup`):
    ```bash
    vercel
    ```
    - Follow the prompts (Select scope, Link to existing project: No).
    - **Project Name**: Enter `smart-qa` (Must be **lowercase**!).
    - Use default settings for most prompts.

3.  **Environment Variables**:
    Go to your Vercel Project Dashboard > Settings > Environment Variables and add these:

    | Key | Value | Note |
    |-----|-------|------|
    | `VERCEL` | `true` | **Critical** for file/db handling |
    | `SECRET_KEY` | `your-secure-random-string` | For session security |
    | `OPENROUTER_API_KEY` | `your-key` | Required for AI |
    | `GOOGLE_API_KEY` | `your-key` | Optional |
    | `GROQ_API_KEY` | `your-key` | Optional |

## Important Considerations

### ⚠️ Database Persistence (Read Carefully)
This MVP uses **SQLite**. On Serverless platforms like Vercel:
- The database is created in `/tmp`, which is **ephemeral**.
- **Data (accounts, history) will be wiped** when the serverless function puts itself to sleep (after a few minutes of inactivity) or on new deployments.
- **Solution for Production**: Connect a real database (like **Neon Postgres** or **Supabase**) and update `database.py` to use it.

### ⚠️ File Uploads
- Uploaded files are stored in `/tmp/uploads`.
- They are also temporary and will persist only for the duration of the request processing.

## Production Setup
For a true production app on Vercel:
1.  **Database**: Vercel > Storage > Create **Postgres** (Neon).
2.  **Connect**: It will automatically add `POSTGRES_URL` etc. env vars.
3.  **Code Update**: You would need to update `database.py` to use `psycopg2` instead of `sqlite3`.

For this MVP, the ephemeral SQLite is sufficient for testing but not for long-term user data storage.
