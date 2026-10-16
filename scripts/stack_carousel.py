"""Genera assets/stack.svg: carrusel del stack en dos filas que se mueven en sentidos opuestos.

Uso: python scripts/stack_carousel.py > assets/stack.svg
Los logos salen de simple-icons (se descargan al generar y quedan incrustados en el SVG).
"""
import re
import sys
import urllib.request

SI = "https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/{}.svg"
INK, CHIP, LINE, BONE, ACC = "#0b0b0b", "#141312", "#2e2d2a", "#ece9e1", "#ff3b00"
ROWS = [
    [("React", "react"), ("Next.js", "nextdotjs"), ("Svelte", "svelte"), ("Astro", "astro"),
     ("TypeScript", "typescript"), ("JavaScript", "javascript"), ("Tailwind", "tailwindcss"),
     ("Three.js", "threedotjs"), ("HTML", "html5"), ("Figma", "figma")],
    [("Python", "python"), ("Django", "django"), ("Laravel", "laravel"), ("PHP", "php"),
     ("Node.js", "nodedotjs"), ("MySQL", "mysql"), ("MariaDB", "mariadb"), ("Supabase", "supabase"),
     ("Docker", "docker"), ("Git", "git"), ("GitLab", "gitlab"), ("Claude Code", "claude")],
]
W, ROW_H, CHIP_H, GAP, ICON, CH = 880, 56, 40, 10, 18, 8.4  # CH: ancho por carácter de mono 16px
MONO = "'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def icon_path(slug):
    try:
        with urllib.request.urlopen(SI.format(slug), timeout=20) as r:
            return re.search(r' d="([^"]+)"', r.read().decode()).group(1)
    except Exception:
        return None  # sin logo: el chip queda solo con texto


def chips(items, paths, y):
    out, x = [], 0
    for name, slug in items:
        p = paths[slug]
        tw = len(name) * CH
        w = 18 + (ICON + 10 if p else 0) + tw + 18
        out.append(f'<rect x="{x}" y="{y}" width="{w:.0f}" height="{CHIP_H}" fill="{CHIP}" stroke="{LINE}"/>')
        tx = x + 18
        if p:
            s = ICON / 24
            out.append(f'<path transform="translate({tx} {y + (CHIP_H - ICON) / 2}) scale({s})" fill="{ACC}" d="{p}"/>')
            tx += ICON + 10
        out.append(f'<text x="{tx}" y="{y + CHIP_H / 2 + 6}" textLength="{tw:.0f}" lengthAdjust="spacingAndGlyphs">{name.upper()}</text>')
        x += w + GAP
    return out, x  # x = ancho de una copia completa (con hueco final) -> loop sin salto


def main():
    paths = {slug: icon_path(slug) for row in ROWS for _, slug in row}
    H = len(ROWS) * ROW_H + 16
    body, css = [], []
    for i, row in enumerate(ROWS):
        y = 8 + i * ROW_H + (ROW_H - CHIP_H) / 2
        one, span = chips(row, paths, y)
        copies = -(-2 * W // int(span)) + 1  # copias suficientes para cubrir el ancho durante todo el loop
        groups = "".join(f'<g transform="translate({k * span:.0f} 0)">{"".join(one)}</g>' for k in range(copies))
        start = "0" if i % 2 == 0 else f"-{span:.0f}px"
        end = f"-{span:.0f}px" if i % 2 == 0 else "0"
        css.append(f"@keyframes r{i}{{from{{transform:translateX({start})}}to{{transform:translateX({end})}}}}"
                   f".r{i}{{animation:r{i} {span / 40:.0f}s linear infinite}}")
        body.append(f'<g class="r{i}">{groups}</g>')
    names = ", ".join(n for row in ROWS for n, _ in row)
    print(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Stack: {names}">')
    print(f"<style>text{{font:700 14px {MONO};fill:{BONE};letter-spacing:.06em}}{''.join(css)}"
          "@media (prefers-reduced-motion:reduce){.r0,.r1{animation:none}}</style>")
    print(f'<rect width="{W}" height="{H}" fill="{INK}"/>')
    print("\n".join(body))
    print("</svg>")
    missing = [s for s, p in paths.items() if not p]
    if missing:
        print("sin logo:", ", ".join(missing), file=sys.stderr)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
