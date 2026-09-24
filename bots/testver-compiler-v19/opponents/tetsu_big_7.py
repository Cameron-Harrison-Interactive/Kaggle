from pathlib import Path
from collections import Counter
from cycler import cycler
import contextlib
import gzip
import html
import hashlib
import io
import math
import py_compile
import tarfile
import tempfile

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
import pandas as pd
from IPython.display import HTML, Image, display

# Silence only optional environment import chatter.
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments import make

# Figures use a light, self-contained canvas so the saved outputs remain readable
# in both Kaggle light and dark themes.
FOREST = "#F7FAF8"
PANEL = "#FFFFFF"
GRID = "#D6E2DA"
TEXT = "#173322"
MUTED = "#607168"
PALETTE = ["#23864F", "#168A9A", "#B78312", "#8B5FB2", "#C75B4F", "#5577B8"]

plt.rcParams.update({
    "figure.dpi": 92,
    "savefig.dpi": 92,
    "font.size": 10,
    "figure.facecolor": FOREST,
    "axes.facecolor": PANEL,
    "axes.edgecolor": GRID,
    "axes.labelcolor": TEXT,
    "axes.titlecolor": TEXT,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "text.color": TEXT,
    "grid.color": GRID,
    "axes.prop_cycle": cycler(color=PALETTE),
})

def forest_axes(ax, title=None, xlabel=None, ylabel=None):
    ax.set_facecolor(PANEL)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors=MUTED)
    ax.grid(alpha=.55)
    if title:
        ax.set_title(title, color=TEXT, fontsize=14, fontweight="bold", pad=12)
    if xlabel:
        ax.set_xlabel(xlabel, color=TEXT)
    if ylabel:
        ax.set_ylabel(ylabel, color=TEXT)
    return ax

def show_forest_figure(fig, quality=84):
    fig.patch.set_facecolor(FOREST)
    buffer = io.BytesIO()
    fig.savefig(
        buffer,
        format="jpeg",
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        pil_kwargs={"quality": quality, "optimize": True},
    )
    plt.close(fig)
    display(Image(data=buffer.getvalue(), format="jpeg"))

def show_forest_table(frame, caption=None, formats=None):
    """Theme-independent compact table for precise audit data."""
    table = frame.copy()
    if formats:
        for column, formatter in formats.items():
            if column in table:
                table[column] = table[column].map(formatter)
    caption_html = f'<div style="font-size:12px;letter-spacing:.10em;text-transform:uppercase;font-weight:800;color:#176b42;margin:0 0 9px">{caption}</div>' if caption else ""
    html = table.to_html(index=False, border=0, classes="forest-table", escape=False)
    style = ("<style>.forest-table{border-collapse:collapse;width:100%;color:#173322;font-size:13.5px}"
             ".forest-table th{background:#eef6f1;color:#274b38;text-align:left;padding:10px 11px;border-bottom:1px solid #cbded1;font-size:12px;letter-spacing:.02em}"
             ".forest-table td{padding:9px 11px;border-bottom:1px solid #e1ebe4;color:#294438}"
             ".forest-table tr:nth-child(even){background:#f8fbf9}.forest-table tr:nth-child(odd){background:#fff}"
             ".forest-table tbody tr:last-child td{border-bottom:0}</style>")
    wrapper = '<div style="background:#fff;border:1px solid #d3e1d8;border-radius:17px;padding:15px 16px;overflow-x:auto;box-shadow:0 5px 16px rgba(24,68,44,.05);color:#173322">'
    display(HTML(wrapper + caption_html + style + html + "</div>"))


def show_kpi_cards(items, eyebrow="Observed in this run"):
    cards = []
    for label, value, note, accent in items:
        cards.append(
            f'<div style="background:#fff;border:1px solid #d5e3da;border-top:4px solid {accent};border-radius:16px;padding:14px 15px;color:#173322;box-shadow:0 4px 14px rgba(24,68,44,.04)">'
            f'<div style="font-size:10px;letter-spacing:.11em;text-transform:uppercase;font-weight:800;color:#64786c">{label}</div>'
            f'<div style="font-size:23px;font-weight:850;letter-spacing:-.02em;margin:3px 0 2px;color:#173322">{value}</div>'
            f'<div style="font-size:12px;color:#687970;line-height:1.35">{note}</div></div>'
        )
    display(HTML(
        f'<div style="font-size:12px;letter-spacing:.10em;text-transform:uppercase;font-weight:800;color:#176b42;margin:18px 0 8px">{eyebrow}</div>'
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:10px;margin:0 0 12px">' + ''.join(cards) + '</div>'
    ))


def show_insight(title, body, accent="#2a8a54", tag="INSIGHT"):
    display(HTML(
        f'<div style="background:#fff;border:1px solid #d5e3da;border-left:5px solid {accent};border-radius:15px;padding:14px 16px;margin:12px 0;color:#173322;box-shadow:0 4px 14px rgba(24,68,44,.04)">'
        f'<div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;font-weight:800;color:{accent};margin-bottom:4px">{tag}</div>'
        f'<div style="font-weight:800;margin-bottom:4px;color:#173322">{title}</div>'
        f'<div style="color:#53695d;line-height:1.55;font-size:13.5px">{body}</div></div>'
    ))

def shade_season_phases(ax):
    """Light phase bands that connect diagnostics to the 30-day strategy atlas."""
    phases = [
        (1, 5, "BUILD", "#2A8A54"),
        (5, 20, "SCALE", "#168A9A"),
        (20, 28, "PROTECT", "#8B5FB2"),
        (28, 30, "CLOSE", "#B78312"),
    ]
    for start, end, label, color in phases:
        ax.axvspan(start, end, color=color, alpha=.055, lw=0, zorder=0)
        ax.text(
            (start + end) / 2,
            .965,
            label,
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="top",
            fontsize=8,
            fontweight="bold",
            color=color,
            alpha=.82,
        )
    return ax


def show_market_motion(prices, item="STRAWBERRY", probe_quantity=20):
    """A tiny SVG animation: no GIF, no base64, and only a few KB of notebook output."""
    prices = np.asarray(prices, dtype=float)
    revenue = np.cumsum(prices)
    if len(prices) < 3:
        return

    width, height = 960, 370
    left = (62, 86, 360, 205)
    right = (540, 86, 360, 205)

    def path_for(values, box):
        x0, y0, w, h = box
        values = np.asarray(values, dtype=float)
        lo, hi = float(values.min()), float(values.max())
        span = max(hi - lo, 1.0)
        pts = []
        for i, value in enumerate(values):
            x = x0 + (w * i / max(len(values) - 1, 1))
            y = y0 + h - h * (float(value) - lo) / span
            pts.append((x, y))
        return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts), lo, hi

    price_path, p_lo, p_hi = path_for(prices, left)
    rev_path, r_lo, r_hi = path_for(revenue, right)
    q = min(int(probe_quantity), max(1, len(prices) // 3))
    impact_score = float(q * max(0, prices[0] - prices[min(q, len(prices)-1)]))

    def money(v):
        return f"${v:,.0f}"

    svg = f'''<div style="background:#fff;border:1px solid #d5e3da;border-radius:22px;padding:16px 16px 12px;box-shadow:0 8px 24px rgba(24,68,44,.06);margin:12px 0 16px;overflow-x:auto;color:#173322">
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin:0 0 10px">
      <div style="flex:1;min-width:145px;background:#f2faf5;border:1px solid #d8e8dd;border-radius:14px;padding:10px 12px"><div style="font-size:10px;letter-spacing:.11em;font-weight:800;color:#607168">OPENING QUOTE</div><div style="font-size:21px;font-weight:850;color:#173322">{money(prices[0])}</div></div>
      <div style="flex:1;min-width:145px;background:#eef8fa;border:1px solid #d5e6e9;border-radius:14px;padding:10px 12px"><div style="font-size:10px;letter-spacing:.11em;font-weight:800;color:#607168">AFTER {len(prices)} UNITS</div><div style="font-size:21px;font-weight:850;color:#173322">{money(prices[-1])}</div></div>
      <div style="flex:1;min-width:145px;background:#f8f1fb;border:1px solid #e5d9ec;border-radius:14px;padding:10px 12px"><div style="font-size:10px;letter-spacing:.11em;font-weight:800;color:#607168">{q}-UNIT IMPACT SCORE</div><div style="font-size:21px;font-weight:850;color:#173322">{money(impact_score)}</div></div>
      <div style="flex:1;min-width:145px;background:#fff8e9;border:1px solid #eee0bf;border-radius:14px;padding:10px 12px"><div style="font-size:10px;letter-spacing:.11em;font-weight:800;color:#607168">TOTAL REVENUE</div><div style="font-size:21px;font-weight:850;color:#173322">{money(revenue[-1])}</div></div>
    </div>
    <svg viewBox="0 0 {width} {height}" width="100%" style="min-width:760px;max-width:980px;display:block;margin:auto" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" role="img" aria-label="Animated market price erosion and cumulative revenue">
      <defs>
        <linearGradient id="kgPriceGrad" x1="0" x2="1"><stop offset="0" stop-color="#23864F"/><stop offset="1" stop-color="#168A9A"/></linearGradient>
        <linearGradient id="kgRevGrad" x1="0" x2="1"><stop offset="0" stop-color="#168A9A"/><stop offset="1" stop-color="#8B5FB2"/></linearGradient>
        <filter id="kgGlow"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      <rect x="18" y="14" width="924" height="334" rx="22" fill="#F7FAF8" stroke="#D6E2DA"/>
      <text x="62" y="48" fill="#173322" font-size="17" font-weight="800">Market pressure in motion · {item.title()}</text>
      <text x="62" y="68" fill="#607168" font-size="12">The same sale becomes less valuable as shared inventory moves before it.</text>

      <rect x="44" y="78" width="396" height="232" rx="16" fill="#fff" stroke="#D6E2DA"/>
      <rect x="522" y="78" width="396" height="232" rx="16" fill="#fff" stroke="#D6E2DA"/>
      <text x="62" y="105" fill="#173322" font-size="13" font-weight="800">SELL PRICE</text>
      <text x="540" y="105" fill="#173322" font-size="13" font-weight="800">CUMULATIVE REVENUE</text>
      <text x="62" y="299" fill="#607168" font-size="11">units added to shared market inventory →</text>
      <text x="540" y="299" fill="#607168" font-size="11">units sold →</text>
      <text x="404" y="126" text-anchor="end" fill="#607168" font-size="10">{money(p_hi)}</text>
      <text x="404" y="282" text-anchor="end" fill="#607168" font-size="10">{money(p_lo)}</text>
      <text x="882" y="126" text-anchor="end" fill="#607168" font-size="10">{money(r_hi)}</text>
      <text x="882" y="282" text-anchor="end" fill="#607168" font-size="10">{money(r_lo)}</text>

      <path d="{price_path}" fill="none" stroke="#BFD6C8" stroke-width="4" opacity=".5"/>
      <path id="kgPricePath" d="{price_path}" pathLength="1" fill="none" stroke="url(#kgPriceGrad)" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1" stroke-dashoffset="1">
        <animate attributeName="stroke-dashoffset" values="1;0;0;1" keyTimes="0;.76;.92;1" dur="7s" repeatCount="indefinite"/>
      </path>
      <circle r="6" fill="#23864F" stroke="#fff" stroke-width="2" filter="url(#kgGlow)">
        <animateMotion dur="7s" repeatCount="indefinite" keyPoints="0;1;1;0" keyTimes="0;.76;.92;1" calcMode="linear"><mpath xlink:href="#kgPricePath"/></animateMotion>
      </circle>

      <path d="{rev_path}" fill="none" stroke="#C9D9E1" stroke-width="4" opacity=".5"/>
      <path id="kgRevPath" d="{rev_path}" pathLength="1" fill="none" stroke="url(#kgRevGrad)" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1" stroke-dashoffset="1">
        <animate attributeName="stroke-dashoffset" values="1;0;0;1" keyTimes="0;.76;.92;1" dur="7s" repeatCount="indefinite"/>
      </path>
      <circle r="6" fill="#8B5FB2" stroke="#fff" stroke-width="2" filter="url(#kgGlow)">
        <animateMotion dur="7s" repeatCount="indefinite" keyPoints="0;1;1;0" keyTimes="0;.76;.92;1" calcMode="linear"><mpath xlink:href="#kgRevPath"/></animateMotion>
      </circle>

      <text x="480" y="338" text-anchor="middle" fill="#53695D" font-size="12">SVG animation: lightweight, vector-sharp, and free of embedded GIF/base64 payloads.</text>
    </svg></div>'''
    display(HTML(svg))



def show_farm_motion(env, seat=0, stride=6, duration=18):
    frames = list(range(0, len(env.steps), stride))
    if frames[-1] != len(env.steps)-1:
        frames.append(len(env.steps)-1)
    observations = [env.steps[idx][seat].observation for idx in frames]
    player_id = int(observations[0].player)
    farms = [obs.farms[player_id] for obs in observations]
    rows, cols = len(farms[0]['tiles']), len(farms[0]['tiles'][0])

    colors = {
        'LOCKED':'#20362C','EMPTY':'#E6EEE9','WHEAT':'#E5B94E','STRAWBERRY':'#D85C70',
        'MELON':'#61B873','PASTURE':'#4B9DA5','WEED':'#A66BB5','OTHER':'#A9B8AF'
    }
    def category(tile):
        if tile == 'LOCKED': return 'LOCKED'
        if tile is None: return 'EMPTY'
        if isinstance(tile, dict):
            kind = tile.get('kind')
            if kind == 'PLANT': return tile.get('crop','OTHER')
            if kind == 'PASTURE': return 'PASTURE'
            if kind == 'WEED': return 'WEED'
        return 'OTHER'

    cell=27; gap=2; map_x=34; map_y=74
    map_w=cols*cell; map_h=rows*cell
    width=960; height=405
    parts=[]
    parts.append(f'<div style="background:#fff;border:1px solid #d5e3da;border-radius:24px;padding:14px 14px 10px;box-shadow:0 10px 28px rgba(24,68,44,.07);margin:14px 0 16px;overflow-x:auto;color:#173322">')
    parts.append(f'<svg viewBox="0 0 {width} {height}" width="100%" style="min-width:760px;max-width:1040px;display:block;margin:auto" xmlns="http://www.w3.org/2000/svg">')
    parts.append('<rect x="8" y="8" width="944" height="389" rx="22" fill="#F7FAF8" stroke="#D6E2DA"/>')
    parts.append('<text x="34" y="34" font-size="17" font-weight="800" fill="#173322">Farm topology in motion</text>')
    parts.append('<text x="34" y="54" font-size="11.5" fill="#607168">A compressed replay of the full 720-turn season · tiles + farmer + hired hands</text>')

    # phase rail
    phase_x=495; phase_y=35; phase_w=410
    phases=[(0,.17,'BUILD','#2A8A54'),(.17,.67,'SCALE','#168A9A'),(.67,.93,'PROTECT','#8B5FB2'),(.93,1.0,'CLOSE','#B78312')]
    for a,b,label,color in phases:
        x=phase_x+a*phase_w; w=(b-a)*phase_w
        parts.append(f'<rect x="{x:.1f}" y="{phase_y}" width="{w:.1f}" height="7" rx="3.5" fill="{color}" opacity=".72"/>')
        if w>45:
            parts.append(f'<text x="{x+w/2:.1f}" y="{phase_y+22}" text-anchor="middle" font-size="9" font-weight="800" fill="{color}">{label}</text>')
    parts.append(f'<circle cx="{phase_x}" cy="{phase_y+3.5}" r="6" fill="#FFFFFF" stroke="#173322" stroke-width="2"><animate attributeName="cx" values="{phase_x};{phase_x+phase_w}" dur="{duration}s" repeatCount="indefinite"/></circle>')

    # map background and grid
    parts.append(f'<rect x="{map_x-8}" y="{map_y-8}" width="{map_w+16}" height="{map_h+16}" rx="18" fill="#FFFFFF" stroke="#D6E2DA"/>')
    nframes=len(frames)
    for r in range(rows):
        for c in range(cols):
            vals=[colors[category(f['tiles'][r][c])] for f in farms]
            x=map_x+c*cell; y=map_y+r*cell
            parts.append(f'<rect x="{x}" y="{y}" width="{cell-gap}" height="{cell-gap}" rx="4" fill="{vals[0]}"><animate attributeName="fill" values="{";".join(vals)}" dur="{duration}s" calcMode="discrete" repeatCount="indefinite"/></rect>')

    # moving farmer
    fx=[]; fy=[]
    for farm in farms:
        rr,cc=farm['farmer']
        fx.append(map_x+cc*cell+(cell-gap)/2); fy.append(map_y+rr*cell+(cell-gap)/2)
    parts.append(f'<circle cx="{fx[0]:.1f}" cy="{fy[0]:.1f}" r="8.8" fill="#FFFFFF" stroke="#173322" stroke-width="3"><animate attributeName="cx" values="{";".join(f"{v:.1f}" for v in fx)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="cy" values="{";".join(f"{v:.1f}" for v in fy)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/></circle>')
    parts.append(f'<circle cx="{fx[0]:.1f}" cy="{fy[0]:.1f}" r="3.2" fill="#2A8A54"><animate attributeName="cx" values="{";".join(f"{v:.1f}" for v in fx)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="cy" values="{";".join(f"{v:.1f}" for v in fy)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/></circle>')

    # hired hands
    max_hands=max(len(f['hands']) for f in farms)
    offsets=[(-5,-5),(5,-5),(-5,5),(5,5),(0,-7),(0,7),(-7,0),(7,0)]
    for h in range(max_hands):
        xs=[]; ys=[]; op=[]
        dx,dy=offsets[h%len(offsets)]
        for f in farms:
            if h < len(f['hands']):
                rr,cc=f['hands'][h]
                xs.append(map_x+cc*cell+(cell-gap)/2+dx*.55); ys.append(map_y+rr*cell+(cell-gap)/2+dy*.55); op.append('0.9')
            else:
                xs.append(map_x); ys.append(map_y); op.append('0')
        parts.append(f'<circle cx="{xs[0]:.1f}" cy="{ys[0]:.1f}" r="3.3" fill="#D7F4F7" stroke="#168A9A" stroke-width="1.4" opacity="{op[0]}"><animate attributeName="cx" values="{";".join(f"{v:.1f}" for v in xs)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="cy" values="{";".join(f"{v:.1f}" for v in ys)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="opacity" values="{";".join(op)}" dur="{duration}s" calcMode="discrete" repeatCount="indefinite"/></circle>')

    # right-side legend / readout
    sx=350
    parts.append(f'<text x="{sx}" y="88" font-size="11" font-weight="800" letter-spacing="1.3" fill="#607168">WHAT TO WATCH</text>')
    notes=[('Capacity expands','More cells become productive before the closeout.','#2A8A54'),('Labor circulates','White/teal markers reveal routing and service pressure.','#168A9A'),('Weeds are local shocks','Purple cells appear stochastically; repair should stay local.','#A66BB5'),('Deadline changes behavior','The final phase converts operating value back to cash.','#B78312')]
    yy=108
    for title,desc,col in notes:
        parts.append(f'<circle cx="{sx+4}" cy="{yy+3}" r="4" fill="{col}"/><text x="{sx+17}" y="{yy+6}" font-size="12.5" font-weight="800" fill="#173322">{html.escape(title)}</text><text x="{sx+17}" y="{yy+24}" font-size="10.5" fill="#607168">{html.escape(desc)}</text>')
        yy+=52

    # legend
    parts.append(f'<text x="{sx}" y="317" font-size="10" font-weight="800" letter-spacing="1.2" fill="#607168">TILES</text>')
    legend=[('Empty','EMPTY'),('Wheat','WHEAT'),('Strawberry','STRAWBERRY'),('Melon','MELON'),('Pasture','PASTURE'),('Weed','WEED'),('Locked','LOCKED')]
    lx=sx; ly=331
    for i,(label,key) in enumerate(legend):
        col=i%4; row=i//4; x=lx+col*112; y=ly+row*27
        parts.append(f'<rect x="{x}" y="{y-10}" width="13" height="13" rx="3" fill="{colors[key]}"/><text x="{x+19}" y="{y+1}" font-size="10" fill="#53695D">{label}</text>')
    parts.append(f'<circle cx="{sx+4}" cy="389" r="6" fill="#fff" stroke="#173322" stroke-width="2"/><text x="{sx+17}" y="393" font-size="10" fill="#53695D">Farmer</text><circle cx="{sx+99}" cy="389" r="3.3" fill="#D7F4F7" stroke="#168A9A" stroke-width="1.3"/><text x="{sx+111}" y="393" font-size="10" fill="#53695D">Hands</text>')
    parts.append('</svg></div>')
    display(HTML(''.join(parts)))



