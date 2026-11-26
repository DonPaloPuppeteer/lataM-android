# lataM 1.0 - "LÖVE en español": motor para juegos escritos en Latino (.lat)
# lataM [carpeta | juego.lataM | principal.lat]   o suelta un juego sobre la ventana
# lataM --empaquetar carpeta [salida.lataM]       (--py muestra la traduccion a Python)
import sys, os, io, json, zipfile, traceback
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame as pg, latino2py
from latino2py import NS
_AQUI = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
_p = {"v": None, "f": None, "cache": {}, "fonts": {}, "ff": None, "col": (255, 255, 255), "dt": 0,
      "fps": 0, "tope": 60, "sig": None, "ico": False, "mus": None, "off": (0, 0), "conf": {}}

def _rd(p):
    try:
        with open(p, "rb") as f: return f.read()
    except OSError: return None

class _Fuente:  # carpeta, paquete .lataM/.zip o archivo .lat
    def __init__(s, ruta):
        s.ruta = os.path.abspath(ruta); s.z = None; s.pre = ""; s.main = "principal.lat"; s.dir = None
        if os.path.isdir(s.ruta): s.dir = s.ruta
        elif s.ruta.lower().endswith(".lat"): s.dir = os.path.dirname(s.ruta); s.main = os.path.basename(s.ruta)
        else:
            s.z = zipfile.ZipFile(s.ruta)
            n = [x for x in s.z.namelist() if x.endswith("principal.lat")]
            if not n: raise FileNotFoundError("El paquete no tiene principal.lat")
            s.pre = min(n, key=len)[:-len("principal.lat")]
        emb = hasattr(sys, "_MEIPASS") and s.dir and s.dir.startswith(sys._MEIPASS)
        base = os.environ.get("APPDATA") or os.environ.get("ANDROID_PRIVATE") or os.path.expanduser("~/.local/share")
        s.w = s.dir if (s.dir and not emb) else os.path.join(base, "lataM", os.path.splitext(os.path.basename(s.ruta))[0])
    def leer(s, r):  # guardado > paquete > carpeta > recursos del motor
        r = r.replace("\\", "/").lstrip("/"); b = _rd(os.path.join(s.w, r))
        if b is None and s.z:
            try: b = s.z.read(s.pre + r)
            except KeyError: pass
        if b is None and s.dir: b = _rd(os.path.join(s.dir, r))
        return b if b is not None else _rd(os.path.join(_AQUI, r))

def _dat(r):
    b = _p["f"].leer(r)
    if b is None: raise FileNotFoundError("No se encontro el archivo: " + r)
    return b

# ---- ventana
def _icono(r=None):
    if r: pg.display.set_icon(pg.image.load(io.BytesIO(_dat(r)), r)); _p["ico"] = True; return
    for x in ("icono.png", "lataM.png"):
        b = _p["f"].leer(x) if _p["f"] else _rd(os.path.join(_AQUI, x))
        if b: pg.display.set_icon(pg.image.load(io.BytesIO(b), x)); return
def _conf(f):  # conf.lat opcional (como conf.lua de LÖVE)
    t = f.leer("conf.lat")
    if t is None: return {}
    c = dict(latino2py.BASE)
    exec(compile(latino2py.traducir(t.decode("utf-8-sig")), "conf.lat", "exec"), c)
    return {k: c[k] for k in ("ancho", "alto", "titulo", "redim", "fps", "icono") if k in c}
def _crear(ancho=None, alto=None, titulo=None, redim=None):  # sin argumentos usa conf.lat
    k = _p["conf"]
    if not _p["ico"]: _icono(k.get("icono"))
    red = k.get("redim", False) if redim is None else redim
    _p["v"] = pg.display.set_mode((ancho or k.get("ancho", 800), alto or k.get("alto", 600)), pg.RESIZABLE if red else 0)
    pg.display.set_caption(titulo or k.get("titulo", "lataM"))
def _win():
    if not _p["v"]: _crear()
def _tope(n): _p["tope"] = n
ventana = NS(crear=_crear, titulo=lambda t: pg.display.set_caption(t), icono=_icono, fps=_tope,
    tamano=lambda: _p["v"].get_size(), pantalla_completa=lambda: pg.display.toggle_fullscreen())

# ---- graficos
def _imagen(r):
    if r not in _p["cache"]: _win(); _p["cache"][r] = pg.image.load(io.BytesIO(_dat(r)), r).convert_alpha()
    return _p["cache"][r]
def _o(x, y): ox, oy = _p["off"]; return int(x + ox), int(y + oy)  # aplica la camara
def _dib(img, x, y, esc=1, rot=0):
    if isinstance(img, str): img = _imagen(img)
    if esc != 1: img = pg.transform.scale_by(img, esc)
    x, y = _o(x, y)
    if rot:
        img = pg.transform.rotate(img, -rot); _p["v"].blit(img, img.get_rect(center=(x, y)))
    else: _p["v"].blit(img, (x, y))
def _recorte(i, x, y, w, h):  # parte de una imagen (sprite sheet)
    if isinstance(i, str): i = _imagen(i)
    return i.subsurface(pg.Rect(int(x), int(y), int(w), int(h)))
def _trasl(x, y): ox, oy = _p["off"]; _p["off"] = (ox + x, oy + y)

def _fnt(t):
    k = (_p["ff"], t)
    if k not in _p["fonts"]: _p["fonts"][k] = pg.font.Font(io.BytesIO(_dat(_p["ff"])) if _p["ff"] else None, t)
    return _p["fonts"][k]
def _texto(t, x, y, tam=24): _p["v"].blit(_fnt(tam).render(latino2py._t(t), True, _p["col"]), _o(x, y))
def _fuente(r=None): _p["ff"] = r
def _color(r, g, b, a=255): _p["col"] = (r, g, b)
graficos = NS(imagen=_imagen, dibujar=_dib, color=_color, texto=_texto, fuente=_fuente, recorte=_recorte,
    trasladar=_trasl, reiniciar=lambda: _p.update(off=(0, 0)),
    ancho=lambda t, tam=24: _fnt(tam).size(latino2py._t(t))[0],
    alto=lambda t, tam=24: _fnt(tam).size(latino2py._t(t))[1],
    rectangulo=lambda m, x, y, w, h: pg.draw.rect(_p["v"], _p["col"], (*_o(x, y), int(w), int(h)), 0 if m == "lleno" else 2),
    circulo=lambda m, x, y, r: pg.draw.circle(_p["v"], _p["col"], _o(x, y), int(r), 0 if m == "lleno" else 2),
    linea=lambda x1, y1, x2, y2, grosor=2: pg.draw.line(_p["v"], _p["col"], _o(x1, y1), _o(x2, y2), grosor),
    poligono=lambda m, pts: pg.draw.polygon(_p["v"], _p["col"], [_o(*p) for p in pts], 0 if m == "lleno" else 2),
    tamano=lambda i: _imagen(i).get_size() if isinstance(i, str) else i.get_size(),
    limpiar=lambda r=0, g=0, b=0: _p["v"].fill((r, g, b)))

# ---- audio (el mezclador se inicia al usarlo: arranque mas rapido)
def _mix():
    if not pg.mixer.get_init(): pg.mixer.init()
def _musica(r, bucle=True, vol=1.0):
    _mix(); _p["mus"] = io.BytesIO(_dat(r)); pg.mixer.music.load(_p["mus"], os.path.splitext(r)[1][1:])
    pg.mixer.music.set_volume(vol); pg.mixer.music.play(-1 if bucle else 0)
def _snd(r): _mix(); return pg.mixer.Sound(file=io.BytesIO(_dat(r)))
audio = NS(sonido=_snd, reproducir=lambda s, vol=1.0: (s.set_volume(vol), s.play()), musica=_musica,
    parar=lambda: pg.mixer.get_init() and pg.mixer.music.stop(), volumen=lambda v: (_mix(), pg.mixer.music.set_volume(v)))

# ---- teclado / raton / tiempo
_K = {"izquierda": pg.K_LEFT, "derecha": pg.K_RIGHT, "arriba": pg.K_UP, "abajo": pg.K_DOWN,
      "espacio": pg.K_SPACE, "enter": pg.K_RETURN, "escape": pg.K_ESCAPE}
teclado = NS(presionada=lambda n: pg.key.get_pressed()[_K.get(n) or pg.key.key_code(n)])
raton = NS(posicion=lambda: pg.mouse.get_pos(), presionado=lambda b=1: pg.mouse.get_pressed()[b - 1],
    visible=lambda v: pg.mouse.set_visible(bool(v)))
tiempo = NS(delta=lambda: _p["dt"], total=lambda: pg.time.get_ticks() / 1000, fps=lambda: _p["fps"],
    esperar=lambda s: pg.time.wait(int(s * 1000)))

# ---- archivos
def _rw(r):
    w = os.path.normpath(_p["f"].w); p = os.path.normpath(os.path.join(w, r))
    if not p.startswith(w): raise ValueError("Ruta no permitida: " + r)
    os.makedirs(os.path.dirname(p), exist_ok=True); return p
def _escr(r, s):
    with open(_rw(r), "w", encoding="utf8") as f: f.write(s)
def _leer(r):
    b = _p["f"].leer(r); return None if b is None else b.decode("utf-8-sig")
def _listar(d=""):
    f = _p["f"]; d = d.replace("\\", "/").strip("/"); o = set()
    for b in (f.w, f.dir):
        if b and os.path.isdir(os.path.join(b, d)): o.update(os.listdir(os.path.join(b, d)))
    if f.z:
        pre = f.pre + (d + "/" if d else "")
        o.update(n[len(pre):].split("/")[0] for n in f.z.namelist() if n.startswith(pre) and n != pre)
    return sorted(o)
def _borrar(r):
    if os.path.exists(_rw(r)): os.remove(_rw(r))
def _gd(r, t): _escr(r, json.dumps(t, ensure_ascii=False))
def _cd(r, d=None):  # devuelve la tabla guardada, o d si no existe
    s = _leer(r)
    try: return d if s is None else json.loads(s, object_hook=latino2py._D)
    except ValueError: return d
archivos = NS(leer=_leer, escribir=_escr, existe=lambda r: _p["f"].leer(r) is not None, borrar=_borrar, listar=_listar,
    guardar_datos=_gd, cargar_datos=_cd)

# ---- sistema / empaquetar
def _empaquetar(carpeta, salida=None):
    carpeta = os.path.abspath(carpeta)
    if not os.path.exists(os.path.join(carpeta, "principal.lat")): raise FileNotFoundError("Falta principal.lat en " + carpeta)
    salida = salida or os.path.basename(carpeta) + ".lataM"
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for raiz, _, fs in os.walk(carpeta):
            for f in fs:
                if not f.endswith(".lataM"): z.write(os.path.join(raiz, f), os.path.relpath(os.path.join(raiz, f), carpeta))
    return salida
def _cargar(ruta):  # busca: tal cual, junto al juego actual, junto al motor, recursos del motor
    f = _p["f"]; fr = getattr(sys, "frozen", False)
    for b in ("", f.dir or os.path.dirname(f.ruta), os.path.dirname(sys.executable if fr else os.path.abspath(__file__)), _AQUI):
        c = os.path.join(b, ruta)
        if os.path.exists(c): _p["sig"] = c; return
    raise FileNotFoundError("No existe el juego: " + ruta)
def _salir(): pg.quit(); sys.exit()
sistema = NS(salir=_salir, cargar=_cargar, empaquetar=_empaquetar, plataforma=lambda: sys.platform, version="lataM 1.0")
def _col(ax, ay, aw, ah, bx, by, bw, bh): return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah
_col.circulo = lambda x1, y1, r1, x2, y2, r2: (x2 - x1) ** 2 + (y2 - y1) ** 2 <= (r1 + r2) ** 2
_col.punto = lambda px, py, x, y, w, h: x <= px <= x + w and y <= py <= y + h

# ---- motor
def _error(ruta, ex):  # pantalla de error (como la azul de LÖVE)
    traceback.print_exc(); _p["v"] = pg.display.set_mode((640, 480)); pg.display.set_caption("lataM - error")
    m = f"{type(ex).__name__}: {ex}"; t = [m[i:i + 70] for i in range(0, len(m), 70)]; ft = pg.font.Font(None, 24)
    while True:
        for e in pg.event.get():
            if e.type == pg.QUIT or (e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE): return None
            if e.type == pg.DROPFILE: return e.file
            if e.type == pg.KEYDOWN and e.key == pg.K_r: return ruta
        _p["v"].fill((20, 40, 110))
        for i, l in enumerate(["lataM: ocurrio un error", ""] + t + ["", "R = recargar   Esc = salir   o suelta otro juego aqui"]):
            _p["v"].blit(ft.render(l, True, (255, 255, 255)), (20, 20 + i * 24))
        pg.display.flip(); pg.time.wait(30)

def jugar(ruta):  # corre un juego; devuelve el siguiente a cargar (o None para salir)
    _p.update(cache={}, fonts={}, ff=None, sig=None, ico=False, tope=60)
    if pg.mixer.get_init(): pg.mixer.music.stop()
    try:
        f = _p["f"] = _Fuente(ruta); b = f.leer(f.main)
        _p["conf"] = _conf(f); _p["tope"] = _p["conf"].get("fps", 60)
        if b is None: raise FileNotFoundError("No se encontro " + f.main)
        py = latino2py.traducir(b.decode("utf-8-sig"))
        if "--py" in sys.argv: print(py); return None
        g = dict(latino2py.BASE, ventana=ventana, graficos=graficos, audio=audio, teclado=teclado, raton=raton,
                 tiempo=tiempo, archivos=archivos, sistema=sistema, colision=_col)
        def _incl(r):  # incluir("util.lat"): comparte las globales del juego
            t = _leer(r)
            if t is None: raise FileNotFoundError("No se encontro " + r)
            exec(compile(latino2py.traducir(t), r, "exec"), g)
        g["incluir"] = _incl
        exec(compile(py, f.main, "exec"), g)
        _win()
        if "cargar" in g: g["cargar"]()
        reloj = pg.time.Clock()
        while True:
            for e in pg.event.get():
                if e.type == pg.QUIT:
                    if "salir" in g: g["salir"]()
                    return None
                if e.type == pg.DROPFILE:
                    if "soltar" in g: g["soltar"](e.file)
                    else: return e.file
                if e.type == pg.KEYDOWN and "tecla" in g: g["tecla"](pg.key.name(e.key))
                if e.type == pg.KEYUP and "tecla_soltada" in g: g["tecla_soltada"](pg.key.name(e.key))
                if e.type == pg.MOUSEBUTTONDOWN and "clic" in g: g["clic"](*e.pos, e.button)
                if e.type == pg.MOUSEWHEEL and "rueda" in g: g["rueda"](e.y)
            _p["dt"] = reloj.tick(_p["tope"]) / 1000; _p["fps"] = reloj.get_fps()
            if "actualizar" in g: g["actualizar"](_p["dt"])
            _p["off"] = (0, 0); graficos.limpiar()
            if "dibujar" in g: g["dibujar"]()
            pg.display.flip()
            if _p["sig"]: return _p["sig"]
    except SystemExit: raise
    except Exception as ex: return _error(ruta, ex)

ANDROID = bool(os.environ.get("ANDROID_ARGUMENT") or os.environ.get("ANDROID_PRIVATE"))
def _resolver():  # sin argumentos: juego empaquetado > .lataM/carpeta junto al motor > sin_juego (solo PC)
    fr = getattr(sys, "frozen", False)
    d = os.path.dirname(sys.executable if fr else os.path.abspath(__file__))
    extra = [] if ANDROID else [os.path.join(d, "sin_juego"), os.path.join(_AQUI, "sin_juego")]
    for c in ([os.path.join(_AQUI, "juego")] if fr else []) + [os.path.splitext(sys.executable if fr else __file__)[0] + ".lataM",
              os.path.join(d, "juego.lataM"), os.path.join(d, "juego")] + extra:
        if os.path.exists(c): return c

def _lista_lataM():  # .lataM en las carpetas donde el usuario puede copiarlos
    dirs = [_AQUI, "/sdcard/Download", "/storage/emulated/0/Download", "/sdcard/Android/data/org.latino.latam/files",
            os.environ.get("ANDROID_PRIVATE", ""), os.path.expanduser("~/Downloads")]
    out = set()
    for d in dirs:
        try:
            for n in os.listdir(d):
                if n.lower().endswith(".latam"): out.add(os.path.join(d, n))
        except OSError: pass
    return sorted(out)

def _selector():  # sin juego dentro: el usuario elige un .lataM (como abrir un .love en LÖVE)
    _win(); pg.display.set_caption("lataM"); fs = _lista_lataM()
    fnt = pg.font.Font(None, 30); clk = pg.time.Clock()
    while True:
        for e in pg.event.get():
            if e.type == pg.QUIT or (e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE): return None
            if e.type == pg.MOUSEBUTTONDOWN and e.button == 1 and e.pos[1] >= 110:
                i = (e.pos[1] - 110) // 44
                if i < len(fs): return fs[i]
        v = _p["v"]; v.fill((20, 20, 60))
        titulo = "Elige un juego .lataM" if fs else "No hay ningun juego .lataM"
        v.blit(fnt.render(titulo, True, (255, 255, 255)), (20, 30))
        v.blit(fnt.render("Copia un .lataM a la carpeta Download o Android/data/org.latino.latam/files", True, (200, 200, 200)), (20, 66))
        for i, f in enumerate(fs[:10]):
            v.blit(fnt.render(os.path.basename(f), True, (255, 220, 0)), (30, 110 + i * 44))
        pg.display.flip(); clk.tick(30)

def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if "--empaquetar" in sys.argv: print("Creado:", _empaquetar(a[0], a[1] if len(a) > 1 else None)); return
    pg.display.init(); pg.font.init()
    r = a[0] if a else _resolver()
    if r is None: r = _selector()
    while r: r = jugar(r)
    pg.quit()

if __name__ == "__main__": main()
