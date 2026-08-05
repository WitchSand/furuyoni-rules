import type { APIRoute } from "astro";

import { loadSiteContent } from "../../lib/content-model";
import { sitePath } from "../../lib/site-path";

export const prerender = true;

export const GET: APIRoute = () => {
  const content = loadSiteContent();
  const base = import.meta.env.BASE_URL;
  return new Response(
    JSON.stringify({
      schemaVersion: 1,
      terms: content.glossary,
      routes: Object.fromEntries(
        content.glossary.map((term) => [term.id, sitePath(`/glossary/${term.id}/`, base)]),
      ),
    }),
    {
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "public, max-age=3600",
      },
    },
  );
};
