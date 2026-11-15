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
