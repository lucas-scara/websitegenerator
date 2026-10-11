// One input color drives the shared palette, including SVGs and animations.
import { deriveTheme } from './themeMath.js'
import segment from '../segment.json'

const supplied = window.WEBSITE_BUSINESS?.theme_color
const hex = /^#[0-9a-f]{6}$/i.test(supplied || '') ? supplied : segment.default_theme_color
const { rgb, dark, light, onPrimary } = deriveTheme(hex)
const colors = {primary:rgb, 'primary-dark':dark, 'primary-light':light, accent:light, 'accent-dark':dark}
for (const [key,color] of Object.entries(colors)) document.documentElement.style.setProperty('--theme-'+key,color.join(' '))
const foreground = onPrimary
document.documentElement.style.setProperty('--theme-on-primary',foreground)
document.querySelector('meta[name="theme-color"]')?.setAttribute('content',hex)

const icon = document.querySelector('link[rel="icon"]')
if (icon) icon.href = 'data:image/svg+xml,' + encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="12" fill="${hex}"/><path d="M27 7 14 27h10l-3 14 14-23H25z" fill="${foreground}"/></svg>`)
