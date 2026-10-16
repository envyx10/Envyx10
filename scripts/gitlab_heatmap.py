"""Genera assets/gitlab-heatmap.svg desde el calendario público de GitLab.

Uso: python scripts/gitlab_heatmap.py [usuario] > assets/gitlab-heatmap.svg
Solo stdlib: lo ejecuta la GitHub Action a diario.
"""
import json
import sys
import urllib.request
from datetime import date, timedelta

USER = sys.argv[1] if len(sys.argv) > 1 else "envyx10"
INK, LINE, MUTED, BONE, ACC = "#0b0b0b", "#2e2d2a", "#9a968e", "#ece9e1", "#ff3b00"
# Escala de ink a acento: nivel 0 = sin actividad.
LEVELS = ["#1a1918", "#5c1f0b", "#9c2a05", "#d43302", ACC]
MONTHS = "ENE FEB MAR ABR MAY JUN JUL AGO SEP OCT NOV DIC".split()
CELL, GAP, LEFT, TOP = 14, 3, 36, 64
MONO = "font-family:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def level(n, peak):
    if n == 0:
        return 0
    return min(4, 1 + int(3 * n / peak)) if peak else 1


def weekday_ratio(days, counts):
    """% de días laborables con actividad desde el primer día con contribuciones."""
    active = [d for d in days if counts.get(d.isoformat())]
    if not active:
        return 0
    span = [d for d in days if d >= active[0] and d.weekday() < 5]
    return round(100 * sum(1 for d in span if counts.get(d.isoformat())) / len(span))


def render(counts, today):
    # 53 semanas completas terminando en la semana de hoy (semanas de lunes a domingo).
    start = today - timedelta(days=today.weekday()) - timedelta(weeks=52)
    days = [start + timedelta(days=i) for i in range((today - start).days + 1)]
    values = [counts.get(d.isoformat(), 0) for d in days]
    total, active = sum(values), sum(1 for v in values if v)
    peak = sorted(values)[int(len(values) * 0.98)] or max(values) or 1  # p98: un día raro no apaga el resto
    ratio = weekday_ratio(days, counts)

    width = LEFT + 53 * (CELL + GAP) + 16
    height = TOP + 7 * (CELL + GAP) + 44
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Actividad en GitLab: {total} contribuciones en {active} días el último año">',
        f'<rect width="{width}" height="{height}" fill="{INK}"/>',
        f'<g style="{MONO};font-size:11px;letter-spacing:.08em">',
        f'<text x="16" y="26" fill="{BONE}" font-weight="700">GITLAB / @{USER.upper()}</text>',
        f'<text x="{width - 16}" y="26" fill="{MUTED}" text-anchor="end">'
        f'<tspan fill="{ACC}" font-weight="700">{total}</tspan> CONTRIBUCIONES · {active} DÍAS · '
        f'<tspan fill="{BONE}">{ratio}%</tspan> DE DÍAS LABORABLES</text>',
        f'<line x1="0" y1="40" x2="{width}" y2="40" stroke="{LINE}"/>',
    ]
    for row, label in ((0, "L"), (2, "X"), (4, "V")):
        out.append(f'<text x="16" y="{TOP + row * (CELL + GAP) + 11}" fill="{MUTED}">{label}</text>')
    last_month = None
    for i, (d, v) in enumerate(zip(days, values)):
        col, row = i // 7, d.weekday()
        x, y = LEFT + col * (CELL + GAP), TOP + row * (CELL + GAP)
        if row == 0 and d.month != last_month:
            last_month = d.month
            if col < 52:  # sin etiqueta cortada en la última columna
                out.append(f'<text x="{x}" y="{TOP - 8}" fill="{MUTED}">{MONTHS[d.month - 1]}</text>')
        out.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{LEVELS[level(v, peak)]}">'
                   f'<title>{d.isoformat()}: {v}</title></rect>')
    ly = height - 22
    out.append(f'<text x="{width - 16 - 5 * (CELL + GAP) - 44}" y="{ly + 11}" fill="{MUTED}" text-anchor="end">MENOS</text>')
    for k, color in enumerate(LEVELS):
        out.append(f'<rect x="{width - 16 - 40 - (5 - k) * (CELL + GAP)}" y="{ly}" width="{CELL}" height="{CELL}" fill="{color}"/>')
    out.append(f'<text x="{width - 16}" y="{ly + 11}" fill="{MUTED}" text-anchor="end">MÁS</text>')
    out.append(f'<text x="16" y="{ly + 11}" fill="{MUTED}">ACTUALIZADO {today.isoformat()}</text>')
    out.append("</g></svg>")
    return "\n".join(out)


if __name__ == "__main__":
    # Self-check: lun-vie 5-9 ene 2026, activo 4 de 5 laborables + finde vacío no cuenta.
    ds = [date(2026, 1, 5) + timedelta(days=i) for i in range(7)]
    assert weekday_ratio(ds, {d.isoformat(): 1 for d in ds[:4]}) == 80
    assert level(0, 10) == 0 and level(10, 10) == 4 and level(1, 10) == 1

    url = f"https://gitlab.com/users/{USER}/calendar.json"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "heatmap"}), timeout=30) as r:
        counts = json.load(r)
    if not counts:
        sys.exit("calendar.json vacío: revisa la privacidad del perfil de GitLab")  # no pisar el SVG bueno
    sys.stdout.reconfigure(encoding="utf-8")
    print(render(counts, date.today()))
