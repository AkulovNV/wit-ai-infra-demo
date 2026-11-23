"""Сквозная схема сервиса во всех состояниях. Один набор координат на все шаги,
новые элементы шага выделены цветом. python diagrams/gen.py -> diagrams/*.svg"""
import os
from xml.sax.saxutils import escape

W, H = 1280, 720
FONT = "Inter, Arial, sans-serif"
INK, MUTED = "#270E0B", "#736664"
NEW, BAD, OLDA = "#008660", "#CD4A39", "#9D9392"
STY = {
    "old": ("#F9F8F1", "#B9B1B0", INK),
    "new": ("#E5F3EF", NEW, INK),
    "bad": ("#FAEDEB", BAD, "#9A1706"),
}

# id: (x, y, w, h, title, subtitle)
BOX = {
    "client":   (40, 300, 140, 70, "Клиент", "обращение"),
    "app":      (220, 300, 150, 70, "Приложение", "поддержки"),
    "guard":    (220, 410, 150, 54, "Guardrail", "проверяет вход"),
    "human":    (220, 560, 150, 60, "Подтверждение", "человеком"),
    "agent":    (470, 300, 200, 80, "Агент", "agent loop + инструменты"),
    "envkey":   (470, 410, 200, 44, "API-ключ в .env", "права разработчика"),
    "gw":       (790, 150, 170, 60, "LLM gateway", "ключи · лимиты · логи"),
    "extapi":   (1040, 110, 200, 56, "Внешний API модели", ""),
    "own":      (1040, 190, 200, 70, "Свой endpoint", "vLLM на GPU · SkyPilot"),
    "mcp":      (790, 310, 170, 60, "MCP / tool-сервер", "authz на инструмент"),
    "tickets":  (1040, 290, 200, 44, "Тикеты", ""),
    "kb":       (1040, 346, 200, 44, "База знаний", ""),
    "egress":   (790, 470, 170, 60, "Egress proxy", "allowlist"),
    "web":      (1040, 450, 200, 54, "Интернет", ""),
    "attacker": (1040, 524, 200, 50, "Сервер атакующего", ""),
    "identity": (420, 560, 140, 60, "Identity", "токен на сессию"),
    "obs":      (580, 560, 140, 60, "Observability", "трейсы · audit log"),
}
# слои из блока 3: номер и точное название (должно совпадать со слайдами блоков 3 и 4)
LAYERS = {
    "container": (1, "изоляция исполнения"), "mcp": (2, "инструменты и MCP"),
    "identity": (3, "identity и креды"), "egress": (4, "сеть"), "gw": (4, "сеть"),
    "obs": (5, "состояние и наблюдаемость"),
}


def t(x, y, s, size=14, weight=400, color=INK, anchor="middle"):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}" text-anchor="{anchor}">{escape(s)}</text>')


def box(bid, style, title=None, sub=None, badges=False):
    x, y, w, h, tt, st = BOX[bid]
    fill, stroke, ink = STY[style]
    tt, st = title or tt, sub if sub is not None else st
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="{2.5 if style != "old" else 1.5}"/>']
    cy = y + h / 2 + (-4 if st else 5)
    out.append(t(x + w / 2, cy, tt, 16, 600, ink))
    if st:
        out.append(t(x + w / 2, cy + 19, st, 12.5, 400, MUTED if style == "old" else ink))
    if badges and bid in LAYERS:
        out.append(badge(x + w, y, LAYERS[bid][0]))
    return "".join(out)


def badge(cx, cy, n):
    return (f'<circle cx="{cx}" cy="{cy}" r="13" fill="{INK}"/>' + t(cx, cy + 5, str(n), 14, 700, "#fff"))


def container(label, style, badges=False):
    fill, stroke, ink = STY[style]
    out = (f'<rect x="420" y="200" width="300" height="300" rx="16" fill="none" stroke="{stroke}" '
           f'stroke-width="2" stroke-dasharray="7 5"/>' + t(440, 228, label, 15, 600, ink, "start"))
    if badges:
        out += badge(714, 206, 1)
    return out


def arrow(p, q, style="old", label=None, dashed=False, lx=None, ly=None, cut=False):
    color = {"old": OLDA, "new": NEW, "bad": BAD}[style]
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    out = (f'<line x1="{p[0]}" y1="{p[1]}" x2="{q[0]}" y2="{q[1]}" stroke="{color}" stroke-width="2.2"{dash} '
           f'marker-end="url(#a-{style})"/>')
    if label:
        mx, my = lx if lx is not None else (p[0] + q[0]) / 2, ly if ly is not None else (p[1] + q[1]) / 2 - 8
        out += (f'<rect x="{mx - len(label) * 3.6 - 6}" y="{my - 14}" width="{len(label) * 7.2 + 12}" height="20" '
                f'rx="4" fill="#FFFFFF" opacity="0.92"/>' + t(mx, my, label, 12.5, 500, color))
    if cut:
        out += block(q[0] - 14, q[1])
    return out


def block(cx, cy):
    return (f'<circle cx="{cx}" cy="{cy}" r="13" fill="{BAD}"/>'
            f'<path d="M{cx-5} {cy-5} L{cx+5} {cy+5} M{cx+5} {cy-5} L{cx-5} {cy+5}" stroke="#fff" stroke-width="2.6" stroke-linecap="round"/>')


def note(y, s, color=MUTED):
    return t(40, y, s, 14, 400, color, "start")


BARE = False
def svg(step, title, body, notes=()):
    if BARE:
        defs = "".join(f'<marker id="m{step}-{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                       f'<path d="M0 0 L10 5 L0 10 z" fill="{c}"/></marker>' for k, c in {"old": OLDA, "new": NEW, "bad": BAD}.items())
        body = body.replace('url(#a-', f'url(#m{step}-')
        return (f'<svg class="diagram" viewBox="28 96 1228 534" xmlns="http://www.w3.org/2000/svg" aria-label="{escape(title)}">'
                f'<defs>{defs}</defs>{body}</svg>')
    defs = "".join(f'<marker id="a-{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                   f'<path d="M0 0 L10 5 L0 10 z" fill="{c}"/></marker>'
                   for k, c in {"old": OLDA, "new": NEW, "bad": BAD}.items())
    nav = "".join(
        f'<rect x="{900 + i * 68}" y="34" width="60" height="8" rx="4" fill="{NEW if i + 1 == int(step[0]) else "#DDDBD1"}"/>'
        for i in range(5))
    head = t(40, 50, f"Шаг {step}", 15, 600, NEW, "start") + t(40, 84, title, 26, 700, INK, "start")
    foot = "".join(note(668 + i * 22, n) for i, n in enumerate(notes))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<defs>{defs}</defs><rect width="{W}" height="{H}" fill="#FFFFFF"/>{nav}{head}{body}{foot}</svg>')


A = {  # точки привязки стрелок
    "agent_m": (670, 318), "agent_t": (670, 340), "agent_w": (670, 362),
}

# ---------- шаг 1 ----------
def s1():
    b = [container("Ноутбук разработчика", "old"),
         box("client", "old"), box("agent", "old"), box("envkey", "bad"),
         box("extapi", "old"), box("tickets", "old"), box("kb", "old"), box("web", "old"),
         arrow((180, 335), (468, 335)),
         arrow(A["agent_m"], (1038, 140)),
         arrow(A["agent_t"], (1038, 312)), arrow(A["agent_t"], (1038, 366)),
         arrow(A["agent_w"], (1038, 476))]
    return svg("1", "Прототип: всё работает, пока вход доверенный", "".join(b),
               ["Неявные допущения: один пользователь, доверенный вход, креды разработчика, открытая сеть, логов нет."])


# ---------- шаг 2 ----------
def s2_body(style_own="new", direct=True):
    return ([arrow((180, 335), (468, 335))] if direct else []) + [container("Ноутбук разработчика", "old"),
            box("client", "old"), box("agent", "old"), box("envkey", "bad"),
            box("extapi", "old"), box("own", style_own), box("tickets", "old"), box("kb", "old"),
            arrow(A["agent_m"], (1038, 140)),
            arrow(A["agent_m"], (1038, 225), style_own, "OpenAI-совместимый API", lx=880, ly=262),
            arrow(A["agent_t"], (1038, 312)), arrow(A["agent_t"], (1038, 366))]


def s2():
    b = s2_body() + [box("web", "old"), arrow(A["agent_w"], (1038, 476))]
    return svg("2", "Своя модель: описываем нагрузку, а не место её исполнения", "".join(b),
               ["Контракт агента с моделью не меняется: за OpenAI-совместимым API может стоять внешний провайдер или свой vLLM."])


# ---------- шаг 3 ----------
def harness(new=True, badges=True):
    st = "new" if new else "old"
    return [container("Harness · sandbox на сессию", st, badges),
            box("client", "old"), box("app", st), box("agent", "old"),
            box("gw", st, badges=badges), box("extapi", "old"), box("own", "old"),
            box("mcp", st, badges=badges), box("tickets", "old"), box("kb", "old"),
            box("egress", st, badges=badges),
            box("identity", st, badges=badges), box("obs", st, badges=badges),
            arrow((180, 335), (218, 335)), arrow((370, 335), (468, 335)),
            arrow(A["agent_m"], (788, 182), st), arrow((960, 170), (1038, 140)), arrow((960, 192), (1038, 222)),
            arrow(A["agent_t"], (788, 340), st), arrow((960, 330), (1038, 312)), arrow((960, 352), (1038, 366)),
            arrow(A["agent_w"], (788, 496), st),
            arrow((490, 558), (510, 384), st, "токен", dashed=True, lx=470, ly=530),
            arrow((620, 384), (650, 558), st, dashed=True)]


def s3():
    b = harness() + [box("web", "old"), arrow((960, 494), (1038, 478))]
    if BARE: return svg("3", "Harness: платформа для исполнения недоверенного кода", "".join(b))
    legend = "".join(t(40 + i * 245, 646, f"{n}  {name}", 13.5, 500, INK, "start") for i, (n, name) in enumerate(
        [(1, "изоляция исполнения"), (2, "инструменты и MCP"), (3, "identity и креды"), (4, "сеть"), (5, "состояние и наблюдаемость")]))
    return svg("3", "Harness: платформа для исполнения недоверенного кода", "".join(b) + legend)


# ---------- шаг 4a: атака на naive ----------
def s4a():
    b = s2_body("old", direct=False) + [
        box("guard", "new", sub="SAFE: вход чистый"),
        box("web", "bad", "Страница партнёра", "скрытая инструкция"), box("attacker", "bad"),
        arrow((150, 372), (236, 408), "new"), arrow((370, 425), (468, 372), "new"),
        arrow((1038, 470), (672, 356), "bad", "инъекция в результате http_fetch", lx=850, ly=398),
        arrow((672, 344), (1038, 304), "bad", "get_ticket T-1001…1003", lx=850, ly=300),
        arrow((672, 372), (1038, 548), "bad", "выжимка чужих данных", lx=850, ly=488)]
    return svg("4", "Инцидент: guardrail пропустил, данные ушли", "".join(b),
               ["Guardrail проверил сообщение клиента. Инъекция пришла из результата инструмента, его он не видел."])


# ---------- шаг 4b: та же атака на harness ----------
def s4b():
    b = harness(new=False) + [
        box("guard", "old", sub="SAFE: вход чистый"), arrow((295, 372), (295, 408), dashed=True),
        box("web", "bad", "Страница партнёра", "скрытая инструкция"), box("attacker", "bad"),
        arrow((1038, 470), (962, 486), "bad"),
        arrow((788, 480), (672, 374), "bad", "инъекция (хост в allowlist)", lx=690, ly=452),
        arrow((672, 354), (788, 354), "bad", "чужой тикет", lx=728, ly=378, cut=True),
        arrow((962, 512), (1038, 548), "bad", cut=True),
        t(875, 392, "403 not owner → ALERT", 13.5, 600, BAD),
        t(1140, 596, "TCP_DENIED/403 на egress", 13.5, 600, BAD)]
    return svg("4", "Та же атака на harness: модель обманута, вред не случился", "".join(b),
               ["Модель по-прежнему выполняет инструкцию. Останавливает её инфраструктура, попытка видна в audit log."])


# ---------- шаг 5 ----------
def s5():
    b = harness(new=False) + [
        box("guard", "old"), arrow((295, 372), (295, 408), dashed=True),
        box("human", "new"), arrow((480, 382), (372, 562), "new", "необратимые действия", dashed=True, lx=395, ly=510),
        box("web", "old"), arrow((960, 494), (1038, 478))]
    return svg("5", "Итоговая архитектура: безопасность обеспечивает инфраструктура вокруг модели", "".join(b),
               ["Guardrail остаётся сигналом обнаружения. Необратимые действия идут через подтверждение человеком."])


if __name__ == "__main__":
    import sys
    BARE = "--bare" in sys.argv
    out = sys.argv[-1] if BARE else os.path.dirname(os.path.abspath(__file__))
    for name, fn in [("step1-laptop", s1), ("step2-gpu", s2), ("step3-harness", s3),
                     ("step4a-incident-naive", s4a), ("step4b-incident-harness", s4b), ("step5-final", s5)]:
        open(os.path.join(out, f"{name}.svg"), "w", encoding="utf-8").write(fn())
        print(name)
