# Story Spark Studio

Story Spark Studio creates original personalized bedtime stories, choose-your-path adventures, and family read-alouds.

## Product model

- Unlimited deterministic mini-stories are free.
- The `$19` lifetime toolkit includes 25 AI-crafted stories, printable books, narrator scripts, and a browser-local library.
- Stripe, Gumroad, and Payhip purchases activate through one internal license service.
- One license supports three browser installations.
- Names and saved story text remain in local browser storage.

## Local development

```powershell
python -m pytest
python scripts/serve.py --port 8810
```

## Production configuration

Set the variables shown in `.env.example`. A Redis-compatible Upstash REST database is required for persistent production licenses and atomic credit accounting. Without it, licensing is process-local and suitable only for development.


