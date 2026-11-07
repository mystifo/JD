# Frontend (placeholder)

The React application lands in **M3 — Frontend foundation and app shell**
(see `../docs/roadmap.md` and `../docs/frontend-architecture.md`).

Planned shape:

```text
frontend/
├── index.html
├── package.json
├── vite.config.js
├── public/
└── src/
    ├── main.jsx
    ├── app/            # router, providers, query client
    ├── api/            # axios client, CSRF handling, endpoint modules
    ├── components/
    ├── features/       # mood, journal, selfcare, calm, people, insights, settings
    ├── styles/         # tokens.css, global.css
    └── test/
```

No frontend code is created in M1 so that the API contract stays the single
source of truth until the backend foundation is green.
