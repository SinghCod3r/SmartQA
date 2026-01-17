# Smart QA - Vercel Deployment Guide

## The Problem
The app keeps crashing on Vercel because:
1. SQLite doesn't work on serverless (ephemeral filesystem)
2. PostgreSQL + SQLAlchemy has complex setup issues
3. The current configuration isn't compatible with Vercel's Python runtime

## The Solution: Use Vercel KV (Redis)

Vercel KV is a Redis-based key-value store that's **natively integrated** with Vercel and perfect for serverless apps.

### Steps to Deploy:

1. **Create Vercel KV Database**
   - Go to your Vercel Dashboard
   - Click "Storage" → "Create Database" → **"KV"** (not Postgres)
   - Name it "smartqa-kv"
   - Connect it to your project

2. **Environment Variables**
   - Vercel will automatically set `KV_REST_API_URL` and `KV_REST_API_TOKEN`
   - No manual configuration needed!

3. **Redeploy**
   - I will update the code to use Vercel KV
   - Push changes
   - Vercel will automatically redeploy

### What Will Work:
- ✅ User signup/login
- ✅ Session management
- ✅ Test case generation
- ✅ File history storage
- ✅ All AI providers

### What's Different:
- Uses Redis (Vercel KV) instead of PostgreSQL
- Much simpler, faster, and serverless-native
- No connection pooling issues
- No SQLAlchemy complexity

## Ready to proceed?
I'll update the code to use Vercel KV. You just need to:
1. Create the KV database in Vercel (takes 30 seconds)
2. Let me know when it's ready
3. I'll push the updated code
