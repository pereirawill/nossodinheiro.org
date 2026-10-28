# Painel — Agora: o que está sendo olhado no site

Última revisão: 2026-10-28. Código: `functions/api/e.js` (recebe), `functions/api/agora.js` (agrega),
`site/public/agora.js` (desenha), `site/src/pages/agora/index.astro` (página), `db/agora.sql` (tabela).
Infraestrutura: Cloudflare Pages Functions + banco D1, na mesma conta do site.

## 1. Por que esta página é diferente de todas as outras

Todo o resto do site publica **o que os órgãos públicos divulgam**, com a fonte de cada número. Esta página publica o
**movimento do próprio site**: quantas pessoas estão lendo agora, o que subiu na última hora, o que foi mais aberto no
dia, quais filtros de partido e de estado foram mais consultados e de qual domínio as pessoas chegaram. É a única
exceção ao princípio editorial, e está dita na própria página.

## 2. O que é coletado, e o que não é

Coletamos, por página aberta: o **caminho** da página, o **título**, o **horário** e o **domínio de origem**.

**Não coletamos:** endereço de IP, cookie, user-agent, modelo de aparelho, tamanho de tela, localização, nem o endereço
completo de onde a pessoa veio (só o domínio). Nada é cruzado com nada e nada identifica ninguém.

Para não contar a mesma pessoa várias vezes no número de "agora", o navegador gera um identificador **aleatório** que
vive no `sessionStorage` — morre quando a aba fecha — e vai no sinal apenas para a contagem de sessões distintas. Ele
não é derivado de nenhum dado da pessoa e não serve para reconhecê-la em outra visita.

**Retenção: 48 horas.** A limpeza roda junto com as gravações (uma em cada duzentas apaga o que passou do prazo).
**Robôs são descartados** pelo user-agent, que é lido e não gravado. Quem usa automação de navegador (`navigator.webdriver`)
também não é contado.

## 3. Como cada número é calculado

| Número | Conta |
|---|---|
| pessoas no site agora | sessões distintas com evento nos últimos **5 minutos** |
| o que mais subiu na última hora | aberturas na última hora menos as da hora anterior, por página, só com 3+ na última hora |
| mais abertas do dia | aberturas nas últimas 24 h, por página |
| partidos e estados mais olhados | aberturas de páginas de filtro (`/deputados/partido/…`, `/deputados/uf/…`, `/municipios/<uf>/…`) em 24 h |
| de onde chegam | domínio de origem em 24 h; "direto" é quem digitou o endereço ou veio de app que não informa |

O endpoint tem cache de 20 segundos na borda, e a página se atualiza no mesmo ritmo.

## 4. Degradação proposital

O banco é **opcional**. Se o token da Cloudflare não tiver permissão de D1, ou se o banco estiver fora, o passo do
deploy falha sozinho, o site é publicado sem o binding e `/agora/` mostra "indisponível". Nenhuma outra página do site
depende disso, e o sinal do navegador é ignorado em silêncio (resposta 204).

## 5. Limites conhecidos

1. O plano gratuito do D1 aceita cerca de **100 mil gravações por dia**. Um post que viralize no Instagram pode passar
   disso; nesse caso o próximo passo é amostrar no navegador (gravar uma fração das visitas e multiplicar), o que já
   está previsto no desenho.
2. Quem bloqueia JavaScript não é contado — e isso é correto, porque é quem escolheu não ser contado.
3. O número de "agora" conta **abas**, não pessoas: quem abre duas abas conta uma vez, porque o identificador é por
   aba... na prática, cada aba gera a sua sessão, então duas abas contam duas. Está declarado na página.

## 6. Sugestões (`/sugestoes/`)

Formulário na mesma infraestrutura: `functions/api/sugestao.js` grava na tabela `sugestao`.

- **Guardamos:** o texto, o contato que a pessoa escrever (opcional, campo livre), a página de onde veio e o id de
  sessão. **Não guardamos** IP, user-agent nem cookie.
- **Nada é publicado automaticamente.** É caixa de sugestão, não comentário público: o site só mostra **quantas**
  chegaram em 24 horas, nunca o texto. Publicar texto de terceiro exigiria moderação, e não é o que o site faz.
- **Anti-robô sem captcha:** um campo-armadilha escondido no formulário (só robô preenche) faz a requisição ser
  descartada em silêncio, respondendo "ok" para o robô não tentar de novo. Além disso, no máximo 3 sugestões por sessão
  por hora e uma a cada 20 segundos.
- **Funciona sem JavaScript:** o formulário faz POST comum e o endpoint responde com redirecionamento para
  `/sugestoes/obrigado/`. Com JavaScript, envia sem sair da página.
- **Como ler:** `make sugestoes` (precisa de token da Cloudflare com permissão de D1). Traz as 50 últimas, em horário
  de Brasília.

## 7. Pendências

1. **Duelos lado a lado**: exige antes uma página de comparação entre dois parlamentares, que o site ainda não tem.
2. Cidades mais consultadas aparecem hoje dentro do recorte por estado; separar município de UF no agregado.
3. Amostragem automática quando o volume diário passar de um limite.
