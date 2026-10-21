"""Build the static docs site (GitHub Pages) from the board profiles: site/index.html + site/boards/<id>.html

  python tools/build_docs.py            # writes ./site
"""

import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "ws-esp32" / "scripts"))

from wslib.data import load_boards, load_chips  # noqa: E402
from wslib.display import display_support  # noqa: E402
from wslib.scaffold import render_header  # noqa: E402

REPO = "https://github.com/mlger/ws-esp32"
CSS = """
:root{--bg:#fff;--fg:#1b1f24;--muted:#57606a;--line:#d0d7de;--card:#f6f8fa;--accent:#0969da;
--ok:#1a7f37;--warn:#9a6700;--bad:#cf222e}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--muted:#8d96a0;--line:#30363d;
--card:#161b22;--accent:#4493f8;--ok:#3fb950;--warn:#d29922;--bad:#f85149}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:960px;margin:0 auto;padding:24px 16px 64px}a{color:var(--accent)}
h1{font-size:1.8rem;margin:.2em 0}h2{margin-top:2em;border-bottom:1px solid var(--line);padding-bottom:.3em}
.muted{color:var(--muted)}table{border-collapse:collapse;width:100%;margin:12px 0;font-size:.95rem}
th,td{border:1px solid var(--line);padding:6px 10px;text-align:left;vertical-align:top}th{background:var(--card)}
.wrap{overflow-x:auto}code,pre{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:.9em}
pre{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:12px;overflow-x:auto}
.badge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.8rem;border:1px solid currentColor}
.s-hardware-tested{color:var(--ok)}.s-schematic{color:var(--ok)}.s-wiki{color:var(--accent)}.s-partial{color:var(--warn)}
.warn{border-left:4px solid var(--warn);background:var(--card);padding:8px 12px;margin:8px 0;border-radius:4px}
"""


def page(title: str, body: str, depth: int = 0) -> str:
    up = "../" * depth
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body><main>"
            f"<p class=muted><a href='{up}index.html'>ws-esp32 boards</a> · <a href='{REPO}'>GitHub</a></p>"
            f"{body}</main></body></html>\n")


def badge(status: str) -> str:
    return f"<span class='badge s-{status}'>{status}</span>"


def pin_text(v) -> str:
    if v is None:
        return "<span class=muted>unknown</span>"
    return html.escape(str(v) if isinstance(v, str) else f"GPIO{v}")


def board_page(b, chip) -> str:
    e = html.escape
    v = b["verification"]
    usb = b["usb"]
    ok, why = display_support(b)
    rows = []
    for p in b["peripherals"]:
        pins = ", ".join(f"<code>{e(k)}</code>={pin_text(x)}" for k, x in (p.get("pins") or {}).items())
        extra = " ".join(x for x in [e(p.get("part", "")), f"@{e(p['addr'])}" if p.get("addr") else "",
                                     f"on {e(p['bus'])}" if p.get("bus") else ""] if x)
        note = f"<br><span class=muted>{e(p['notes'])}</span>" if p.get("notes") else ""
        rows.append(f"<tr><td><code>{e(p['id'])}</code></td><td>{e(p['kind'])}</td><td>{extra}</td>"
                    f"<td>{pins}{note}</td></tr>")
    sources = "".join(f"<li><a href='{e(s)}'>{e(s)}</a></li>" for s in v["sources"])
    warnings = "".join(f"<div class=warn>{e(w)}</div>" for w in b.get("warnings", []))
    sw = ", ".join(f"{e(k)} {e(x)}" for k, x in (b.get("software") or {}).items() if x) or "not stated"
    usb_kind = " + ".join(x for x in ["native USB" if usb.get("native") else "", usb.get("bridge") or ""] if x)
    cmd = (f"python skills/ws-esp32/scripts/wsesp.py new {b['id']} --framework idf"
           + (" --with display" if ok else "") + " --name app")
    body = f"""
<h1>{e(b['name'])}</h1>
<p>{badge(v['status'])} <span class=muted>checked {e(v.get('checked', '?'))}</span></p>
<div class=wrap><table>
<tr><th>SoC</th><td>{e(b['soc'])} ({e(chip['name'])})</td></tr>
<tr><th>Flash / PSRAM</th><td>{b['flash_mb']} MB / {b['psram_mb']} MB {e(b['psram_mode'])}</td></tr>
<tr><th>USB</th><td>{e(usb_kind)}; console on {e(usb['console'])}</td></tr>
<tr><th>Display code generator</th><td>{'yes: ' if ok else 'no: '}{e(why)}</td></tr>
<tr><th>Tested with</th><td>{sw}</td></tr>
</table></div>
{warnings}
<h2>Onboard peripherals and pins</h2>
<div class=wrap><table><tr><th>ID</th><th>Kind</th><th>Part</th><th>Pins</th></tr>{''.join(rows)}</table></div>
<h2>Start a project</h2><pre>{e(cmd)}</pre>
<h2>board_pins.h</h2><pre>{e(render_header(b))}</pre>
<h2>Sources</h2><ul>{sources}</ul>
<p class=muted>Found a wrong pin? <a href='{REPO}/issues/new?template=bug.yml'>Report it</a>.
Own this board? <a href='{REPO}/issues/new?template=hardware-test.yml'>Send a hardware test report</a>.</p>
"""
    return page(f"{b['name']} pinout - ws-esp32", body, depth=1)


def index_page(boards, chips) -> str:
    e = html.escape
    rows = "".join(
        f"<tr><td><a href='boards/{e(b['id'])}.html'>{e(b['name'])}</a></td><td>{e(chips[b['chip']]['name'])}</td>"
        f"<td>{b['flash_mb']} MB / {b['psram_mb']} MB</td><td>{'yes' if display_support(b)[0] else '-'}</td>"
        f"<td>{badge(b['verification']['status'])}</td></tr>"
        for b in sorted(boards.values(), key=lambda x: x["name"]))
    body = f"""
<h1>ws-esp32 board profiles</h1>
<p>Pinouts and onboard peripherals for Waveshare ESP32 boards, used by the
<a href='{REPO}'>ws-esp32 agent skill</a>. Every pin links back to its source.</p>
<div class=wrap><table><tr><th>Board</th><th>Chip</th><th>Flash / PSRAM</th><th>Display codegen</th><th>Data</th></tr>
{rows}</table></div>
<p class=muted><b>partial</b>: some pins unknown · <b>wiki</b>: from Waveshare docs/demo code ·
<b>schematic</b>: checked against the schematic · <b>hardware-tested</b>: confirmed on a real board</p>
"""
    return page("ws-esp32 board profiles", body)


def main(out: str = "site") -> int:
    chips, boards = load_chips(), load_boards()
    out_dir = ROOT / out
    (out_dir / "boards").mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(index_page(boards, chips), encoding="utf-8")
    for b in boards.values():
        (out_dir / "boards" / f"{b['id']}.html").write_text(board_page(b, chips[b["chip"]]), encoding="utf-8")
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    print(f"wrote {out_dir} ({len(boards)} boards)")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
