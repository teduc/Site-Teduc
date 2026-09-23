#!/usr/bin/env python3
"""Gera o pacote estatico do site Teduc (pasta teduc-deploy) a partir do
arquivo-fonte do artifact (/home/claude/teduc-site/index.html).

- troca os assets do artifact (/_blob/...) por arquivos locais
- substitui o resolvedor de logo por referencias diretas ao lockup oficial
- adiciona o <head> completo (charset, viewport, favicons, Open Graph)
- separa CSS e JS em arquivos, quebrando-os em partes menores
- extrai o dicionario de idiomas (chaves + valores EN/ES) para arquivos proprios
- minifica HTML, CSS e JS
"""
import hashlib, json, os, re, shutil, subprocess, sys

SRC   = '/home/claude/teduc-site/index.html'
OUT   = '/home/claude/teduc-deploy'
MEDIA = '/home/claude/teduc-media'          # imagens ja otimizadas
BIN   = '/tmp/claude-0/-home-claude/d9622a65-cc65-5842-bbf2-35a56561122f/scratchpad/min/node_modules/.bin'
MAXCHUNK = 36000                            # tamanho alvo por arquivo (bytes)

BLOB = {
 'fe235c9ff9b2299653c77055b2ac9f40': 'assets/clientes/conexia.png',
 '5aea8da8d7fbcc0a187f5a449e45b866': 'assets/clientes/cogna.png',
 '132ed49ce741923071e2beb2fde9d03a': 'assets/clientes/pearson.png',
 '4cc6ada744824aefb754628715995fcc': 'assets/clientes/seb.png',
 'bd0fa6df5bc78da00d65b19b3480d61c': 'assets/clientes/senna.png',
 'b7283f850d229792813e4b0cc93e3663': 'assets/clientes/itaipu.png',
 '55ec0a82b3415f54f9ede1aa76e85537': 'assets/clientes/cpqd.png',
 '03b711fb890e4fe3a9c309e22103a6f7': 'assets/cintia.jpg',
 'da114224e260d46cad0c2f192c7b98cc': 'assets/og/teduc-og-pt.png',
}

HEAD = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#FAF8F5">
<link rel="icon" href="assets/logo/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="assets/logo/teduc-simbolo-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="assets/logo/teduc-simbolo-16.png">
<link rel="apple-touch-icon" href="assets/logo/teduc-simbolo-180.png">
<link rel="manifest" href="site.webmanifest">
'''

LOGO_JS = """(function(){
var SRC={g:'assets/logo/teduc-horizontal-grafite.png',w:'assets/logo/teduc-horizontal-branco.png'};
[].slice.call(d.querySelectorAll('img[data-logo]')).forEach(function(im){
  im.src=SRC[im.getAttribute('data-logo')==='w'?'w':'g'];
  im.removeAttribute('width');im.removeAttribute('height');
});
})();
"""


def split_array_elems(txt):
    """Divide os elementos de topo de um literal de array JS (sem o [ ]),
    respeitando strings, regex simples e aninhamento."""
    elems, depth, i, start = [], 0, 0, 0
    quote = None
    while i < len(txt):
        c = txt[i]
        if quote:
            if c == '\\':
                i += 2; continue
            if c == quote:
                quote = None
        elif c in '"\'`':
            quote = c
        elif c in '[{(':
            depth += 1
        elif c in ']})':
            depth -= 1
        elif c == ',' and depth == 0:
            elems.append(txt[start:i]); start = i + 1
        i += 1
    tail = txt[start:]
    if tail.strip():
        elems.append(tail)
    return elems


def sh(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    if r.returncode:
        sys.exit('FALHOU: %s\n%s' % (' '.join(a), r.stderr[:500]))
    return r.stdout


def split_top_level(src, limit):
    """Divide um bloco de statements de topo (indentados com 2 espacos)."""
    pts = [m.start() for m in re.finditer(r'(?m)^  (?=[A-Za-z_$(/])', src)]
    out, start = [], 0
    while start < len(src):
        cand = [p for p in pts if start < p <= start + limit]
        end = cand[-1] if cand else len(src)
        if len(src) - end < limit // 4:
            end = len(src)
        out.append(src[start:end]); start = end
    return out


def main():
    s = open(SRC, encoding='utf-8').read()

    for k, v in BLOB.items():
        if ('/_blob/' + k) not in s:
            sys.exit('asset do artifact nao encontrado: ' + k)
        s = s.replace('/_blob/' + k, v)

    i = s.index('  /* Logo oficial Teduc')
    j = s.index('  /* ---------- Páginas internas', i)
    s = s[:i] + LOGO_JS + '\n\n' + s[j:]
    if '/_blob/' in s:
        sys.exit('ainda ha referencias /_blob/ no HTML')

    # pastas
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    for p in ('assets/css', 'assets/js', 'assets/clientes', 'assets/logo'):
        os.makedirs(os.path.join(OUT, p), exist_ok=True)
    for f in os.listdir(MEDIA + '/clientes'):
        shutil.copy2(MEDIA + '/clientes/' + f, OUT + '/assets/clientes/' + f)
    for f in os.listdir(MEDIA + '/logo'):
        shutil.copy2(MEDIA + '/logo/' + f, OUT + '/assets/logo/' + f)
    shutil.copy2(MEDIA + '/cintia.jpg', OUT + '/assets/cintia.jpg')
    os.makedirs(OUT + '/assets/og', exist_ok=True)
    for f in os.listdir(MEDIA + '/og'):
        shutil.copy2(MEDIA + '/og/' + f, OUT + '/assets/og/' + f)
    for f in ('site.webmanifest', 'vercel.json'):
        shutil.copy2(MEDIA + '/' + f, OUT + '/' + f)

    # CSS
    a = s.index('<style>'); b = s.index('</style>') + len('</style>')
    css = s[a + len('<style>'):b - len('</style>')].strip() + '\n'
    s = s[:a] + '@@CSS@@' + s[b:]

    # JS
    a = s.index('<script>') + len('<script>'); b = s.rindex('</script>')
    js = s[a:b].strip()
    s = s[:a - len('<script>')] + '@@JS@@' + s[b + len('</script>'):]
    if not (js.startswith('(function(){') and js.endswith('})();')):
        sys.exit('script principal nao esta no formato esperado')
    inner = js[len('(function(){'):-len('})();')]

    # dicionario de idiomas
    m = re.search(r'(?m)^ *var I18N=', inner)
    if not m:
        sys.exit('bloco var I18N= nao encontrado')
    k0 = m.start()
    k1 = inner.index("I18N.en['Sobre']", k0)
    k1 = inner.rindex('\n', k0, k1)
    lit = inner[m.end():k1].strip().rstrip(';')
    open('/tmp/_lit.js', 'w', encoding='utf-8').write('module.exports=' + lit + ';')
    dic = json.loads(sh('node', '-e',
        "process.stdout.write(JSON.stringify(require('/tmp/_lit.js')))"))
    # idiomas traduzidos: um arquivo de valores por idioma, indexado pelas chaves
    LANGS_T = [k for k in dic if k not in ('pt',)]
    inner = (inner[:k0]
             + '  ' + ' '.join("I18N.%s=I18N.%s||{};" % (l, l) for l in LANGS_T)
             + inner[k1:])

    keys = list(dic['en'].keys())
    extra = {k: v for k, v in dic.items() if k not in LANGS_T}
    data = {'i18n-keys.js': 'var I18N_K=' + json.dumps(keys, ensure_ascii=False) + ';\n'}
    for l in LANGS_T:
        data['i18n-%s.js' % l] = ('var I18N_%s=' % l.upper()
                                  + json.dumps([dic[l].get(k, dic['en'][k]) for k in keys],
                                               ensure_ascii=False) + ';\n')
    data['i18n-build.js'] = (
        'var I18N=Object.assign({' + ','.join('%s:{}' % l for l in LANGS_T) + '},'
        + json.dumps(extra, ensure_ascii=False) + ');\n'
        '(function(){for(var i=0;i<I18N_K.length;i++){'
        + ''.join('I18N.%s[I18N_K[i]]=I18N_%s[i];' % (l, l.upper()) for l in LANGS_T)
        + '}\n'
        + 'I18N_K=' + '='.join('I18N_%s' % l.upper() for l in LANGS_T) + '=null;})();\n')

    # PAGES: array grande de dados -> arquivos separados
    pm = re.search(r'(?m)^ *var PAGES *= *\[', inner)
    pages_files = []
    if pm:
        depth, i2, quote = 1, pm.end(), None
        while i2 < len(inner) and depth:
            c = inner[i2]
            if quote:
                if c == '\\':
                    i2 += 2; continue
                if c == quote:
                    quote = None
            elif c in '"\'`':
                quote = c
            elif c in '[{(':
                depth += 1
            elif c in ']})':
                depth -= 1
            i2 += 1
        body = inner[pm.end():i2 - 1]
        rest = inner[i2:]
        if rest.startswith(';'):
            rest = rest[1:]
        elems = split_array_elems(body)
        groups, cur, size = [], [], 0
        for e in elems:
            if cur and size + len(e.encode()) > MAXCHUNK:
                groups.append(cur); cur, size = [], 0
            cur.append(e); size += len(e.encode())
        if cur:
            groups.append(cur)
        pages_files = groups
        inner = inner[:pm.start()] + rest

    # ordem: nucleo de idiomas antes do resto (route() usa LANG/tr/translate)
    mark = inner.index('  /* ---------- Idiomas:')
    partA, partB = inner[:mark], inner[mark:]
    cut = partB.index('  function applyLang(lang){')
    core, tail = partB[:cut], partB[cut:]

    files = []
    def add(name, content):
        path = os.path.join(OUT, 'assets/js', name)
        open(path, 'w', encoding='utf-8').write(content)
        files.append('assets/js/' + name)

    for n in ['i18n-keys.js'] + ['i18n-%s.js' % l for l in LANGS_T]:
        chunks = [data[n]] if len(data[n].encode()) <= MAXCHUNK else None
        if chunks is None:
            arr = json.loads(data[n][data[n].index('=') + 1:].rstrip(';\n'))
            var = data[n][4:data[n].index('=')]
            half = (len(arr) + 1) // 2
            add(n.replace('.js', '-1.js'), 'var %s=%s;\n' % (var, json.dumps(arr[:half], ensure_ascii=False)))
            add(n.replace('.js', '-2.js'), '%s=%s.concat(%s);\n' % (var, var, json.dumps(arr[half:], ensure_ascii=False)))
        else:
            add(n, data[n])
    add('i18n-build.js', data['i18n-build.js'])
    add('i18n-core.js', 'var d=document, root=d.documentElement;\n' + core.strip() + '\n')
    for n, g in enumerate(pages_files, 1):
        head = 'var PAGES=[];\n' if n == 1 else ''
        add('pages-%d.js' % n, head + 'PAGES.push(' + ','.join(g).strip() + ');\n')
    for n, c in enumerate(split_top_level(partA, MAXCHUNK), 1):
        add('app-%d.js' % n, c.strip('\n') + '\n')
    add('app-last.js', tail.strip('\n') + '\n')

    for f in files:
        sh('node', '--check', os.path.join(OUT, f))

    open(os.path.join(OUT, 'assets/css/site.css'), 'w', encoding='utf-8').write(css)
    s = s.replace('@@CSS@@', '<link rel="stylesheet" href="assets/css/site.css">')
    s = s.replace('@@JS@@', '\n'.join('<script src="%s"></script>' % f for f in files))
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(HEAD + s + '\n</body>\n</html>\n')

    # minificacao
    for f in files:
        p = os.path.join(OUT, f)
        sh(BIN + '/terser', p, '-c', '-m', '--comments', 'false', '-o', p + '.min')
        os.replace(p + '.min', p)
    p = os.path.join(OUT, 'assets/css/site.css')
    sh(BIN + '/cleancss', '-O2', '-o', p, p)
    p = os.path.join(OUT, 'index.html')
    sh(BIN + '/html-minifier-terser', '--collapse-whitespace', '--conservative-collapse',
       '--remove-comments', '-o', p + '.min', p)
    os.replace(p + '.min', p)

    # manifesto
    man = []
    for root_, _dirs, fs in os.walk(OUT):
        for f in sorted(fs):
            path = os.path.join(root_, f)
            rel = os.path.relpath(path, OUT)
            data_ = open(path, 'rb').read()
            man.append({'file': rel, 'sha': hashlib.sha1(data_).hexdigest(), 'size': len(data_)})
    man.sort(key=lambda x: x['size'])
    json.dump(man, open('/home/claude/deploy-manifest.json', 'w'), indent=1, ensure_ascii=False)
    for e in man:
        print('%7d  %s  %s' % (e['size'], e['sha'], e['file']))
    print('TOTAL %d bytes em %d arquivos' % (sum(e['size'] for e in man), len(man)))


if __name__ == '__main__':
    main()
