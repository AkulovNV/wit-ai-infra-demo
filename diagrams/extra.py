"""Доп. иллюстрации для слайдов: цикл агента и lethal trifecta."""
import sys
from gen import t, INK, MUTED, NEW, BAD

def defs(c):
    return f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="{c}"/></marker></defs>'

def loop():
    W, H = 1400, 640
    b = [defs(INK)]
    def bx(x, y, w, h, title, sub, fill="#F9F8F1", stroke="#B9B1B0"):
        b.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="{fill}" stroke="{stroke}" stroke-width="2.5"/>')
        b.append(t(x + w/2, y + h/2 - 4, title, 34, 700, INK)); b.append(t(x + w/2, y + h/2 + 32, sub, 22, 400, MUTED))
    bx(80, 230, 360, 170, "Модель", "решает, что делать дальше", "#E5F3EF", NEW)
    bx(960, 230, 360, 170, "Инструменты", "get_ticket · search_kb · …")
    p = lambda d, c=INK: b.append(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="3" marker-end="url(#ah)"/>')
    p("M300 226 C 420 100, 980 100, 1100 222")
    p("M1100 404 C 980 540, 420 540, 300 408")
    b.append(t(700, 50, "tool call", 30, 700, NEW)); b.append(t(700, 84, "get_ticket(\"T-1041\")", 22, 400, MUTED))
    b.append(t(700, 580, "результат", 30, 700, INK)); b.append(t(700, 614, "JSON тикета → обратно в контекст", 22, 400, MUTED))
    b.append(t(700, 322, "agent loop", 40, 800, INK)); b.append(t(700, 358, "пока есть tool call", 22, 400, MUTED))
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{"".join(b)}</svg>'

def trifecta():
    W, H = 1000, 920
    c = [(500, 350, "#CD4A39", "Приватные данные", "тикеты всех клиентов", 500, 56),
         (360, 580, "#9A1706", "Недоверенный контент", "страница по ссылке", 290, 862),
         (640, 580, "#402E2C", "Канал наружу", "http_fetch в интернет", 720, 862)]
    b = []
    for x, y, col, *_ in c:
        b.append(f'<circle cx="{x}" cy="{y}" r="230" fill="{col}" fill-opacity="0.13" stroke="{col}" stroke-width="3"/>')
    for x, y, col, title, sub, lx, ly in c:
        b.append(t(lx, ly, title, 32, 700, INK)); b.append(t(lx, ly + 36, sub, 22, 400, MUTED))
    b.append(f'<circle cx="500" cy="500" r="58" fill="#CD4A39"/>')
    b.append(t(500, 508, "утечка", 26, 700, "#FFFFFF"))
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{"".join(b)}</svg>'

if __name__ == "__main__":
    out = sys.argv[1]
    open(f"{out}/agent-loop.svg", "w").write(loop())
    open(f"{out}/trifecta.svg", "w").write(trifecta())
