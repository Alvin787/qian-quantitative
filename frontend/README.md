# Qian Quantitative Frontend

React + TypeScript + Vite single-page UI for the indicator dashboard shell.

## Stack

- React 19 + TypeScript
- Vite 8 (`@vitejs/plugin-react`)
- Tailwind CSS v4 (`@tailwindcss/vite`)
- shadcn/ui (`new-york`) with Lucide icons

Recommended: Node 24 LTS (see root `.nvmrc`). `package.json` `engines` requires Node `>=24.18.0` and does not pin away newer majors.

## Commands

```bash
npm install
npm run dev
npm run build
npm run lint
```

From the repository root, the Makefile wraps the same workflows for `frontend/` and `backend/`.
