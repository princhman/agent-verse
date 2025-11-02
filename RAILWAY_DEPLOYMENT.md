# Railway Deployment Guide

This guide explains how to deploy the Agent Verse project on Railway with separate backend and frontend services.

## Prerequisites

1. A GitHub account with the agent-verse repository
2. A Railway account (https://railway.app)
3. Environment variables from UCL API and other services

## Architecture

This project uses a monorepo structure with separate deployments:

- **Backend**: Flask API (Python) running on Railway
- **Frontend**: SvelteKit app (Node.js) running on Railway
- **Database**: PostgreSQL (optional, via Railway plugin)

Both services are deployed from the same GitHub repository but in separate Railway services.

## Setup Steps

### 1. Link Your GitHub Repository to Railway

1. Go to https://railway.app and sign in
2. Create a new project
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account
5. Select the `agent-verse` repository

### 2. Create Backend Service

1. In your Railway project, click "New Service"
2. Select "GitHub Repo"
3. Choose your `agent-verse` repository
4. In the service settings:
   - **Name**: `backend`
   - **Root Directory**: `backend`
   - **Build Command**: (leave empty, Railway will auto-detect)
   - **Start Command**: (leave empty, uses Procfile)

5. Add environment variables:
   ```
   ENVIRONMENT=production
   CLIENT_ID=<your_ucl_client_id>
   CLIENT_SECRET=<your_ucl_client_secret>
   DATABASE_URL=<if_using_postgres>
   AWS_ACCESS_KEY_ID=<if_using_s3>
   AWS_SECRET_ACCESS_KEY=<if_using_s3>
   AWS_S3_BUCKET_NAME=<if_using_s3>
   ```

6. Railway will automatically detect the `Procfile` and deploy

### 3. Create Frontend Service

1. In your Railway project, click "New Service"
2. Select "GitHub Repo"
3. Choose your `agent-verse` repository
4. In the service settings:
   - **Name**: `frontend`
   - **Root Directory**: `frontend`
   - **Build Command**: (leave empty, uses Procfile)
   - **Start Command**: (leave empty, uses Procfile)

5. Add environment variables:
   ```
   VITE_API_URL=https://<your-backend-railway-url>
   ```
   
   To get your backend URL:
   - Go to your backend service in Railway
   - Copy the public URL from the "Deployments" tab

6. Railway will automatically detect the `Procfile` and deploy

### 4. Link Services (Optional but Recommended)

1. Go to the frontend service settings
2. Under "Variables", you can reference backend service variables
3. Set `VITE_API_URL=${{ Railway.Backend.RAILWAY_PUBLIC_URL }}`

This way, if your backend URL changes, the frontend automatically updates.

### 5. Database Setup (If Needed)

If your application needs PostgreSQL:

1. In your Railway project, click "New Service"
2. Select "Database" → "PostgreSQL"
3. Configure the database
4. Railway will automatically generate a `DATABASE_URL` environment variable
5. Share this URL with both backend and frontend services as needed

## Environment Variables Reference

### Backend (`backend/.env.example`)

```
CLIENT_ID=your_ucl_client_id
CLIENT_SECRET=your_ucl_client_secret
ENVIRONMENT=production
DATABASE_URL=postgresql://user:password@host:port/dbname
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET_NAME=your_bucket_name
AWS_REGION=us-east-1
```

### Frontend (`frontend/.env.example`)

```
VITE_API_URL=https://your-backend-service.railway.app
```

## Production Considerations

### Backend

- The Flask app runs with Gunicorn in production (see `backend/Procfile`)
- Playwright is configured to run in headless mode
- CORS is enabled to allow requests from the frontend
- The app listens on `$PORT` environment variable (Railway standard)

### Frontend

- Uses the Node.js adapter for SvelteKit (changed from Vercel)
- Builds to static files and serves them
- Communicates with backend via `VITE_API_URL` environment variable

## Deployment Workflow

1. **Make changes** to your code
2. **Commit and push** to GitHub
3. **Railway automatically detects** the push
4. **Services rebuild and redeploy**:
   - Backend: Dependencies installed, app starts via Gunicorn
   - Frontend: Dependencies installed, app built, started via Node adapter

You can monitor deployments in the Railway dashboard.

## Troubleshooting

### Backend won't start

- Check the logs in Railway dashboard
- Ensure all dependencies are in `requirements.txt`
- Verify `main.py` syntax and imports

### Frontend won't build

- Check that `@sveltejs/adapter-node` is installed
- Ensure all environment variables are set
- Check for TypeScript errors in build logs

### Frontend can't communicate with backend

- Verify `VITE_API_URL` is set correctly in frontend environment variables
- Ensure backend CORS is configured: `CORS(app)` in `main.py`
- Check browser console for CORS errors

### Playwright errors

- Ensure Playwright is in `requirements.txt`
- Verify headless mode is enabled in production

## Custom Domains

1. Go to your service in Railway
2. Click "Settings"
3. Under "Domain", add your custom domain
4. Update your DNS settings with the provided CNAME record

## Monitoring and Logs

- View logs: Click on any service → "Logs" tab
- Monitor metrics: Service dashboard shows CPU, memory, request count
- Set up alerts in Railway dashboard for issues

## Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [SvelteKit Deployment](https://kit.svelte.dev/docs/adapter-node)
- [Flask Production Deployment](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [Playwright Documentation](https://playwright.dev/python/)