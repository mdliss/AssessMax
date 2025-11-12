# Railway Deployment Issue - S3 Presigned URL

## Problem
Production Railway deployment is still generating S3 presigned URLs for GET instead of PUT, causing 403 errors.

## Evidence
- Local code has `HttpMethod="PUT"` on line 89 of `backend/app/ingest/storage.py`
- Commit `f67acfc` contains the fix
- Railway logs show it deployed but S3 errors still show "GET" in CanonicalRequest
- Local testing with same code works perfectly

## Possible Causes
1. Railway build cache not cleared
2. Python bytecode cache (.pyc files) in Railway
3. Different boto3 version on Railway
4. Railway not actually deploying latest commit

## Solutions to Try

### Option 1: Clear Railway Cache
In Railway dashboard:
- Settings → Clear build cache
- Then redeploy

### Option 2: Force Fresh Deploy
Add a dummy change to force rebuild:
```bash
echo "# force rebuild" >> backend/app/ingest/storage.py
git commit -am "Force rebuild"
git push origin master
```

### Option 3: Check Railway Build Logs
Verify the deployment actually pulled commit `f67acfc` and installed dependencies correctly.

### Option 4: Check boto3 Version
Railway might have older boto3. Add to requirements.txt:
```
boto3>=1.28.0
```
