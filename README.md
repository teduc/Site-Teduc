# Site Teduc

Site institucional da Teduc — Ecossistema de Educação e Tecnologia.
HTML, CSS e JavaScript sem dependências: nada para instalar, nada para compilar.

## Como publicar

O site é estático. A raiz do repositório já é a pasta a publicar.

- **Vercel / Netlify** — importe o repositório, sem comando de build, com a raiz como
  diretório de saída. O `vercel.json` já define cache dos assets, cabeçalhos de segurança
  e o redirecionamento das rotas internas para o `index.html`.
- **GitHub Pages** — ative Pages na branch `main`, pasta `/ (root)`.
- **Servidor próprio** — copie todos os arquivos para a pasta pública.

Para ver localmente:

    python3 -m http.server 8000

## Estrutura

    index.html              página única, com as rotas internas em #/
    assets/css/site.css     estilos
    assets/js/              scripts, divididos por responsabilidade
      i18n-keys.js            chaves em português
      i18n-en.js              traduções em inglês
      i18n-es.js              traduções em espanhol
      i18n-fr.js              traduções em francês
      i18n-build.js           monta o dicionário
      i18n-core.js            detecção de idioma e tradução em tempo real
      pages-*.js              conteúdo das páginas internas
      app-*.js                comportamento (rolagem, rotas, menu, ciclo)
    assets/clientes/        logos das empresas
    assets/logo/            logo e favicons
    assets/og/              imagem de compartilhamento
    fonte/                  arquivo de origem e script de geração

## Idiomas

Português do Brasil é o padrão. O site segue o idioma do navegador (português,
espanhol, inglês ou francês) e abre em inglês para os demais. A escolha manual do
visitante é guardada no navegador e tem prioridade. Robôs de prévia de link recebem
sempre português. As páginas de Privacidade, Cookies, Acessibilidade e Termos de uso
são publicadas em português nos quatro idiomas, com uma nota indicando isso.

## Como alterar o conteúdo

O arquivo `fonte/teduc-fonte.html` é a origem: um único HTML com todo o site.
Depois de editá-lo, rode `python3 fonte/build.py` para regenerar os arquivos da raiz.
Ajustes pontuais também podem ser feitos direto nos arquivos gerados.

## Imagem de compartilhamento

`assets/og/teduc-og-pt.png` é uma captura da capa do site em português, em 1200 × 630.
Quando a capa mudar, refaça a captura para o cartão continuar igual ao site.
