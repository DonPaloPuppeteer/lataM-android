# latino2py: traduce sintaxis Latino (.lat) a Python. Sin dependencias, ~150 lineas.
import re
_S = re.compile(r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')')

# ---------- runtime minimo de Latino ----------
def _t(a):
    if a is None: return "nulo"
    if a is True: return "cierto"
    if a is False: return "falso"
    if isinstance(a, float) and a == int(a): return str(int(a))
    if isinstance(a, list): return "[" + ", ".join(map(_t, a)) + "]"
    if isinstance(a, dict): return "{" + ", ".join(f"{_t(k)}: {_t(v)}" for k, v in a.items()) + "}"
    return str(a)
class _I:  # operador infijo para ".." (concatenar)
    def __init__(s, f): s.f = f
    def __ror__(s, o): return _I(lambda x: s.f(o, x))
    def __or__(s, o): return s.f(o)
_C = _I(lambda a, b: _t(a) + _t(b))
class _Q(str):  # literal de texto: "Clics: " + 5 funciona como concatenacion
    def __add__(s, o): return _Q(str.__add__(s, _t(o)))
    def __radd__(s, o): return _Q(_t(o) + str.__str__(s))
class NS:
    def __init__(s, **k): s.__dict__.update(k)
class _Obj:  # base de las clases Latino
    def __init__(mi, *a):
        mi._campos(); c = getattr(mi, 'constructor', None)
        if c: c(*a)
    def _campos(mi): pass
    def __str__(mi): return "<" + type(mi).__name__ + ">"
class _D(dict):  # diccionario Latino: d.k y d["k"]
    def __getattr__(s, k):
        if k.startswith('__'): raise AttributeError(k)
        return s.get(k, "")
    def __setattr__(s, k, v): s[k] = v
    def __missing__(s, k): return ""
import math, random
def _ins(l, x, i): l.insert(i, x)
def _elim(l, x):
    if x in l: l.remove(x)
def _idx(l, x): return l.index(x) if x in l else -1
def _ord(l): l.sort(key=lambda v: (isinstance(v, str), v))
def _dividir(s, d=" "): return s.split(d)
def _tipo(a):
    return ("logico" if isinstance(a, bool) else "numero" if isinstance(a, (int, float)) else "cadena" if isinstance(a, str)
            else "lista" if isinstance(a, list) else "diccionario" if isinstance(a, dict) else "nulo" if a is None else "funcion")
def _num(a):
    try: f = float(a); return int(f) if f == int(f) else f
    except (ValueError, TypeError): return None
BASE = dict(_C=_C, _Q=_Q, _D=_D, _Obj=_Obj, NS=NS,
    poner=lambda *a: print(*map(_t, a)), imprimir=lambda *a: print(*map(_t, a)),
    escribir=lambda *a: print(*map(_t, a)), imprimirf=lambda *a: print(*map(_t, a), end=""),
    longitud=len, texto=_t, numero=_num, tipo=_tipo, entero=lambda a: int(float(a)),
    lista=NS(agregar=lambda l, x: l.append(x), longitud=len, insertar=_ins, eliminar=_elim, indice=_idx,
             extender=lambda a, b: a.extend(b), invertir=lambda l: l[::-1], eliminar_indice=lambda l, i: l.pop(i),
             comparar=lambda a, b: a == b, ordenar=_ord, contiene=lambda l, x: x in l, copiar=lambda l: l[:],
             limpiar=lambda l: l.clear(), sumar=sum),
    cadena=NS(longitud=len, mayusculas=lambda s: s.upper(), minusculas=lambda s: s.lower(),
              reemplazar=lambda s, a, b: s.replace(a, b), dividir=_dividir, contiene=lambda s, x: x in s,
              subcadena=lambda s, i, j: s[i:j], recortar=lambda s: s.strip(), empieza=lambda s, x: s.startswith(x),
              termina=lambda s, x: s.endswith(x), invertir=lambda s: s[::-1], repetir=lambda s, n: s * n,
              indice=lambda s, x: s.find(x), unir=lambda l, d="": d.join(map(_t, l))),
    diccionario=NS(longitud=len, claves=lambda d: list(d), valores=lambda d: list(d.values()),
                   contiene=lambda d, k: k in d, eliminar=lambda d, k: d.pop(k, None)),
    mate=NS(piso=math.floor, techo=math.ceil, raiz=math.sqrt, seno=math.sin, coseno=math.cos, tangente=math.tan,
            abs=abs, redondear=round, minimo=min, maximo=max, potencia=pow, log=math.log, PI=math.pi,
            aleatorio=random.random, entero=lambda a, b: random.randint(a, b),
            distancia=lambda x1, y1, x2, y2: math.hypot(x2 - x1, y2 - y1),
            limitar=lambda v, a, b: max(a, min(b, v)),
            lerp=lambda a, b, t: a + (b - a) * t, signo=lambda a: (a > 0) - (a < 0)))

# ---------- traductor ----------
def _sinc(s):  # quita comentarios # // /* */
    o = []; i = 0; n = len(s); q = None
    while i < n:
        c = s[i]
        if q:
            o.append(c)
            if c == '\\' and i + 1 < n: o.append(s[i + 1]); i += 1
            elif c == q: q = None
        elif c in '"\'': q = c; o.append(c)
        elif s.startswith('/*', i):
            j = s.find('*/', i + 2); j = n if j < 0 else j + 2
            o.append('\n' * s.count('\n', i, j)); i = j - 1
        elif c == '#' or s.startswith('//', i):
            while i < n and s[i] != '\n': i += 1
            continue
        else: o.append(c)
        i += 1
    return ''.join(o)

def _lineas(s):  # une literales de varias lineas ([ ] { } ( ))
    out = []; buf = ''; d = 0
    for ln in s.split('\n'):
        t = _S.sub(lambda m: 'S' * len(m.group()), ln)
        d += sum(t.count(c) for c in '([{') - sum(t.count(c) for c in ')]}')
        buf += (' ' + ln.strip()) if buf else ln.strip()
        if d <= 0: out.append(buf); buf = ''; d = 0
    if buf: out.append(buf)
    r = []
    for l in out:  # "si (c) romper fin" en una sola linea
        m = re.match(r'^(si|mientras)\s*(\(.*\))\s*(romper|continuar)\s+fin$', l)
        r += [m.group(1) + ' ' + m.group(2), m.group(3), 'fin'] if m else [l]
    return [l for l in r if l]

def _ex(e):  # Latino -> Python. Los textos se enmascaran para no tocar su contenido.
    lit = []
    t = _S.sub(lambda m: lit.append(m.group()) or '\x01%d\x02' % (len(lit) - 1), e)
    t = re.sub(r'\b(cierto|verdadero)\b', 'True', t)
    t = re.sub(r'\bfalso\b', 'False', t); t = re.sub(r'\bnulo\b', 'None', t)
    t = re.sub(r'\bentonces\b', '', t)
    t = re.sub(r'(?<![\w.])no\b(?!\s*=(?!=))', 'not ', t)
    t = re.sub(r'(?<=[\w)\]\x02])\s+(y|o)\s+(?=[\w(\[!\-\x01])', lambda m: ' and ' if m.group(1) == 'y' else ' or ', t)
    t = t.replace('&&', ' and ').replace('||', ' or ')
    t = re.sub(r'!(?!=)', ' not ', t).replace('..', '|_C|').replace('{', '_D({').replace('}', '})')
    return re.sub(r'\x01(\d+)\x02', lambda m: '_Q(%s)' % lit[int(m.group(1))], t)

def _tern(e):  # c ? a : b
    d = 0; q = None; a = b = -1
    for i, c in enumerate(e):
        if q:
            if c == q: q = None
        elif c in '"\'': q = c
        elif c in '([{': d += 1
        elif c in ')]}': d -= 1
        elif d == 0 and c == '?' and a < 0: a = i
        elif d == 0 and c == ':' and a >= 0: b = i; break
    return f'({e[a+1:b]} if {e[:a]} else {e[b+1:]})' if b > 0 else e

def _st(l):  # sentencia simple
    l = re.sub(r'^global\s+', '', l)
    t = _ex(l)
    t = re.sub(r'^(\S+?)\s*\+\+$', r'\1 += 1', t); t = re.sub(r'^(\S+?)\s*--$', r'\1 -= 1', t)
    m = re.match(r'^([\w.\[\]]+\s*=(?!=)\s*)(.+)$', t)
    return m.group(1) + _tern(m.group(2)) if m else t

def _pasada(src, G):
    out = []; st = []
    lv = lambda: sum(e[2] for e in st)
    def w(s, n=None): out.append('    ' * (lv() if n is None else n) + s)
    for l in _lineas(_sinc(src)):
        k = re.match(r'(\w+)\s*(.*)$', l); kw = k.group(1) if k else ''; r = k.group(2) if k else ''
        kw = {'fun': 'funcion', 'ret': 'retorno', 'retornar': 'retorno'}.get(kw, kw)
        if kw == 'fin':
            e = st.pop()
            if e[0] == 'desde': w('finally:', lv() + 1); w(_st(e[1]), lv() + 2)
            elif e[0] == 'clase':
                i = '    ' * (lv() + 1)
                c = [i + 'def _campos(mi):'] + ([i + '    ' + e[3] + '._campos(mi)'] if e[3] else []) + [i + '    ' + x for x in e[1]]
                if len(c) == 1: c.append(i + '    pass')
                out[e[4]:e[4]] = c
        elif kw == 'si': w(f'if {_ex(r)}:'); st.append(['si', 0, 1])
        elif kw == 'osi': w(f'elif {_ex(r)}:', lv() - 1)
        elif kw == 'sino': w('else:', lv() - 1)
        elif kw == 'mientras': w(f'while {_ex(r)}:'); st.append(['mientras', 0, 1])
        elif kw == 'repetir': w('while True:'); st.append(['rep', 0, 1])
        elif kw == 'hasta': st.pop(); w(f'if {_ex(r)}: break', lv() + 1)
        elif kw == 'desde':
            a = [x.strip() for x in r.strip()[1:-1].split(';')]
            w(_st(a[0])); w(f'while {_ex(a[1])}:'); w('try:', lv() + 1); st.append(['desde', a[2], 2])
            if not st[:-1] or all(e[0] != 'func' for e in st): G.add(re.match(r'\w+', a[0]).group())
        elif kw == 'elegir':
            w(f'_e{lv()} = {_ex(r)}'); st.append(['elegir', True, 1])
        elif kw == 'caso':
            e = st[-1]; w(f"{'if' if e[1] else 'elif'} _e{lv()-1} == {_ex(r.strip().rstrip(':'))}:", lv() - 1); e[1] = False
        elif kw == 'defecto':
            e = st[-1]; w('else:' if not e[1] else 'if True:', lv() - 1); e[1] = False
        elif kw == 'clase':
            m = re.match(r'(\w+)\s*(?:\((.*?)\))?\s*(?:hereda\s+(\w+))?', r)
            b = m.group(3) or (m.group(2) or '').strip() or None
            w(f'class {m.group(1)}({b or "_Obj"}):'); st.append(['clase', [], 1, b, len(out)])
        elif kw == 'funcion':
            m = re.match(r'(\w+)\s*\((.*)\)', r); en = bool(st) and st[-1][0] == 'clase'
            ps = {x.strip() for x in m.group(2).split(',')} | ({'mi'} if en else set())
            a = ', '.join(['mi'] + ([m.group(2)] if m.group(2).strip() else [])) if en else m.group(2)
            w(f'def {m.group(1)}({a}):'); st.append(['func', 0, 1])
            g = sorted(G - ps)
            if g: w('global ' + ', '.join(g))
        elif kw == 'retorno': w('return ' + _tern(_ex(r)) if r else 'return')
        elif kw == 'romper': w('break')
        elif kw == 'continuar': w('continue')
        else:
            if st and st[-1][0] == 'clase':
                m = re.match(r'(\w+)\s*=(?!=)\s*(.+)$', l)
                if m: st[-1][1].append(f'mi.{m.group(1)} = {_tern(_ex(m.group(2)))}')
                continue
            if all(e[0] != 'func' for e in st):
                m = re.match(r'(?:global\s+)?(\w+)\s*(?:=(?!=)|[-+*/]=|\+\+|--)', l)
                if m: G.add(m.group(1))
            w(_st(l))
    return '\n'.join(out) + '\n'

def traducir(src):
    G = set(); _pasada(src, G)  # 1a pasada: detecta variables globales
    return _pasada(src, G)
