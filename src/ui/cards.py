"""Small HTML fragments for the dark team calculator view."""
import html

from src.ui.style import GREY, text_color


CSS = """<style>
.row{display:grid;grid-template-columns:64px 128px 64px 124px 86px 72px 1fr;gap:8px;align-items:center;padding:8px 10px;background:#171B20;border:1px solid #30363D;border-radius:8px;color:#F2F3F4;font:12px sans-serif;margin:4px 0}
.asset-group{display:flex;gap:5px;align-items:flex-start;flex-wrap:wrap}.asset-grid{display:grid;grid-template-columns:repeat(2,56px);gap:4px}
.card{box-sizing:border-box;width:56px;min-height:54px;border-radius:5px;padding:4px 3px;text-align:center;display:flex;flex-direction:column;justify-content:center;font-weight:700;overflow:hidden}
.card-id{font-size:11px;line-height:14px}.card-stat{font:10px/12px ui-monospace,monospace;white-space:nowrap}.card-constructor{background:#171B20}.card-driver{box-shadow:inset 0 0 0 1px rgba(255,255,255,.18)}
.row-label{font-weight:700}.row.head{background:none;border:none;padding:0 10px;margin:8px 0 0;color:#858B93;font-size:11px;font-weight:700}.row-money,.row-xpts{font:11px/16px ui-monospace,monospace}.row-xpts{font-size:14px;font-weight:700}.chips{display:flex;flex-wrap:wrap;gap:4px;align-content:center}.chip{font-size:10px;font-weight:700;white-space:nowrap;padding:3px 6px;border-radius:4px;background:#F2F3F4;color:#000}.chip.used{background:#2EB86A;color:#000}.chip.gone{background:#4A4F56;color:#B5BAC1}
.swap-strip{padding:5px 9px;margin:3px 0 8px;background:#171B20;border-left:2px solid #E10600;border-radius:3px;color:#F2F3F4;font:12px ui-monospace,monospace}
.tcard{display:grid;grid-template-columns:auto auto auto 1fr;gap:8px;align-items:center;padding:10px;background:#111418;border:1px solid #2A2F36;border-radius:10px;color:#F2F3F4;font:12px sans-serif}
.tcol{display:flex;flex-direction:column;gap:4px}.x2col{align-items:center}.x2col .card{outline:2px solid #E10600;outline-offset:2px}.x2-tag{margin-top:2px;padding:1px 6px;border-radius:3px;background:#E10600;color:#FFF;font:700 10px sans-serif}.tstat{display:flex;flex-direction:column;gap:4px;align-items:stretch}
.tbox{background:#1B1F25;border:1px solid #2A2F36;border-radius:6px;padding:6px 8px;text-align:center;font:12px/16px ui-monospace,monospace;color:#C9CDD2}.tbox.big{font-size:15px;font-weight:700;color:#F2F3F4}
.chip-grid{display:grid;grid-template-columns:repeat(3,52px);gap:6px;justify-content:center}
.chip-tile{box-sizing:border-box;width:52px;height:52px;border-radius:8px;display:flex;align-items:center;justify-content:center;font:700 14px sans-serif;background:#F2F3F4;color:#000;border:1px solid #F2F3F4;transition:transform .15s}
.chip-tile:hover{transform:translateY(-2px)}.chip-tile.used{background:#2EB86A;border-color:#2EB86A}.chip-tile.gone{background:#2A2F36;border-color:#3A4048;color:#7D838B;text-decoration:line-through}
.app-head{display:flex;align-items:center;gap:10px;margin:-8px 0 4px}.app-mark{width:6px;height:26px;border-radius:3px;background:#E10600;box-shadow:0 0 12px rgba(225,6,0,.6)}
.app-title{font:800 24px/1 sans-serif;letter-spacing:.5px;color:#F2F3F4}.app-title span{color:#E10600}
[role="tablist"]{gap:6px;border:none}.react-aria-SelectionIndicator{display:none}
[data-testid="stTab"]{padding:6px 16px;border-radius:999px;color:#9AA0A6;transition:background .2s,color .2s,transform .15s}
[data-testid="stTab"]:hover{background:#1B1F25;color:#F2F3F4;transform:translateY(-1px)}
[data-testid="stTab"][aria-selected="true"]{background:#E10600;color:#FFF}
[data-testid="stTab"][aria-selected="true"] p{color:#FFF}
.sk-wrap{display:flex;flex-direction:column;gap:8px;margin:4px 0}.sk-team{display:grid;grid-template-columns:5fr 2fr 4fr;gap:16px;align-items:start}
.sk-col{display:flex;flex-direction:column;gap:8px}.sk-chips{display:grid;grid-template-columns:repeat(3,52px);gap:6px;justify-content:center}
.sk{background:#262B31;border-radius:8px;animation:sk-pulse 1.6s ease-in-out infinite}
.sk-title{height:20px;width:70px;border-radius:4px}.sk-card{height:140px;border-radius:10px}.sk-select{height:40px}.sk-chip{width:52px;height:52px}
.sk-bar{height:40px}.sk-row{height:128px}.sk-head{height:18px;width:60%;border-radius:4px}.sk-chart{height:300px;border-radius:10px}
@keyframes sk-pulse{0%,100%{opacity:1}50%{opacity:.45}}
@media(prefers-reduced-motion:reduce){.sk{animation:none}}
.load-error{padding:16px;text-align:center;color:#F2F3F4;font:13px sans-serif}
[data-stale="true"]{opacity:1!important}
@media(max-width:850px){.row{grid-template-columns:40px 1fr 56px 1fr;}.row-money,.row-xpts,.chips{grid-row:2}}
</style>"""


def _number(value: float | None) -> str:
    return "—" if value is None else f"{value:.1f}"


def asset_card(asset_id: str, kind: str, color: str | None, price: float | None, xpts: float | None) -> str:
    asset_id = html.escape(str(asset_id))
    color = color or GREY
    if kind == "driver":
        style = f"background:{color};color:{text_color(color)}"
        class_name = "card card-driver"
    else:
        style = f"border:2px solid {color};color:#F2F3F4;background:#171B20"
        class_name = "card card-constructor"
    return (f'<div class="{class_name}" style="{style}"><span class="card-id">{asset_id}</span>'
            f'<span class="card-stat">{_number(price)}</span><span class="card-stat">{_number(xpts)}</span></div>')


def chip_badges(all_chips: list[str], chips_left: list[str], selected: str | None,
                played_now: str | None) -> str:
    checked = played_now or selected
    badges = []
    for chip in all_chips:
        safe = html.escape(chip)
        if chip == checked:
            badges.append(f'<span class="chip used">✓ {safe}</span>')
        elif chip not in chips_left:
            badges.append(f'<span class="chip gone"><s>{safe}</s></span>')
        else:
            badges.append(f'<span class="chip">{safe}</span>')
    return f'<div class="chips">{"".join(badges)}</div>' if badges else ""


HEADER = '<div class="app-head"><div class="app-mark"></div><div class="app-title">F1 <span>Fantasy</span></div></div>'
CHIP_LABELS = {"limitless": "LL", "wildcard": "WC", "x3_boost": "X3", "no_negative": "NN",
               "autopilot": "AP", "final_fix": "FF"}


def _skeleton(inner: str, cls: str = "sk-wrap") -> str:
    """Busy wrapper read once as "Loading"; the boxes inside are hidden from screen readers."""
    return f'<div class="{cls}" role="status" aria-busy="true" aria-label="Loading">{inner}</div>'


def _boxes(kind: str, n: int = 1) -> str:
    return f'<div class="sk {kind}" aria-hidden="true"></div>' * n


def team_skeleton() -> str:
    """Placeholder for one My Team row: card | chip select + 3x2 chips | four expanders (5:2:4 like the real columns)."""
    return _skeleton(f'<div class="sk-col">{_boxes("sk-title")}{_boxes("sk-card")}</div>'
                     f'<div class="sk-col">{_boxes("sk-title")}{_boxes("sk-select")}'
                     f'<div class="sk-chips">{_boxes("sk-chip", 6)}</div></div>'
                     f'<div class="sk-col">{_boxes("sk-bar", 4)}</div>', "sk-team")


def best_skeleton(rows: int = 8) -> str:
    return _skeleton(_boxes("sk-head") + _boxes("sk-row", rows))


def timeline_skeleton() -> str:
    return _skeleton(_boxes("sk-head") + _boxes("sk-chart"))


def load_error(thing: str) -> str:
    """One-line failure message in place of a skeleton; the caller adds the Retry button."""
    return (f"<div class='load-error' role='alert'>Couldn't load {html.escape(thing)}. "
            "Is the data built? Try the Update tab.</div>")


def chip_grid(all_chips: list[str], chips_left: list[str], selected: str | None, played_now: str | None) -> str:
    """Square chip tiles, 3 per row: green = this weekend, struck grey = played, white = left."""
    checked = played_now or selected
    tiles = []
    for chip in all_chips:
        state = " used" if chip == checked else " gone" if chip not in chips_left else ""
        label = html.escape(CHIP_LABELS.get(chip, chip[:2].upper()))
        tiles.append(f'<span class="chip-tile{state}" title="{html.escape(chip)}">{label}</span>')
    return f'<div class="chip-grid">{"".join(tiles)}</div>'


def team_card(constructors: list[str], x2: str | None, drivers: list[str], cost: float | None,
              money_lines: list[str], xpts: float | None, cards: dict[str, str]) -> str:
    """Boxed team card: constructors, x2 driver, 2x2 drivers, then cost / bank / xPts boxes."""
    col = lambda ids: "".join(cards[a] for a in ids if a in cards)
    money = "".join(f'<div class="tbox">{html.escape(x)}</div>' for x in money_lines)
    return (f'<div class="tcard"><div class="tcol">{col(constructors)}</div>'
            f'<div class="tcol x2col">{col([x2] if x2 else [])}{'<span class="x2-tag">x2</span>' if x2 else ''}</div><div class="asset-grid">{col(drivers)}</div>'
            f'<div class="tstat"><div class="tbox">$ {_number(cost)}</div>{money}'
            f'<div class="tbox big">{_number(xpts)} xPts</div></div></div>')


def team_row(label: str, constructors: list[str], x2: str | None, drivers: list[str],
             cost: float | None, money_lines: list[str], xpts: float | None,
             cards: dict[str, str], chips_html: str = "") -> str:
    constructor_html = "".join(cards[a] for a in constructors if a in cards)
    x2_html = cards.get(x2, "") if x2 else ""
    driver_html = "".join(cards[a] for a in drivers if a in cards)
    chips_column = chips_html  # chip_badges already wraps in div.chips
    return (f'<div class="row"><div class="row-label">{html.escape(label)}</div>'
            f'<div class="asset-group">{constructor_html}</div><div class="asset-group">{x2_html}</div>'
            f'<div class="asset-grid">{driver_html}</div>'
            f'<div class="row-money">{_number(cost)}<br>{"<br>".join(html.escape(x) for x in money_lines)}</div>'
            f'<div class="row-xpts">{_number(xpts)}</div>{chips_column}</div>')


def swap_strip(out: list[str], in_: list[str]) -> str:
    if not out and not in_:
        body = "No transfers"
    else:
        body = f'OUT {html.escape(", ".join(out))} → IN {html.escape(", ".join(in_))}'
    return f'<div class="swap-strip">{body}</div>'


def header_row(label: str = "Team", chips: bool = True) -> str:
    """Column titles aligned with team_row."""
    cells = [label, "CR", "x2", "DR", "$", "xPts", *(["Chips"] if chips else [])]
    return '<div class="row head">' + "".join(f"<div>{html.escape(c)}</div>" for c in cells) + "</div>"
