# Deploying To Vercel

This Django project is configured for Vercel with:

- `vercel.json` running `python manage.py collectstatic --noinput`
- `.python-version` set to Python 3.12
- WhiteNoise for collected static files
- `DATABASE_URL` support for production PostgreSQL
- local SQLite fallback for development

## 1. Create A Production Database

Use a hosted PostgreSQL database such as Neon, Supabase, Railway, Render, or a Vercel Marketplace database.

Copy its connection string. It should look similar to:

```txt
postgresql://USER:PASSWORD@HOST:PORT/DBNAME
```

## 2. Set Vercel Environment Variables

In Vercel, open the project settings and add:

```txt
SECRET_KEY=replace-with-a-long-random-secret
DEBUG=False
DATABASE_URL=your-postgres-url
ALLOWED_HOSTS=.vercel.app,your-domain.com
CSRF_TRUSTED_ORIGINS=https://*.vercel.app,https://your-domain.com
```

If you do not have a custom domain yet, keep only the Vercel values:

```txt
ALLOWED_HOSTS=.vercel.app
CSRF_TRUSTED_ORIGINS=https://*.vercel.app
```

## 3. Push To GitHub

This folder must be a Git repository before Vercel can import it:

```powershell
git init
git add .
git commit -m "Prepare Django app for Vercel"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

## 4. Import In Vercel

1. Go to Vercel.
2. Add a new project.
3. Import the GitHub repository.
4. Add the environment variables above.
5. Deploy.

## 5. Run Production Migrations

After the first deploy, run migrations using the same `DATABASE_URL`:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

## Important Note About Uploads

Vercel's filesystem is not persistent. Uploaded files in `media/`, such as profile photos, should be stored in external storage like Cloudinary, S3, Supabase Storage, or Vercel Blob before this app is used in production.
