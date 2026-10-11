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
