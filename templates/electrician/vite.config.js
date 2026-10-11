import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

/* One engine, one profile per segment: VITE_SEGMENT picks segments/<id> (default: electrician). */
const id = process.env.VITE_SEGMENT || 'electrician'
if (!/^[a-z][a-z-]*$/.test(id)) throw new Error(`Invalid VITE_SEGMENT: ${id}`)
const dir = fileURLToPath(new URL(`./segments/${id}/`, import.meta.url))
const segment = JSON.parse(readFileSync(dir + 'segment.json', 'utf8'))

/* Head defaults per segment; the generator rewrites them per business (tools/quick_site.py render_head). */
const head = {
  name: 'segment-head',
  transformIndexHtml: (html) => html
    .replaceAll('__TITLE__', `${segment.noun} | Your Company`)
    .replaceAll('__DESCRIPTION__', `Your Company: ${segment.activity}. Conheça os serviços e peça seu orçamento.`)
    .replaceAll('__HERO_META__', segment.hero_image
      ? `<meta property="og:image" content="${segment.hero_image}" />\n    <link rel="preload" as="image" href="${segment.hero_image}" />`
      : ''),
}

export default defineConfig({
  plugins: [react(), head],
  resolve: { alias: { '@segment': dir } },
  build: { outDir: id === 'electrician' ? 'dist' : `dist-${id}` },
  server: { port: 5173, open: false },
})
