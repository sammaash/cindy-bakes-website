# Cindy Bakes Delights website

React/Vite frontend for Cindy Bakes Delights. The chatbot backend is deployed separately.

## Local development

```powershell
npm install
npm run dev
```

Set `VITE_CAKE_BOT_URL` in `.env.local` to the local bot URL, for example `http://localhost:5001`.

## Vercel deployment

1. Import this project into Vercel.
2. Set the build command to `npm run build` and output directory to `dist`.
3. Add `VITE_CAKE_BOT_URL` with the public Railway URL of the chatbot API.
4. Add the final Vercel domain to the backend `CORS_ALLOWED_ORIGINS` value.
5. Deploy after the backend is available.

No secret belongs in `VITE_*` variables; Vite exposes them to browser code.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and Oxlint's TypeScript related rules in your project.
