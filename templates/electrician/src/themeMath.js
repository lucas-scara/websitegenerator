/* Pure color math for the theme (also exercised by tests/test_theme_contrast.py). */
const mix = (color, target, amount) => color.map((n, i) => Math.round(n + (target[i] - n) * amount))
export const luminance = (color) => color.map((n) => { const c = n / 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4 }).reduce((s, n, i) => s + n * [0.2126, 0.7152, 0.0722][i], 0)

/* From one brand color: a dark variant for text on light backgrounds, a light one for text on dark, and the legible text color for the brand color itself. */
export function deriveTheme(hex) {
  const rgb = hex.slice(1).match(/../g).map((n) => parseInt(n, 16))
  let dark = rgb
  while (luminance(dark) > 0.16) dark = mix(dark, [0, 0, 0], 0.1)
  let light = rgb
  while (luminance(light) < 0.55) light = mix(light, [255, 255, 255], 0.12)
  return { rgb, dark, light, onPrimary: luminance(rgb) > 0.179 ? '#000000' : '#ffffff' }
}
