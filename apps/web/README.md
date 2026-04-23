# Narriv web app

This is the Next.js frontend for Narriv. It talks to the local API service and provides the draft, score, compare, and refine workflow.

## Run locally

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

The frontend expects the API to be available through `NEXT_PUBLIC_API_BASE_URL`. See `.env.example` in this folder.

## Useful files

- `app/page.tsx`: main workflow screen
- `app/globals.css`: global styles
- `.env.example`: local frontend environment template
