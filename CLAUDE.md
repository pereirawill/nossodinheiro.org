# Nosso Dinheiro — contexto do projeto

Site de transparência pública do Brasil (estilo politicometro.org), base de um perfil de Instagram
sobre política e cidadania. Dono: Will (SRE sênior). Site em português. Princípio editorial:
"Só o que os órgãos públicos publicam, com a fonte de cada número" — sem nota, ranking de
bom/ruim nem opinião; toda premissa documentada em `docs/metodologia/`.

- Produção: https://nossodinheiro.org (Cloudflare Pages, projeto `nossodinheiro`, domínio ativo com SSL)
- Repo: github.com/pereirawill/nossodinheiro.org (privado por enquanto; código MIT, dados/textos CC BY 4.0)
- Identidade visual: Big Shoulders Display (números-herói), Public Sans (corpo), IBM Plex Mono (fonte/data),
  fundo #f2f4f2, cartões brancos, cor só nos dados. Tudo em `site/src/layouts/Base.astro`.

## Arquitetura
```
fontes oficiais ──► etl/ (Python 3.12, httpx, DuckDB) ──► data/raw/*.jsonl.gz (não versionado)
                                                           data/parquet/ (artefato do Actions)
                                                           data/public/*.json ──► site/public/data/ (versionado)
site/ (Astro 5 estático, SVG gerado no build, zero JS) ──► wrangler pages deploy ──► Cloudflare Pages
```
Workflows (`.github/workflows/`):
- `etl.yml` — Câmara. Diário 06:17 BRT (desde 26/10/2026) e em push em `etl/**`. Commita JSONs, dispara deploy.
- `etl-portal.yml` — Portal da Transparência. Terça 03:23 BRT (janela de 700 req/min). `workflow_dispatch`
  com inputs `etapa` (inspect | poderes | emendas | emendas-documentos) e `ano`.
- `etl-{renda,seguranca,credito,saude,inflacao,corrupcao,previdencia,obras}.yml` — mensais (dias 7, 9, 10, 11, 12, 13, 14, 15); `etl-cambio.yml` — dias úteis; `etl-irpf.yml` — 8/4 e 8/5 (edição anual); `etl-educacao.yml` só dispatch (INEP bloqueia o GitHub). `deploy.yml` — após qualquer ETL ou push em `site/**`. Usa secrets `CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_ACCOUNT_ID`.
Secrets existentes: os dois da Cloudflare + `PORTAL_TRANSPARENCIA_KEY`. Workflow permissions = read/write.

Comandos: `make test` (smoke test com fixtures sintéticas), `make etl ANO=2026` (FONTE=bulk padrão),
`make site`. Disparar workflow via REST (GraphQL bloqueado no gh):
`gh api -X POST repos/pereirawill/nossodinheiro.org/actions/workflows/etl-portal.yml/dispatches -f ref=main -f 'inputs[etapa]=poderes' -f 'inputs[ano]=2025'`

## Menu: duas tentativas recusadas (28/10/2026)
- O dono disse que o menu tinha itens demais (30 numa linha). **Tentativa 1**: 6 grupos + segunda linha só com o grupo
  da página → recusada ("todas as subpáginas inacessíveis": ir de Deputados a Impostos virou dois cliques).
  **Tentativa 2**: todos os painéis visíveis em blocos com legenda → recusada ("ficou pior"). Olhei a página no
  navegador e ela confirma: as legendas criam uma escada irregular e o cabeçalho cresce de 2 para 4 linhas.
- **Revertido para o menu original** (fila única de 30 pílulas, `const nav` no `Base.astro`). `site/src/lib/menu.ts` e
  as páginas `/secao/` foram removidos. **Não mexer no menu de novo sem antes mostrar uma imagem ao dono**: o layout é
  dele, e as duas tentativas às cegas custaram dois deploys e a paciência dele.

## Estrutura do site (26/10/2026)
- `/` = painel Geral (panorama: União por função via `poderes_funcao_<ano>.json`, três níveis via SICONFI, cartões dos painéis).
  Deputados mudou para `/deputados/`. `/judiciario/` = índice dos tribunais (SIOP) com link para `/stf/`; demais tribunais
  pendentes (mesmo molde do STF). Menu: Geral, Deputados, Senadores, Presidência, Judiciário, Emendas, Poderes, Estados,
  Municípios, Obras, Estatais, Economia, Impostos, Imposto de Renda, Inflação, Trabalho, INSS, Aposentadoria, Renda, Educação, Segurança, Saúde, Inadimplência, Corrupção, Rankings, Histórico, Metodologia, Sobre. Pedidos na fila: painel "Presença e votações" (Câmara/Senado),
  painel "Trabalho" (PNAD/Mapa de Empresas/INSS BEPS tabela 14/Bolsa Família via API por município).

## Painel 1 — Custo por deputado (NO AR, dados reais)
- Fonte CEAP: **CSV anual** `camara.leg.br/cotas/Ano-YYYY.csv.zip` (o endpoint `/deputados/{id}/despesas`
  da API v2 respondia 200 com lista vazia em 26/10/2026 — registrado na metodologia). API v2 usada para
  `/deputados?idLegislatura=57` (dedupe por id: 648 na legislatura) e `/deputados/{id}` → `ultimoStatus`
  (filtro `situacao == "Exercício"` → 513).
- Fórmula: subsídio (DL 172/2022, R$ 46.366,19 desde **fev/2025** — corrigido 26/10/2026, antes estava fev/2026; 13 + 1/3 por ano) + CEAP líquida (valor
  real, líquido de glosas) + verba de gabinete pelo **teto** (R$ 165.806,07/mês; gasto real não está na
  API). Auxílio-moradia fora do total. Constantes com fonte/data em `etl/camara/config.py`.
- Resultado 2026 (10 meses): 513 deputados, CEAP R$ 135,6 mi, total R$ 1,25 bi, média R$ 243.528/mês.
  Custo mensal e anual projetado por deputado (§3.5 da metodologia).
- Reconciliação: site da Câmara mostra R$ 179,09 mi de CEAP em 2026; nosso 141,3 mi (todas as linhas
  com `ideCadastro`) → −21%, explicado por lideranças (sem ideCadastro) e ex-deputados. A conferir.
- Já calculado mas sem página: `ceap_categoria`, `ceap_fornecedor` (com url da NF), `fornecedor_rede`
  (CNPJ atendendo ≥5 deputados). Top categoria 2026: divulgação R$ 52,3 mi (37%).
- 28/10 (pedido do dono): `url_foto` passou do raw para o `custo_deputado_<ano>.json` (a coluna `urlFoto` da API já estava
  na tabela `deputados` do transform, só não era selecionada) e `TabelaDeputados.astro` mostra a foto quando a linha traz
  `url_foto` — vale para deputados e senadores (o Senado já publicava `url_foto`). As imagens são carregadas do site da
  Câmara e do Senado, com `loading="lazy"`, não copiadas para o repo. `/deputados/` ganhou `MapaBrasil` com a bancada por
  estado (513 em 27 estados) e `/senadores/`, mapa do custo médio por senador por estado (o tamanho da bancada é fixo em 3).
- Filtros por UF e partido são páginas estáticas (`/deputados/uf/{uf}/`, `/deputados/partido/{slug}/`,
  `site/src/pages/deputados/`, componente `TabelaDeputados.astro` + `PaginaFiltro.astro`, slug em `site/src/lib/slug.ts`).
- Pendências: teto CEAP por UF (Ato da Mesa 43/2009), gasto real de gabinete, confirmar 13º/férias,
  subsídio proporcional p/ quem assumiu no meio do ano, passagens SIGEPA não aparecem no CSV (verificar).

## Painel Senadores (NO AR, dados reais, sem chave)
- `etl/senado/extract.py`: `senadores` (lista atual), `legislatura --numero 57` (245, inclusive quem saiu; usado nas
  emendas), `recursos --ano` (JSON oficial `adm.senado.gov.br/adm-dadosabertos/api/v1/senadores/{id}/recursos-utilizados`:
  CEAPS por categoria, gastos não inclusos na cota — diárias, passagens aéreas, correios, mídias —, benefícios,
  nº de pessoal por gabinete). `transform.py` → `custo_senador_<ano>.json` + `meta_senado_<ano>.json`.
- Fórmula: subsídio (mesmo dos deputados) + CEAPS real + gastos fora da cota (real). **Sem pessoal do gabinete**
  (Senado publica só a quantidade; custo está na folha de servidores — pendência) e sem auxílio-moradia (só
  utilizou/não). 2026 (10 meses): 81 senadores, média R$ 90,8 mil/mês. Workflow `etl-senado.yml` (diário 06:47 BRT).
- Site: `/senadores/`, `/senadores/uf/{uf}/`, `/senadores/partido/{slug}/`; componentes parametrizados por `casa`.
  Metodologia: `docs/metodologia/painel-senadores.md`.

## Painel STF (NO AR, folha real do STF, sem chave)
- `etl/stf/extract.py folha --ano`: CSV do formulário `egesp-portal.stf.jus.br/transparencia/rendimento_folha`
  (`tipo_relatorio=CSV`; cargo 55 = ministros; `q[cdg_unidade_in][]` = folha de um gabinete; ids das lotações
  lidos do HTML). Para em 2 meses seguidos sem folha. `transform.py` → `custo_ministro_stf_<ano>.json` + `meta_stf_<ano>.json`.
- Custo = "Remuneração bruta após o teto + outras verbas" do ministro + soma da mesma coluna de quem está lotado no
  gabinete (sem o ministro). Presidente (Fachin) aparece com o Gabinete da Presidência (7 pessoas) — subestimado,
  avisado na página. Aposentados (16) como estatística separada. 2026 jan–ago: 10 ministros, média R$ 811 mil/mês
  (remuneração 53 mil + gabinete 758 mil, ~33 pessoas). **O portal do STF devolve 403 a IPs fora do Brasil** (runners
  do GitHub, qualquer UA) → sem agendamento; atualização mensal manual: `make stf ANO=2026` + commit. `etl-stf.yml` só dispatch.
- Site: `/stf/`. Metodologia: `docs/metodologia/painel-stf.md`.

## Painéis STJ, TST e STM (NO AR, mensal dia 24; feitos 28/10/2026)
- `etl/tribunais/` (`fontes.py` com um adaptador por tribunal, `extract.py`, `transform.py`) → `custo_magistrado_<sigla>_<ano>.json`
  + `meta_<sigla>_<ano>.json`; página única `site/src/pages/judiciario/[sigla].astro` (rota por arquivo publicado).
- Fontes: **STJ** dados abertos CKAN, 1 CSV cumulativo de 110 MB desde 2020 (resolver o recurso por `package_show`, o id
  muda; cache por `last_modified`); **TST** `transparencia-remuneracao.tst.jus.br/arquivos` (JSON) + `/arquivo?data-referencia=<ano>-<mês>-completo`
  (CSV); **STM** `www2.stm.jus.br/rem_web` (POST com cookie + token CSRF, botão Gerar CSV). Nenhuma traz CPF.
- **Medida comparável = bruto após o teto SEM indenizações.** Foi o achado que mudou tudo: o `Total de Créditos` do STJ
  inclui indenizações (R$ 30,8 mi num mês para um ministro; média R$ 36 mil/mês), e a coluna do STF não. Sem essa
  correção a comparação dava R$ 1,1 mi contra R$ 811 mil do STF. O CSV do STM não detalha verbas e é antes do teto →
  declarado em `coluna_valor`, na página e na metodologia.
- 2026 (até set), **média do ano / último mês**: TST 26/27 R$ 991 mil / R$ 1,06 mi; STJ 32/33 R$ 909 mil / R$ 924 mil;
  STF 10/11 R$ 811 mil (só média); STM 13/15 R$ 304 mil / R$ 343 mil. Gabinetes de 41, 43, 31 e 15 pessoas. O índice
  `/judiciario/` mostra as duas colunas, porque o painel do STF só tem média e os novos destacam o último mês. Destaques usam o **último mês**, não a média: em 2026 um ministro do STJ está
  afastado e a equipe passou ao gabinete de um desembargador convocado em fevereiro.
- Regras no transform: magistrado convocado só vira linha se chefia gabinete **sem titular** (no TST é juiz auxiliar
  dentro do gabinete de um ministro → conta como pessoal); unidades de direção fora do custo por ministro, em tabela
  própria; pseudo-lotações (INATIVO, PENSIONISTA, À DISPOSIÇÃO, EXONERADO) fora; chave por matrícula, porque a grafia do
  nome muda de mês para mês no STJ. Invariante: nenhum mês pode ter mais magistrados que a composição legal.
- **Os runners do GitHub alcançam STJ, TST e STM** (workflow verde em 28/10/2026) — diferente do STF, que bloqueia IP de
  fora. `etl-tribunais.yml` roda dia 24 e tolera a falha de um tribunal sem derrubar os outros.
- **Sem painel, com motivo documentado**: TJDFT (consulta com reCAPTCHA v3, sem arquivo, embora a página declare CSV/XLS);
  TSE (folha aberta em HTML, mas ministro é cedido do STF/STJ e o arquivo traz só a gratificação eleitoral, ~R$ 21 mil);
  CNJ (`cnj.jus.br/remuneracao/rem.php`, HTML; 9 dos 11 conselheiros são requisitados e o gabinete é nomeado pela vaga).
  Metodologia `docs/metodologia/painel-tribunais.md` §7.
- 28/10: **TRF4 e TRF6 no ar** (`/judiciario/trf4/`, `/judiciario/trf6/`), rótulo "desembargador". O transform ganhou
  `gabinete` opcional na linha: quando a lotação do magistrado é genérica, o **adaptador** informa a chave do gabinete.
  TRF4 casa por **código** (`TRF4/GLIPPEL`, compartilhado com a equipe) e o Total de Créditos já vem pós-teto; busca os
  4 meses mais recentes (50 por página, ~24 requisições/mês) e a folha de magistrados da fonte para em abr/2026. TRF6 é
  XML mensal, lotação do desembargador é genérica → casamento por tokens de sobrenome com tolerância de grafia
  (`KUSCHEL`×`KUSCHELL` na fonte); mês vem do NOME do arquivo (o diretório é o do upload e dois links do índice apontam
  para o mês errado). Resultado: TRF4 36/39 a R$ 326 mil/mês (14 pessoas/gab), TRF6 16/18 a R$ 186 mil/mês (8 pessoas).
- **TCU, TRF1 e TRF5 sem painel, com motivo**: TCU tem API JSON viva mas **não publica lotação** (sem isso não há
  gabinete por ministro); TRF1 está com o sistema em manutenção e só há espelho congelado até 03/2025; TRF5 publica só
  PDF e está parado em fev/2026. TRF2 e TRF3 em levantamento. Tudo na metodologia §7.

## Painel Presidência (NO AR, sem chave, mensal dia 15)
- `etl/presidencia/extract.py cpgf --ano`: ZIP mensal `portaldatransparencia.gov.br/download-de-dados/cpgf/AAAAMM`
  (precisa de UA de navegador + Referer; mês não publicado = 403, pulado). Guarda órgão superior 20000 + total do governo
  por mês. `viagens --ano` baixa o ZIP anual (~90 MB) e filtra 20000 — extrator pronto, sem página ainda.
- `transform.py` → `presidencia_cpgf_<ano>.json` (meses, por órgão, por tipo, favorecidos PJ top 25, nº portadores, totais).
  2026 jan–ago: R$ 10,47 mi, 98% sob sigilo. Página `/presidencia/` reaproveita `poderes_orgaos_2025` (órgão 20000).
- Privacidade: CPF de favorecido PF mascarado no extrator; site não lista portadores nem favorecidos PF.

## Painel Municípios e estados (sem chave; DCA anual)
- `etl/municipios/extract.py`: `entes` (SICONFI, 5.597 entes com população), `vagas` (TSE consulta_vagas, cargo vereador),
  `dca --ano` (API SICONFI, 1 chamada por ente, 4 workers, ~10 min, retomável). `transform.py` → `municipios_<ano>.json`
  (função 01 Legislativa paga = custo da Câmara; por hab, por vereador, % orçamento, faixa de população), `estados_<ano>.json`
  (Legislativa, Judiciária, Essencial à Justiça, Administração, Segurança, Previdência, Saúde, Educação, Encargos),
  `municipios_meta_<ano>.json` (cobertura, medianas por faixa).
- Site: `/municipios/`, `/municipios/uf/{uf}/`, `/municipios/{uf}/{slug}/` (≈5.5 mil páginas); `/estados/` (funções por estado,
  por habitante). Subsídio dos governadores: 27 leis estaduais, só com fonte primária — levantamento pendente (não usar compilações de imprensa). Workflow `etl-municipios.yml`
  (mai/ago/nov). Salário de vereador NÃO existe em base nacional (lei municipal, teto CF art. 29 VI). Metodologia: `painel-municipios.md`.

## Painel Impostos (NO AR, sem chave, mensal dia 25)
- `etl/impostos/extract.py`: CSV `gov.br/receitafederal/dados/arrecadacao-estado.csv` (2000→, por mês × UF × tributo).
  Parser `_brl()` lida com formatos misturados ('8762245,567' = decimal; '1,006,523,961' = milhar); famílias agregado ×
  detalhado deduplicadas. Bases de incidência = convenção nossa (ver metodologia). Conferido: mar/2026 224,6 bi (RFB 229,25).
- 28/10: `serie_longa` (tabela **TRIB 01-B**, "Total da Receita Tributária" em % do PIB) dá a carga **ano a ano de 2002
  a 2024** — a Tab_01 que usávamos pula anos. Gráfico de `/impostos/` passou a usá-la. **Não dá para ir a 1989**: as
  edições pré-2015 do estudo dão 404 e cada edição republica a série com PIB revisado; a página diz isso em vez de
  emendar bases. Mín. 29,0% (2020), máx. 32,2% (2024). E `ocde` (tabela 07) trouxe Brasil × média de 36 países da OCDE
  por base: total 32,0% × 34,1%, mas bens e serviços 13,0% × 10,5% e renda 9,1% × 12,3% — está em `/comparacao/`.
- Saída `impostos.json`: anual (2000→), mensal (24 m), por UF, tributos do ano. Página `/impostos/`. Pendente: estados e
  municípios via SICONFI para "quanto já foi arrecadado" oficial (Impostômetro da ACSP é privado — não usar).

## Painel Imposto de Renda (NO AR, sem chave, anual; feito 27/10/2026)
- `etl/irpf/extract.py` → `irpf.json`, `/imposto-de-renda/` (menu depois de Impostos). Fonte: **Receita Federal, Grandes Números
  do IRPF**, planilha de tabelas (~20 MB). O slug muda por edição (2024 termina em `-tabelas-1`) → o extrator lê o índice e pega
  o link mais recente por regex. Cache em `data/raw/gn_irpf_ac<ano>.xlsx`. Salário mínimo vem do **SGS 1619** (dezembro do ano),
  porque a planilha publica as faixas em salários mínimos anuais (`piso × 12 × SM`); conferido contra a tabela 5.
- Tabelas 8 (faixa de renda total), 15 (natureza da ocupação) e 16 (ocupação principal, 134 categorias). `x` = sigilo → zero,
  contado em `celulas_suprimidas`; **nunca** reconstruir subtraindo do total. Categoria vazia da Tab16 = "Não informada"
  (6,6 mi de declarantes, a 2ª maior). Invariantes: 30–80 mi de declarantes, totais das 3 abas dentro de 0,1%, imposto > 50 bi.
- AC 2024: 41,7 mi de declarantes, renda R$ 6,089 tri, imposto devido R$ 348,8 bi (alíquota média 5,7%). **A curva de alíquota
  efetiva sobe até 9,9% na faixa de 15–20 SM (R$ 21–28 mil/mês) e cai para 2,1% no topo** (renda média R$ 1,69 mi/mês), porque
  77,5% da renda do topo é isenta — 49,1% disso é lucro e dividendo, 20,2% herança. Faixas de 7 a 30 SM: 33,6% da renda e 54,7%
  do imposto. Subsídio do deputado em 2024 = R$ 584.422,67 (34,5 SM, dentro da faixa 30–40) → "pelo menos 867.083 (2,08%)
  declararam acima do teto da faixa dele"; o número exato não existe (a Receita publica faixas).
- Natureza da ocupação: servidor municipal R$ 8,5 mil/mês, estadual 15,9, federal 24,8, militar 12,6, proprietário de empresa
  26,6, capitalista 32,5. Ocupações: titular de cartório 203,5 mil (maior das 134), Judiciário/TCU 95,9 mil, MP 93,3 mil,
  "Membro do Poder Legislativo" só 12,0 mil (reúne 58 mil vereadores). **Os dados contrariam a tese de que o funcionalismo em
  bloco é a elite** — a página publica a curva e as médias e não escreve conclusão (pedido do dono em 27/10).
- Impostos ganhou `carga.bases` da tabela **INC 01-A** do estudo Carga Tributária (oficial, três níveis): bens e serviços 43,5%,
  renda 28,3%, folha 21,2%, propriedade 5,3%, transações financeiras 1,8%. Usado na página do IRPF para dizer que 71,7% da
  arrecadação não é imposto sobre renda. Metodologia: `docs/metodologia/painel-imposto-de-renda.md`.

## Painéis Renda, Educação, Segurança, Inadimplência (NO AR, sem chave, mensais dias 7–10; feitos 26–27/10/2026)
- `etl/ufs.py`: tabela fixa das 27 UFs (código IBGE, sigla, nome) + `normalizar()`; usada pelos quatro.
- **Renda** `etl/renda/extract.py` → `renda.json`, `/renda/`: SIDRA 4659 (rendimento por posição, Brasil série + UF), 7527/7530
  (massa por percentil), 7533, 7438 (limites P90/P99), 7535 (ocupados por percentil), 7435 (Gini). Público 5.301 × privado c/
  carteira 3.176 (2025); 1% com 11,0% da renda.
  27/10: **"quantos vivem com até um salário mínimo"** entrou no `renda.json` (`censo_sm`) e na página. Vem do **Censo 2022**
  (SIDRA 10292 ocupados e 10296 moradores) porque a PNAD publica renda em reais, não em classes de salário mínimo; SM de 2022
  (R$ 1.212) vem do SGS 1619. Brasil: 34,3% dos ocupados e **58,2% dos moradores** (117,5 mi) com até 1 SM por pessoa; MA 80,4%.
  As duas medidas respondem perguntas diferentes e a página explica (um mínimo para quatro pessoas = 1/4 por morador).
  28/10: `acumulado` (1, 2, 3, 5 e 10 SM; "sem rendimento" fora da soma) nos dois universos e `*_pct_ate_3_sm` por UF —
  até 3 SM são 81,3% dos ocupados e 88,4% dos moradores (MA e PI: 94,8%).
- **Educação** `etl/educacao/extract.py` → `educacao.json`, `/educacao/`: INEP zips `divulgacao_{brasil,regioes_ufs}_ideb_<ano>` e
  `divulgacao_<etapa>_municipios_<ano>` (openpyxl; md5 do zip conferido; TLS do INEP falha → retry sem verify + md5; abreviações
  "R. G. do Sul"). Município = rede pública. 2023 é a última edição (2025 sai em 2026). **INEP bloqueia runners do GitHub**
  (connection reset) → workflow só com dispatch; rodar local e commitar o JSON, como o STF.
  28/10 (pedido do dono): `escolaridade()` no mesmo extrator → bloco `escolaridade` no `educacao.json`, da **PNAD Contínua**
  (SIDRA 7189, 25 anos ou mais por nível de instrução; 7113, analfabetismo 15+), série 2016–2025, Brasil e UF, com mapa.
  2025: 69,4% dos adultos terminaram o fundamental, 57,4% o médio, 21,4% o superior; 30,7% sem o fundamental (43,2 mi);
  analfabetismo 4,9% (era 6,7% em 2016). **Analfabetismo funcional não entra**: IBGE não publica mais e o INAF é de
  instituto privado — usamos "sem o fundamental" como medida oficial próxima. **Não dá para medir desde o Plano Real**:
  a série começa em 2016 e a PNAD antiga tem outra metodologia; a página declara isso em vez de emendar séries.
  28/10 (segunda rodada, pedido do dono): **analfabetismo desde 1991** (`analfabetismo_longo`), juntando SIDRA 204
  (Censo 1991 e 2000), 271 (PNAD antiga 2001–2015) e 7113 (PNADC 2016–2025) — 20,1% → 4,9%, queda de 15,2 p.p. em 34
  anos. Nas duas primeiras a taxa de 15+ é somada por nós das faixas de idade (não publicam o agregado). **Não existe
  1988**: o Censo mais próximo é 1991. Três cores no gráfico, uma por pesquisa, sem emendar. A página ganhou pizza da
  escolaridade, gráfico de linhas da evolução 2016–2025 e o aviso de que não há dado de 2026 (PNADC 2025 é a última,
  IDEB 2023 é o último).
- **Segurança** `etl/seguranca/extract.py` → `seguranca.json`, `/seguranca/`: MJSP Sinesp VDE `bancovde-<ano>.xlsx` (26 MB, servidor
  corta download → 4 tentativas; cache em data/raw), abrangência Estadual, eventos separados (sem MVI), vítimas × ocorrências,
  população SIDRA 6579 do mesmo ano; municípios ≥100 mil + capitais; série 2015+ por UF (baixa 11 arquivos, ~5 min).
  Roubo/furto/estupro/intervenção só por UF. dados.mj.gov.br não resolve DNS; gov.br/mj é a fonte.
- 27/10 (pedido do dono): Segurança lidera pelo **total (MVI)**, não só homicídio doloso — homicídio + latrocínio + lesão seguida de
  morte + intervenção de agente do Estado = 39.555 em 2025 (18,5/100 mil). **Feminicídio não soma** (qualificadora do homicídio;
  conferido: 1.578 × 2.084 vítimas mulheres). Fora: trânsito, suicídio, mortes a esclarecer, tentativas. Por município exclui
  intervenção policial (só vem por UF). `MVI`/`MVI_MUNICIPIO` no extrator; série por UF virou MVI + componentes.
- **Inadimplência** `etl/credito/extract.py` → `credito.json`, `/inadimplencia/`: BCB `bcb.gov.br/pda/desig/scrdata_<ano>.zip` (ano
  corrente + anterior, ~300 MB; CSV mensal, DuckDB), inadimplência = >90 dias ÷ carteira ativa, por UF/cliente/modalidade/porte;
  série 24 meses. Sem dado municipal (só UF; "sub-região" do BCB é codificada). **Sem faixa etária** (pedido de 27/10): o SCR não
  publica idade; o recorte mais próximo é `cnae_ocupacao` (PF), que inclui "Aposentado/pensionista" — virou tabela na página.
- `openpyxl` entrou em requirements. Glossário ganhou 14 termos (rendimento_habitual … modalidade_credito).

## Painel Obras (sem chave, mensal dia 15; feito 27/10/2026)
- `etl/obras/extract.py` → `obras.json`, `/obras/` (menu depois de Municípios). **Host novo**: `api.obrasgov.gestao.gov.br/obrasgov/api/`
  (`api-publica.*` devolve 404 — era esse o motivo de o painel estar parado desde o início). Dois endpoints: `projeto-investimento`
  (uma linha por obra) e `execucao-financeira` (empenhos por `idProjetoInvestimento`).
- **Limites medidos**: página máxima 50 (100+ = HTTP 500); **~85 s por requisição**, ~25% de 500/524 sob carga; 8 requisições em
  paralelo rendem ~8 páginas/82 s; `totalElements` do endpoint de obras é falso (repete o servido). Coleta **retomável**
  (`.parcial.gz` + `.pagina`), termina só após **dois blocos vazios e limpos**, e falha se vierem <15 mil obras (cadastro tem ~25 mil).
  Workflow com `timeout-minutes: 240`.
- **Coleta de 27/10 concluída (no ar)**: 124.148 obras, 17.110 com empenho federal; **1.779 paradas** (793 paralisadas +
  986 inacabadas), R$ 49,1 bi previstos e R$ 0,4 bi empenhados nelas; 1.612 com prazo vencido. Situações: Cadastrada 57.527,
  Concluída 41.486, Em execução 19.302, Cancelada 3.540, Inativada 511. A coleta levou ~5 h (cadastro + execução financeira,
  34.665 empenhos); 4 páginas de empenhos não responderam e a página declara isso.
- Regras: paradas = situação "Paralisada"/"Inacabada" (declarada pelo órgão); previsto ≠ gasto; `dataSituacao` é a última atualização
  do status → a página separa "sem atualizar a situação" de "atraso do prazo"; `qdtEmpregosGerados`/`populacaoBeneficiada` são
  declarados pelo órgão e ficam fora dos destaques.

## Painel Estatais (NO AR, sem chave, mensal dia 16; feito 28/10/2026)
- Pedido do dono: "lucro das estatais desde 1988". **1988 não existe** em fonte aberta — a página declara isso e mostra até onde cada
  fonte volta. Três recortes, nunca somados: `etl/estatais/dividendos.py` (Tesouro/RTN, aba 2.2, linha 1.4.2, **desde 1997**, por
  empresa; arquivo resolvido pela API do CKAN porque o nome muda todo mês), `etl/estatais/sest.py` (microdado da SEST, **desde 2016**,
  todas as federais inclusive as fechadas — Caixa, Correios, BNDES) e `etl/estatais/extract.py` (CVM, **desde 2010**, empresa por
  empresa nas três esferas). Saída única: `estatais.json`; página `/estatais/` (menu depois de Obras — 31º item, único acrescentado).
- **SEST**: ZIPs em `gov.br/gestao/.../estatais/transparencia/sest{identificacao,dadosfinanceiros}.zip` (UA de navegador + Referer).
  Agregado = só as **44 de controle direto** (as 73 indiretas já estão no consolidado da mãe). Armadilhas: conta do lucro tem dois
  códigos (`500000` antigo, `290000000` atual); `500000` colide com outros demonstrativos → filtrar `demonstrativo=='DRE'`; os 9
  **grupos** ("GR. PETROBRAS") duplicam; o ano corrente vem no `4º Trimestre` (acumulado), sem linha `Anual`. Duas somas no JSON
  porque a Eletrobras saiu em 17/06/2022: em 2016 incluir as inativas **inverte o sinal** (−1,4 bi → +2,0 bi). 2025: R$ 168,1 bi
  (MGI publicou 169,4 — 0,8%; parte é CDRJ e Ceasaminas sem DRE, o resto **não está explicado** — em 2024 as 44 estão lá e sobram 2,0 bi); maior prejuízo = Correios −8,5 bi; 17 dependentes do Tesouro.
- 28/10 (o dono perguntou se a página não estava "muito otimista" — estava, e em um ponto era erro): o arquivo da SEST traz **as duas
  pontas**. `subvencao`/`sem_subvencao` (DRE 407000 e 260100000), `aporte` (400700/330034000), `afac` (400600/330031000) e
  `dividendo_pago`/`jcp_pago` (400411/400421). **A subvenção é receita na DRE**, então o lucro publicado já a inclui: 2025 cai de
  168,1 para **137,2 bi**; a subvenção foi de 12,7 bi (2016) a 30,9 bi (2025). A EBSERH publica −159 mi e é **−13,8 bi** antes da
  subvenção de 13,7 bi; 13 empresas no vermelho pelo publicado, **18** sem a subvenção. Armadilha: no ano que vem do 4º trimestre, o
  fluxo tem de ser lido no **mesmo** trimestre (ler o 1º dava 6,8 bi em vez de 30,9) — tem teste. Em 2018–2020 a União **pôs mais do
  que recebeu**. Fora da conta (declarado): renúncia fiscal, crédito subsidiado e garantia da União.
- **CVM**: DFP (`DRE_con`, cai no `DRE_ind`) + **formulário de referência** (`posicao_acionaria`). A linha do lucro **não tem código
  fixo** (3.11 nas não financeiras, 3.09 nos bancos até 2019) → achada pela descrição; fixar 3.11 tirava 10 anos de BB e Banrisul.
  Quem era estatal em cada ano **sai do formulário**, não de datas digitadas: ente público com ≥50% das ON em posição direta (ou
  marcado controlador com ≥20%), controle indireto conta, ano sem formulário é interpolado entre confirmados e para trás, **nunca
  para frente** (ausência depois do último confirmado = privatização). Falso positivo corrigido: "do **Estado** de São Paulo" no nome
  da Sabesp (privatizada, comprou a Emae em 2026) a fazia passar por ente público.
- Fora da lista, documentado em `docs/metodologia/painel-estatais.md`: IRB (União tem 11,7% direto; os 50,7% são cadeia via BB),
  CEEE-G, FCA/FNS/Transnordestina/Rota do Oeste/Guarulhos/Metanor (erro de preenchimento ou concessão), Taesa/Gasmig, BRB (não
  entrega DFP). **Não entra** o "déficit das estatais" do conceito fiscal do BCB (desde dez/2001, três esferas, exclui Petrobras e
  Eletrobras) — outro número, outro sinal, outro universo.
- RAEEF e Panorama das Estatais são inacessíveis (PDF atrás de login quebrado no Plone; painel é embed de Power BI/Qlik); a API
  `dados.gov.br/api/publico` exige chave e o catálogo lista 3 de 5 URLs erradas → URLs dos ZIPs fixas no código.

## Painéis INSS e Aposentadoria (NO AR, sem chave, mensal dia 14; feitos 27/10/2026)
- Pedido de 27/10: **duas abas**, com a diferença explicada nas duas (o dono escolheu duas, contra a recomendação de uma só).
- `etl/previdencia/extract.py` → `previdencia.json`: BEPS abas **15** (espécie: quantidade, valor, valor médio — hierarquia em
  `GRUPOS_15`, rótulos com nota de rodapé no texto da célula → corta no primeiro parêntese, nas chaves e nos valores), **19** (UF,
  só RGPS; UFs vêm indentadas, regiões não) e **13** (série desde 2000). Ago/2026: 42,7 mi de benefícios, R$ 80,3 bi/mês.
- `/inss/` = tudo que o instituto paga (42,2% não é aposentadoria; BPC 6,6 mi); `/aposentadoria/` = os dois regimes, com RPPS da
  União vindo de `poderes_categoria_2025` (subcategoria "Aposentados e pensionistas", R$ 135,4 bi) e estados da função 09 do SICONFI
  (R$ 226,2 bi). Ano do INSS = mês × 13, rotulado. **Sem contagem de aposentados do RPPS** (não há base aberta) → não comparamos
  valor médio entre regimes. `xlwt` entrou em requirements só para os testes.

## Painel Inflação (NO AR, sem chave, mensal dia 12; feito 27/10/2026)
- `etl/inflacao/extract.py` → `inflacao.json`, `/inflacao/` (menu depois de Impostos). SIDRA 1737 (IPCA desde dez/1979: índice,
  mês, ano, 12 meses), 7060 (9 grupos + peso; e 16 áreas via N7/N6), 7063 (INPC), BCB SGS 13521 (meta do CMN desde 1999).
  Códigos dos grupos fixos em `GRUPOS` (API de metadados do IBGE dá timeout no GitHub). Set/2026: 4,58% em 12 meses, meta 3,0%.
- Gráfico começa em 1996 (antes, hiperinflação achata tudo); comparação com a meta usa só o **valor central** (sem banda) e diz isso.
- Tabela "quanto os preços subiram desde…" usa o número-índice; avisa que houve cinco trocas de moeda. **Sem mapa**: não existe
  IPCA por estado (só 16 áreas). Pendências: IPCA-15, subitens, Selic (SGS 432 deu 502), IGP-M (FGV é paga).

## Painel Punições/Corrupção (NO AR, sem chave, mensal dia 13; feito 27/10/2026)
- `etl/corrupcao/extract.py` → `corrupcao.json`, `/corrupcao/` (menu: "Corrupção", depois de Inadimplência). Portal da Transparência
  `download-de-dados/{ceis,cnep,ceaf,acordos-leniencia}/AAAAMMDD` (ZIP+CSV latin-1, UA+referer, tenta 8 dias para trás; o ZIP de
  leniência tem 2 CSVs → escolher "Acordos"). Cabeçalhos com travessão cp1252 `\x96` → normalizados na leitura.
- **Privacidade**: CEIS/CNEP trazem CPF em claro → só contagens no JSON; nomes apenas de órgãos e da razão social nos acordos.
- Out/2026: CEIS 23.811 sanções (estadual 9.863, federal 8.509, municipal 5.289; 857 sem UF), CNEP 1.858 com R$ 3,95 bi de multas,
  CEAF 4.044 expulsões (só federal), 152 acordos de leniência. UF = do **órgão sancionador**, não da empresa; ano = início da sanção.
  Fundamentos do CEAF se sobrepõem (uma decisão cita vários artigos). CPI da Transparência Internacional vem de `rankings.json`.
- Pendências: valor devolvido nos acordos (texto livre), CEPIM (403), lista do TCU, improbidade na Justiça estadual.

## Câmbio e poder de compra (dentro de /inflacao/, feitos 27/10/2026)
- **Poder de compra**: calculado na página a partir do índice do IPCA — R$ 100 de jul/1994 compram R$ 11,90 hoje (perda de 88,1%);
  curva mensal desde o Plano Real e projeção do "dinheiro parado". A tabela "quanto os preços subiram desde…" teve os rótulos
  ambíguos trocados (o dono apontou: "R$ 100 daquela época valem hoje" dava a entender dinheiro guardado no colchão).
- **Câmbio** `etl/cambio/extract.py` → `cambio.json` (workflow diário em dias úteis, 14:40 BRT): BCB SGS 3698 (dólar venda, média
  mensal desde jul/1994: 0,9333 → 5,14, +451%), SGS 11752 (câmbio efetivo real, deflacionado pelo IPCA; máx 171 em out/2002, mín 67
  em abr/1997, hoje ~120) e PTAX para 7 moedas com variação em 1, 5 e 10 anos. **PTAX só tem 10 moedas — sem yuan e sem peso
  argentino** (declarado na página). Aviso fixo: câmbio ≠ inflação, e o dólar também perde valor.

## Componente MapaBrasil (feito 27/10/2026)
- `site/src/lib/mapa-uf.ts` (105 KB, 27 paths + centroide) gerado por `python -m etl.mapa.gerar` das malhas do IBGE (API v2,
  resolução 2), projeção equirretangular, contornos simplificados. `MapaBrasil.astro`: coroplético sem JS, escala sequencial
  `color-mix` sobre a cor da página, rótulo UF + valor (estados pequenos com fio para fora, offsets em `FORA`), `<title>` por estado.
- Em uso: Segurança (homicídios/100 mil), Saúde (% com plano), Renda (renda por morador), Inadimplência (% PF), Educação (IDEB AI),
  Estados (despesa por habitante), Punições (sanções do CEIS). Regerar o TS só quando o IBGE publicar malha nova.
- Rótulo dos estados pequenos do Nordeste (RN, PB, PE, AL, SE) + ES e RJ vai para uma **coluna à direita** (dict `COLUNA`, y fixo)
  com fio de ligação; o viewBox ganha `FOLGA` de 230px. Antes ficavam fora do viewBox e sumiam (corrigido em 27/10/2026).

## Painel Saúde (NO AR, sem chave, mensal dia 11; feito 27/10/2026)
- `etl/saude/extract.py` → `saude.json`, `/saude/` (no menu logo depois de Segurança). Só busca o que faltava: **ANS** PDA 047
  (`dadosabertos.ans.gov.br/FTP/PDA/taxa_de_cobertura_de_planos_de_saude-047/pda-047-taxa_cobertura.csv`, 21 MB, latin-1, por
  município × sexo × faixa; DuckDB agrega por UF e capitais; **código da ANS tem 6 dígitos**, casa por `cod_ibge // 10`; coluna
  POPULACAO do arquivo vem zerada → taxa usa SIDRA 6579) e **IBGE** (7362 projeção de esperança de vida/mortalidade infantil,
  3834 MI observada até 2016, ODS 6695/6696/6694 de menores de 5 anos, neonatal e materna).
- O **dinheiro** não é rebaixado: a página importa `poderes_funcao_2025` (função 10 da União), `estados_2025` e `municipios_2025`
  (pago_saude). **Nunca somar os três níveis nem estado+prefeituras por habitante** — repasse fundo a fundo reaparece embaixo
  (a tabela por estado tem duas colunas "por habitante" separadas, ordenada por nome). Cobertura de plano é **piso** ("no mínimo"),
  porque a ANS conta vínculos. Ids do ano da tabela 7362 fixos em `ANOS_7362` (a API de metadados do IBGE dá timeout no GitHub).
- 2026: 53,1 mi de vínculos de plano (24,8% da população) → 75,2% só no SUS; União R$ 216,0 bi, estados R$ 193,0 bi, prefeituras
  R$ 313,6 bi (2025); esperança de vida 78,0 anos (projeção). Pendências: SIOPS (recursos próprios), CNES/leitos (API do MS
  recusa conexão), atenção básica, filas.

## Página /conferir/ e painel Dívida (29/10/2026)
- Pergunta do dono — "como saber se esse dado não é maquiado?" — **para o site inteiro**. Virou `/conferir/`, ligada no **rodapé
  de todas as páginas** (não entrou no menu) e no topo da metodologia. Conteúdo em `site/src/lib/conferencias.ts`: CHECAGENS
  (cada conferência contra outra fonte, com selo bate/explicada/**não explicada**), REGRAS, LIMITES e CORRECOES (registro das
  correções já feitas, com data e como apareceram). Os números do nosso lado são **lidos dos JSONs**, não digitados. Duas
  conferências terminam sem explicação (estatais × MGI, SIOP × Portal) e continuam publicadas assim.
- **Painel Dívida** `/divida/` (menu depois de Poderes — 33º item), `etl/divida/extract.py` → `divida.json`, mensal dia 20.
  Resolve a confusão dos **três números**: juros nominais do Governo Central (Tesouro, RTN aba **2.1**, linha "9. JUROS
  NOMINAIS", **desde 1997**; 2025 = R$ 891,9 bi), juros e encargos pagos no Orçamento (SIOP, R$ 362,7 bi) e amortização
  (R$ 1,77 tri, que é **rolagem, não custo**). O "R$ 1,1 tri" que circula é do **setor público consolidado** (BCB), não do
  Governo Central — declarado na página. Estoque da DPF pelo CSV por título (set/2017→, 12 MB): ago/2026 R$ 12,22 tri, 47,9%
  **Selic**, 24,5% prefixado, 24,0% IPCA; R$ 2,55 tri vencem até o fim de 2027. Indexador deduzido da família do título
  (LFT/NTN-B/NTN-C/LTN/NTN-F), mapeamento declarado em `INDEXADOR`.
- **Fotos de deputados e senadores**: a Câmara devolve **503** quando o navegador pede as 513 de uma vez (curl isolado dá 200) e
  a URL do Senado é **http** (bloqueada em página https). `etl/fotos/baixar.py` baixa uma vez, reduz a 96 px (2,3 MB no total)
  e grava em `site/public/fotos/<casa>/<id>.jpg` + manifesto `fotos.json`; o componente usa o manifesto para não gerar img
  quebrada. Os workflows da Câmara e do Senado baixam o que faltar e commitam `site/public/fotos`.
- `/comparacao/`: os 20 países de referência passaram a ser **nomeados** no próprio gráfico, com o critério e o aviso de que a
  lista é editorial (pedido do dono).

## Painel Desenvolvimento (NO AR; feito 29/10/2026)
- Pergunta do dono: "o país está se desenvolvendo ou estagnado?". `/desenvolvimento/` (menu antes de Comparação), **sem ETL
  próprio**: lê `rankings.json` + educação e saneamento. Sete indicadores novos entraram no `etl/rankings`: investimento
  (NE.GDI.TOTL.ZS), abertura comercial (NE.TRD.GNFS.ZS), internet (IT.NET.USER.ZS), energia elétrica (EG.ELC.ACCS.ZS),
  mortalidade infantil (SP.DYN.IMRT.IN), médio completo (SE.SEC.CUAT.UP.ZS) e trânsito (SH.STA.TRAF.P5).
- **A resposta que os dados dão**: melhorou quase tudo que se mede por pessoa (mortalidade infantil −80,3% desde 1985; médio
  completo 22,8%→61,7%; expectativa 64→76) e parou no que se mede por produção (produtividade **+30,6% em 34 anos**; investimento
  20,3%→**17,1% do PIB**, 143º de 174). **Perdeu posição relativa em 5 dos 12** indicadores com série comparável.
- Método: "melhorou/piorou" é decidido pelo campo `maior_melhor` do indicador, não por nós. A página diz explicitamente que
  **não atribui causa**.
- 29/10 (correção, achada ao fazer o gráfico): **percentil solto engana**. A lista de países cresce (energia elétrica: 98 em 1990
  → 215 em 2024) e o Brasil "subia 36 pontos" sem ter feito nada. `serie_de()` passou a calcular também `posicao_fixa`/
  `total_fixo` — posição dentro do **mesmo grupo de países** (os que têm dado no primeiro e no último ano da série). Com grupo
  fixo a melhora da energia elétrica é de 3 pontos, não 36. Os gráficos usam a fixa; a tabela mostra as duas.
- 29/10: `ANO_INICIO` do rankings foi de 1985 para **1960** (o dono pediu "desde 1988 ou até antes"); PIB, expectativa de vida,
  mortalidade infantil, investimento, abertura e defesa passam a ter série desde 1960. Gráfico **"Subiu ou caiu?"**: 7 indicadores
  ganharam posição (mortalidade infantil +18 pts, médio completo +16, expectativa +11) e 5 perderam (investimento −26, internet
  −23, CPI −20, produtividade −11, PIB por pessoa −6).

## Painel Economia (NO AR, sem chave, mensal dia 4; feito 29/10/2026)
- Pedido do dono: criar a aba e **consolidar** painéis para reduzir o menu. `etl/economia/extract.py` → `economia.json`,
  `/economia/`. Preenche o buraco que faltava: **PIB e crescimento**.
- Fontes: **SIDRA 6784** (Contas Nacionais Anuais: PIB corrente, per capita, população, variação em volume, 1996→2023),
  **SIDRA 5932** (trimestral, PIB a preços de mercado, categoria **90707**, 1996Q1→2026Q2), **BCB SGS 432** (meta Selic) e
  **RTN aba 2.1** (resultado primário **linha 8, "abaixo da linha"** — a 5 é acima da linha e a 7 é discrepância
  estatística; o nominal é a linha 10).
- **Armadilhas do SGS**: recusa janela > 10 anos em série diária (HTTP 406) → coleta em fatias de 9 anos; e devolve 502 ou
  **HTML com status 200** de forma intermitente → `_sgs_janela` com 4 tentativas e checagem de content-type. Guardamos só os
  dias em que a meta mudou (162 desde 1999; pico 45% em 05/03/1999, hoje 13,75%).
- 2023: PIB R$ 10,94 tri, R$ 51.694 por habitante; a economia encolheu em 4 dos 28 anos. 2025: primário −R$ 58,7 bi,
  nominal −R$ 950,6 bi. A página é também porta de entrada (cartões) para Impostos, IR, Inflação, Dívida, Trabalho, Renda,
  Inadimplência, Estatais e Desenvolvimento. 29/10, o dono: "não estou vendo a aba economia" → **Economia entrou no menu**, depois de Estatais (só o
  item, sem mexer em mais nada; o menu foi a 36 itens em 4 linhas). A proposta de consolidação 35 → 29, já enviada
  por imagem, continua esperando o sim dele.

## Indústria — seção de Desenvolvimento (29/10/2026)
- Pergunta do dono: "estamos industrializando ou perdendo indústrias nos últimos 50 anos?". `etl/industria/extract.py`
  → `industria.json`, seção em `/desenvolvimento/`, mensal dia 17. Sem painel novo (o dono quer menos abas).
- **A armadilha, e foi ela que definiu o painel**: `NV.IND.MANF.ZS` existe desde 1960, mas é a **preços correntes** —
  dá **46,1% em 1979 e 22,0% em 1980**. Sob hiperinflação a participação setorial mede preço relativo, não produção.
  Gráfico começa em **1995** (`ANO_CONFIAVEL`), a série inteira fica no JSON e a página explica por quê. Não dá para
  atender os "50 anos" com esse indicador, e a página diz isso em vez de publicar o número bonito de 46%.
- Quatro medidas de propósito: participação (WB), **manufaturados nas exportações** (`TX.VAL.MANF.ZS.UN`, 1962→, é
  razão em dólar e sofre menos com inflação interna — é ela que dá o arco longo), emprego (`SL.IND.EMPL.ZS`, OIT) e
  **produção física** (IBGE PIM-PF, SIDRA **8888**, índice 2022=100, sem preço na conta).
- **O resultado contraria o senso comum**: pela participação no PIB o Brasil caiu **menos** que os países de renda alta
  desde 2000 (−1,0 p.p. contra −5,2). A perda aparece na **produção física** (pico 2013 = 119,9; hoje 102,3, −14,6%, e
  só +9,3% sobre 2002), nas **exportações** (manufaturados 58,7% em 1993 → 23,8%) e na **tecnologia**
  (`NV.MNF.TECH.ZS.UN` 51,0% em 1995 → 31,9%). O indicador mais citado é o mais fraco dos quatro.
- Armadilhas no código, com teste: o Banco Mundial publica **0,00** onde não há dado (zero não é participação) e o
  agregado de renda alta vem com `countryiso3code` vazio (casa por `country.id` = XD). Produção física: só ano com
  12 meses entra na média; o ano em curso vai para `parcial`.

## Endividamento de risco — seção de Inadimplência (29/10/2026)
- O dono mandou uma notícia do g1 ("endividamento de risco cresce 75%") e perguntou se os nossos dados iam na contramão.
  **Não iam**: a nossa inadimplência de PF subiu de 3,97% (jan/2025) para 6,19% (ago/2026), mesma direção. Virou seção.
- **Fonte primária = REF do BC, volume 25, out/2026** (PDF, 13 MB, `data/raw/bcb_ref_202610.pdf`): 20,3 mi de pessoas =
  **17% dos devedores do SFN** em jun/2026, +75% sobre jun/2021 (p. 77, com a série semestral do Gráfico 2.3.1, 11 pontos);
  definição na **nota 70 da p. 72** — é endividado de risco quem atende a **dois ou mais** de quatro critérios (atraso >90 d;
  >50% da renda no serviço da dívida; sobra abaixo da linha de pobreza; cheque especial + pessoal não consignado + rotativo
  ao mesmo tempo). Tomadores por faixa de renda no Boxe 3, p. 37–38 (até 2 SM: 61,2 mi de 95,4 mi).
- **Minha hipótese inicial estava errada** e está registrada aqui para não se repetir: supus que os 20,3 mi fossem a *união*
  dos quatro critérios e os 4,6 mi do estudo de 2023 a *interseção*. É "dois ou mais" — li a nota de rodapé do PDF.
- **Não publicamos os 42% da renda de quem ganha até 2 SM** que a imprensa citou: no relatório esse valor só existe como
  rótulo do Gráfico 1.2.2.12, e ler número de gráfico é régua. Em lugar disso entraram as séries agregadas equivalentes,
  que têm API: **SGS 29034** (comprometimento, mar/2005 17,0% → ago/2026 **28,99%**) e **29037** (endividamento,
  jan/2005 16,51% → **50,11%**) — as duas no **máximo da série**, e são as mesmas que o REF cita.
- Números do PDF ficam em `site/src/lib/endividamento.ts` (constante declarada com página e data de leitura, padrão de
  `comparacao.ts`); as séries do SGS entraram no `etl/credito/extract.py` (`familias`, com as 4 tentativas do SGS).
- Armadilha de CSS: `<b>` dentro do `<span>` de um `.stat` herda a fonte-herói e vira texto gigante — usar texto puro.
- Glossário: `endividamento_risco`, `comprometimento_renda`, `superendividamento`. `/conferir/` ganhou a linha das duas
  medidas subindo juntas e o limite "não há endividamento de risco por estado".

## Poder de compra — subpágina de Economia (NO AR, sem chave, mensal dia 18; feito 29/10/2026)
- Pedido antigo do dono ("quantas horas de trabalho para comprar TV, geladeira, carro; e o motivo seria o imposto?").
  `etl/precos/extract.py` → `precos.json`, `/economia/poder-de-compra/`. **Subpágina de propósito**: o dono pediu menos
  abas, então não entrou no menu — é cartão em `/economia/` e link no bloco de poder de compra de `/inflacao/`.
- **ANP, Sistema de Levantamento de Preços**: duas planilhas contíguas e de mesma definição (`mensal-brasil-2001-a-2012`,
  jul/2001→dez/2012, e `mensal-brasil-desde-jan2013`) + `mensal-estados-desde-jan2013`. O cabeçalho **não** está em linha
  fixa (acha-se a linha cujo primeiro campo é "MÊS"); "ÓLEO DIESEL" × "OLEO DIESEL" casa sem acento; a aditivada (só
  2013+) fica fora. As observações acima do cabeçalho vão para o JSON e para a página: **sem pesquisa de 18/8 a
  17/10/2020**, 85% menos postos na greve de 2018, abrangência 501→459 municípios em 2017.
- **Denominador** (foi a decisão que moldou tudo): série longa no **salário mínimo ÷ 220 h** (valor de lei, exato por mês,
  CLT art. 58 e 64). O rendimento da PNADC (**SIDRA 5436 v5933** ÷ **6371 v8190**, mesmo universo) é **real a preços do
  último trimestre** → só no retrato atual e no mapa, nunca na série. Hora do SM R$ 7,37; hora média R$ 21,62 (2026Q2).
- Resultados: gasolina **123 min (jul/2001) → 53 min**; pior mês fev/2003, 147 min. Botijão 21h → 15h31. **Diesel S10 foi
  na direção oposta** (47 → 58 min desde dez/2012). Mapa por UF usa a hora do próprio estado: MA 27,1 min × DF 11,3 min.
- **Comparação internacional = ICP do Banco Mundial** (fonte **90** da API de `sources`, dimensões Country/Series/
  Classification/Time; `PX.WL` = nível de preços, mundo = 100; ano de referência **2021**). Só a rodada 2021 — a de 2017
  (fonte 78) republica os mesmos anos com outro vintage. O **preço relativo** (categoria ÷ PIB do mesmo país) é conta
  nossa e é o que permite comparar países de renda diferente.
- **O achado**: o Brasil é barato no geral (nível 69,8 contra 158,5 dos EUA; 44% do preço americano, confirmado pela razão
  PPP÷câmbio, 45,7% em 2025) — mas **máquina e equipamento 1,59× e compra de veículo 1,43×** o nível local, contra 0,88×
  e 0,89× na mediana dos outros 20 países. **Contra a intuição: geladeira (1,00×) e TV/eletrônicos (0,99×) estão na
  linha** — custam mais horas aqui pela renda (consumo por habitante 10,1 numa escala em que os EUA são 100), não pelo
  preço relativo. A página publica isso ao lado da carga sobre bens e serviços (43,5%; 13,0% do PIB × 10,5% na OCDE) e
  **não escreve que o imposto é a causa**.
- Indicadores **arquivados** no Banco Mundial (não usar): `EP.PMP.SGAS.CD` (preço da bomba por país), `PA.NUS.PPPC.RF`
  (nível de preços pronto) → o nível de preços é calculado por nós com `PA.NUS.PPP` ÷ `PA.NUS.FCRF`.
- Sem painel próprio, com motivo: preço de produto por país (nenhum órgão publica), preço médio de alimento em reais
  (IBGE publica variação, não preço), abertura do preço do carro em imposto/insumo/margem (só institutos privados).
  Metodologia: seção "Poder de compra" em `metodologia.md`. Glossário ganhou 4 termos.

## Comparação com o mundo em Desenvolvimento (29/10/2026)
- Pedido do dono: "o que melhorou deveria ser comparado com o que melhorou no mundo". `rankings.json` ganhou
  `agregados` — séries dos grupos que o **próprio Banco Mundial** publica: WLD (Mundo), HIC (renda alta), LMY (renda
  média e baixa) e LCN (América Latina), para 11 indicadores (`COMPARAR_COM_O_MUNDO`).
- **Armadilha**: o grupo "renda alta" volta com `countryiso3code` **vazio**; é preciso casar pelo `country.id` (XD).
  Sem isso o HIC some em silêncio.
- As tabelas "o que melhorou/piorou" ganharam três colunas com a mesma variação no mesmo período. O que aparece:
  mortalidade infantil **−90,3% no Brasil × −56,7% no mundo** (remada), mas renda por pessoa **+250% × +358% no
  mundo** (maré que o Brasil não pegou). Quando o grupo não tem o ano inicial, usa-se o mais próximo e a dica mostra.

## Eficiência — seção de Desenvolvimento (29/10/2026)
- O dono perguntou se devia virar aba própria; escolheu **seção em `/desenvolvimento/`** ("Quanto custa e o que entrega").
  Três pares com dado dos dois lados: educação (gasto por aluno × % com médio completo, internacional), saúde (gasto público
  %PIB × expectativa de vida e mortalidade infantil) e **segurança por estado** (SICONFI função 06 por habitante × homicídios
  ODS 16.1.1) — este último é um **scatter dos 27 estados**, sem linha de tendência **de propósito**.
- Regra escrita na página: **não é nota de eficiência**. Não dividimos gasto por resultado (resultado vem de décadas, preço
  unitário muda por lugar, ponto de partida importa). Judiciário e obras entram só como limite declarado, porque o resultado é
  declarado pelo próprio órgão interessado.
- Armadilha de código: `import estados` colidiu com `const estados` já existente na página e o bloco sumiu em silêncio (o
  Astro não acusou). Renomeado para `despesaEstados`.

## Desenvolvimento por estado (29/10/2026)
- Pedido: "mapa para ver quais estados se desenvolveram mais desde 1988". `etl/desenvolvimento/extract.py` →
  `desenvolvimento.json`, mensal dia 11. **Três dimensões com série estadual comparável**: educação (Censos 142/1974/3547/10141
  por UF, % de 25+ com médio completo ou mais, 1991→2022), saneamento (vem do `saneamento.json`) e homicídios (**ODS 16.1.1**,
  tabela 6606, var **13532**, 2000→2024). Três mapas de **variação** (não de nível) + tabela.
- **Fora, com motivo na página**: renda desde 1991 (Censo de 1991 em **cruzeiro**, cinco trocas de moeda — conversão seria
  estimativa), emprego formal (quebras de RAIS/CAGED) e saúde por UF antes de 2000.
- Destaques: todos os 27 estados avançaram em escolaridade (RR 13,8%→56,2%); SP caiu de 41,0 para 6,2 homicídios/100 mil.

## Painel Trânsito (NO AR, sem chave, mensal dia 9; feito 29/10/2026)
- Pergunta do dono: "mortes no trânsito seria em segurança ou transporte?" → **painel próprio** `/transito/` (menu depois de
  Segurança), porque morte no trânsito **não é intencional** e somá-la ao MVI inflaria a violência; as duas aparecem lado a lado.
- `etl/transito/extract.py` → `transito.json`: **SIDRA 4408** (indicador ODS 3.6.1, do **SIM/Ministério da Saúde**), óbitos (v
  11728) e taxa (9734), **2000→2024**, por sexo (c2), faixa de idade (c58) e UF. 2024: **37.150 mortes** (17,5/100 mil), 102 por
  dia, 82,4% homens; pico em **2012** (44.812); TO 38,7 × RJ 7,8.
- **Duas contagens oficiais que não batem**: atestado de óbito 37.150 (2024) × registro policial do Sinesp 25.074 (2025) — o
  policial fica **32% abaixo**; parte é quem morre depois no hospital, o resto não sabemos medir. Virou linha de `/conferir/`.
- Internacional pela **estimativa da OMS** (`SH.STA.TRAF.P5`, entrou no `etl/rankings`): Brasil 16,0 (2019) — não bate com o
  atestado de óbito de propósito, e a página explica.

## Painel Saneamento (NO AR, sem chave, mensal dia 8; feito 28/10/2026)
- Pedido do dono: "aba de saneamento, evolução desde 1988, e como saber se o dado do governo não é maquiado?".
- `etl/saneamento/extract.py` → `saneamento.json`, `/saneamento/` (menu depois de Saúde — 32º item). **IBGE/SIDRA**, duas pesquisas
  nunca emendadas: **Censo** (água 179/1442/3391/6804, esgoto 180/1444/1394/6805, lixo 182/1447/—/6892) e **PNAD Contínua**
  (água 9468 + total 6731, esgoto 7192). 1991: água 70,7%, esgoto 35,3%, lixo 63,8% → 2022: 83,9%, 60,4%, 91,7%; PNADC 2025:
  86,1% e 65,0%.
- Armadilhas: **PNADC vem em mil unidades** e o Censo em unidades; a coluna "(Código)" tem o mesmo prefixo da coluna do rótulo
  (pegava o código no lugar de "Total" e zerava tudo); tabela sem classificação quebra se mandar `/c1/all` (9468); em tabela com
  mais de uma classificação só soma a linha com **as outras no Total**. **Sem 2020 e 2021** (pandemia): a linha é quebrada, não
  interpolada. **Censo 2010 não tem lixo** nesse recorte. Categoria "rede geral" muda a cada Censo e está no JSON — a 46290 de 2022
  (que soma fossa ligada à rede) daria 64,7% em vez de 60,4%.
- **Resposta ao "é maquiado?"**: Censo 2022 (universo) × PNADC 2022 (amostra) no mesmo ano — esgoto 60,4% × 62,7%, água 83,9% ×
  85,5%, com CV de 0,2% publicado pelo IBGE → a diferença é de definição, não de acaso; total de domicílios bate em 0,3%. Mais: a
  categoria somada está publicada por número, e IBGE pergunta ao morador enquanto o SNIS recebe declaração do prestador.
- Dinheiro: **função 17** entrou no `etl/municipios/transform.py` (`pago_saneamento` em municípios e estados, do DCA em cache) e
  vem do SIOP para a União. 2025: prefeituras 25,4 bi, estados 4,1 bi, União 0,2 bi — **não somar como investimento do país**: a
  obra das companhias estaduais corre por tarifa e financiamento (ver `/estatais/`).
- **SNIS fora, com motivo**: a Série Histórica (`app4.cidades.gov.br/serieHistorica`) é app Yii com POST e sem rota documentada;
  parei a raspagem em vez de apoiar o painel nela. Caminho tratável: arquivos estáticos do Diagnóstico anual. Sem SNIS, não há
  **esgoto tratado**, perdas de água nem investimento por prestador — declarado na página.

## Painel Histórico (NO AR, sem chave, mensal dia 6)
- `etl/historico/extract.py`: SIOP por função, 1 grafo por ano desde 2000 (26+ consultas SPARQL); IPCA SIDRA 1737/2266
  (índice de dezembro → `deflator[ano]` para reais do último ano fechado); BEPS tabela 14 (dezembro de cada ano); receita vem
  de `impostos.json`. Saída `historico.json` com nominais; a página deflaciona. `/historico/` + tabela "até onde cada fonte volta"
  (também na Metodologia). Pendentes: Finbra 1989–2012, CPGF 2003+, CEAP 2008+, PNAD anual.

## Painel Trabalho (NO AR, sem chave, mensal dia 5)
- `etl/trabalho/extract.py`: IBGE SIDRA (6318, 4097, 6381), Mapa de Empresas (xlsx do gov.br/memp, aba NJ × porte), BEPS
  tabela 14 (xls via xlrd; anos como texto a partir de 2016; células mescladas). Saída `trabalho.json`; página `/trabalho/`.
  Pendentes: Bolsa Família (API do Portal por município ou CSV de 330 MB), optantes do Simples.
- 27/10 (tarde): **CEMPRE** (SIDRA 7528) entrou no `trabalho.json` — empresas, pessoal e salário médio por faixa de pessoal ocupado,
  mais `portes` (micro/pequena/média/grande pelo critério **Sebrae por pessoal ocupado**, aplicado seção a seção da CNAE: corte alto
  em indústria/construção, baixo em comércio/serviços). A lei (LC 123) classifica por faturamento — a página diz que são critérios
  diferentes. 2024: 94,2% micro, 0,4% grandes com 47,3% do pessoal.
- 27/10 (tarde): pizza **"quem sustenta a previdência"** (SIDRA 5947): 68,4 mi contribuem (31,9% da população), 34,6 mi trabalham sem
  contribuir, 5,8 mi procuram, 66,4 mi fora da força, 39,0 mi crianças. Partição real; não serve para "X sustentam Y" (aposentado
  já contribuiu) e a página diz isso.
- Home usa "trilhões/bilhões/milhões" por extenso (pedido de 26/10); demais páginas mantêm "tri/bi/mi".
- 27/10: duas pizzas novas — **população total** (crianças ≤13 por diferença IBGE−PNAD, ocupados, desocupados, fora da força;
  partição real) e **benefícios do INSS** por grupo. Avisos: as duas pizzas não se somam (benefício ≠ pessoa; aposentado pode
  trabalhar) e 6318 × 4097 dão 103,5 e 103,1 mi por usarem trimestre móvel × fechado. `populacao` entrou no `trabalho.json` (SIDRA 6579).

## Painel Rankings (NO AR, sem chave, mensal)
- `etl/rankings/extract.py` → `rankings.json`: Banco Mundial API (PIB, PIB pc, expectativa, Gini, educação %PIB,
  homicídios/UNODC), PNUD HDR 2025 CSV (IDH 2023, posição oficial), TI CPI 2025 xlsx (leitor xlsx próprio), nomes PT
  pelo IBGE. Posição calculada por nós nos do BM; oficial no IDH/CPI. Workflow `etl-rankings.yml` (dia 1, 06:37 BRT).
- 28/10: `_get` com 3 tentativas (o ETL caiu no runner com ConnectTimeout depois dos seis indicadores novos) e os nomes
  de país **congelados** em `etl/rankings/paises_pt.json` (193 países): a API de localidades do IBGE recusa os runners,
  como já acontece com o SIDRA de metadados. A API só atualiza o arquivo quando responde e traz ≥90% dos nomes.
- Pendentes sem arquivo aberto: Heritage (liberdade econômica), Freedom House (sem planilha gratuita), PISA (SDMX
  OCDE), Global Peace Index. Metodologia: `docs/metodologia/painel-rankings.md`.
## Painel Comparação internacional (NO AR; feito 28/10/2026)
- `/comparacao/` (menu antes de Rankings), sem ETL próprio: lê `rankings.json`, `impostos.json` e `poderes_funcao_2025`.
  Seis indicadores de gasto entraram no `INDICADORES_WB` do `etl/rankings/extract.py`: saúde pública e total, defesa,
  despesa do governo central, transferências/benefícios (% da despesa) e receita tributária do governo central.
- Brasil × mediana de 20 países de referência (lista nossa, declarada). 2026: educação 5,6% do PIB (mediana 5,0),
  saúde pública 4,3% (mediana 6,4), saúde total 9,7%, defesa 1,1%, despesa do governo central 32,4%, transferências
  62,8% da despesa. **A armadilha da carga**: o Banco Mundial mede só o governo central (15,4% do PIB) e a Receita mede
  os três níveis (32,2%) — a página explica, com a tabela INC 01-A ao lado.
- 28/10 (2ª rodada): **Judiciário comparado e custo das Coroas** em `site/src/lib/comparacao.ts` (constantes com fonte,
  página e data, como `beneficios.ts`). Brasil 1,3% do PIB (CNJ, Justiça em Números **2026**, ano-base 2025; R$ 164,6 bi;
  R$ 771,48/hab; 19.094 magistrados, 8,95/100 mil) × mediana europeia de **0,186%** (CEPEJ, dados de 2022 — o ciclo com
  2025 não saiu). **O pareamento é o ponto**: CNJ mede só tribunais; CEPEJ e Eurostat incluem MP e assistência
  judiciária, então usar o total europeu seria erro de construção. Por habitante inverte: R$ 771,48 = € 122 contra € 132
  da UE27, porque o PIB por habitante é menor — as duas leituras estão na página. Inativos (15,3%) não confirmados na
  Europa → publicamos 1,3% e 1,1%.
- 28/10 (ajuste do dono): o gráfico usa **média** (a mediana ficou estranha para ele) e a nota traz a mediana como
  conferência — as duas ficam a <1 ponto em todas as áreas. E a Coroa passou a ser comparada com a **Presidência da
  República** (chefe de Estado), não com o Judiciário: R$ 1,87 bi a unidade, R$ 3,36 bi o órgão com ABIN e EBC; o
  Congresso (Câmara 7,03 + Senado 5,86 = R$ 12,88 bi) ganhou seção própria.
- **Parlamentos (28/10)**: `PARLAMENTOS` e `CONGRESSO_BR` em `comparacao.ts`, dez países, **só as duas casas** (sem
  tribunal de contas, ombudsman, biblioteca — cada país põe coisa diferente na rubrica). Ranking em reais: EUA 18,9 bi,
  **Brasil 12,9 bi**, Itália 8,6, Alemanha 7,6, França 5,9, Reino Unido 5,6, Japão 3,9, Países Baixos 1,7, Suécia 1,5,
  Portugal 1,1, Espanha 1,0. **Eixo que mais distorce: inativos dentro da rubrica** — Camera italiana 47%, Congresso BR
  38% (Senado 45%, Câmara 32%), EUA zero (lá até o salário do congressista corre em outra lei) → publicamos também
  R$ 7,97 bi sem inativos. Denominadores quebrados que NÃO servem para dividir: Bundesrat (69 ministros estaduais) e os
  797 lordes (ajuda de custo por presença). Espanha está com PGE de 2023 prorrogado 3×.
- Monarquias: 8 países com documento oficial próprio (UK realizado/auditado, NO e SE aprovados, DK e NL orçados, BE
  ajustado, JP submetido, ES prorrogado). **Não medem a mesma coisa**: BE inclui polícia de proteção (47% do total),
  NL deixa palácios fora (+€ 21,4 mi), DK conta só dinheiro a pessoas. Conversão pela PTAX do dia; `etl/cambio` passou a
  trazer as 10 moedas da PTAX (entraram DKK, NOK, SEK) e `rankings` ganhou `populacao` (SP.POP.TOTL) para o per capita.

- 29/10 (o dono: "essa média não deveria ser ao longo de 30 ou 50 anos?"): `rankings.json` ganhou `medias_longas` — média de
  **25 anos** por país dos 8 indicadores de gasto, com `anos`/`de`/`ate` por país (cobertura desigual: Brasil 20 anos, EUA 7).
  Cada barra de `/comparacao/` mostra a média como traço vertical. Em educação a conclusão não muda: Brasil 5,5% na média de 20
  anos × 4,8% dos outros.
- 29/10 (o dono: "5,6% do PIB em educação **não traduz a realidade**" — não traduz mesmo): entrou **gasto por aluno em US$ PPP**,
  calculado no `etl/rankings` como `SE.XPD.PRIM.PC.ZS/100 × NY.GDP.PCAP.PP.CD` **do mesmo ano e país** (helper `_serie_por_ano`),
  mais `criancas_pct` (SP.POP.0014.TO.ZS). Brasil **US$ 2.972/aluno (2015)** × Coreia 11.605 × Alemanha 8.993, embora o Brasil
  gaste mais % do PIB. Explicação: PIB por habitante menor + 19,4% da população com até 14 anos (Coreia 10,2%). Ano antigo e
  variável por país (a série da UNESCO parou) — declarado na barra de cada país.
- 29/10: o **Brasil entrou na tabela das monarquias** (Presidência da República, R$ 1,87 bi, R$ 8,80/hab) — sem a linha dele
  não dava para comparar de olho. Com a ressalva na própria nota: a Presidência é órgão de governo com milhares de servidores,
  a dotação das coroas cobre sobretudo a casa real; está lá porque é o cargo correspondente (chefe de Estado).
- 29/10 (pedido do dono): seção **"Violência: o Brasil, os outros países e as guerras"** em `/comparacao/`. Homicídios do
  Brasil (19,3/100 mil, UNODC 2023, 18º maior de 149) numa lista só com os 5 piores do mundo e os de referência. Conflitos em
  `CONFLITOS` (comparacao.ts), **só com fonte de órgão da ONU** e com o que cada número NÃO conta: Gaza 72.045 (OCHA citando o
  MS de Gaza, civis + combatentes, 1.393/100 mil/ano ≈ 75× o Brasil) e Ucrânia 16.874 (OHCHR, **só civis verificados**, sem
  militares → 9,4/100 mil/ano, metade do Brasil — e a página diz por que isso não significa "Brasil pior que a guerra").
  `SEM_TOTAL_OFICIAL` lista Sudão/Congo/Mianmar/Haiti, onde a ONU não publica total.
- Visual: `accent` por página (prop do `Base.astro`): deputados s1, senadores s3, STF s5, emendas s4, poderes s2, rankings s5.

## Benefícios (site)
- `BeneficiosBox.astro` recolhível em cada painel (abaixo do aviso); `/beneficios/` compara as três casas + ex-presidentes (fora do menu).
- `site/src/lib/beneficios.ts`: lista fixa por casa (deputados, senadores, STF) + ex-presidentes, cada linha com valor/
  regra, uso por pessoa, "no custo", fonte, URL e data. Sem API. Metodologia: `docs/metodologia/painel-beneficios.md`.
- Ex-presidentes: Lei 7.474/1986 (8 servidores + 2 carros, sem salário); dataset da Presidência
  (`dadosabertos.presidencia.gov.br`, "custo-de-ex-presidentes") estava fora do ar em 26/10/2026 — carregar quando voltar.
- Tabelas do site ordenam por clique no cabeçalho (script inline em `Base.astro`; única exceção ao "zero JS").

## Glossário e filtros (site)
- `site/src/lib/glossario.ts` + `<Termo t="…">` (dica ⓘ em CSS, sem JS) + `<Glossario termos=[…]>` no fim de cada página.
- Emendas: autores casados com deputados + senadores da legislatura (`etl/portal_transparencia/nomes.py`: exato →
  aproximado por tokens, único candidato). 2025: 590/592 autores identificados; página mostra em exercício × fora.

## Painel Poderes (NO AR, dados reais 2025 — todos os Poderes)
- Fonte: **SIOP, SPARQL público** `https://www1.siop.planejamento.gov.br/sparql/`, grafo
  `http://orcamento.dados.gov.br/<ano>/` (sem chave; 1 consulta agregada órgão × UO × GND, ~1.200 linhas, ~10 s).
  `etl/portal_transparencia/extract_poderes.py` → `despesas_orgao_<ano>.jsonl.gz`; transform gera `poderes_`,
  `poderes_orgaos_` (por unidade orçamentária) e `poderes_gnd_<ano>.json` (Poder × GND, ainda sem página).
- **Por que não o Portal da Transparência**: `/despesas/por-orgao` é documentada no OpenAPI como "despesas dos
  órgãos do Poder Executivo Federal" — Legislativo/Judiciário/MPU/DPU nunca vêm, com qualquer código. O CSV anual
  "Orçamento da Despesa" do Portal tem a mesma cobertura. (Era o "bug" de 26/10/2026; resolvido trocando a fonte.)
- 2025 pago: Executivo R$ 2,04 tri (sem dívida/transferências), Judiciário 63,9 bi, Legislativo 15,7 bi,
  Funções essenciais 10,6 bi, Dívida/Transferências 2,92 tri (71000–75000 + 90000). Previdência 986 bi.
- Classificação em `classificar()`; metodologia em `docs/metodologia/painel-poderes.md`. SIOP já tem grafo 2026.
- 27/10 (pedido do dono, a partir do painel "Despesas Públicas do Governo Federal" do Portal): a página abre com
  **orçamento atualizado × empenhado × pago** do ano fechado e do ano em curso (`dotacao` e `liquidado` entraram no
  `SQL_PODERES` do transform; `poderes_*_2026.json` gerados). 2026: dotação 6,53 tri, empenhado 5,53, pago 4,94 (3,05 de
  dívida/transferências → 1,89 tri sem elas). 2025: 5,84 / 5,38 / 5,05 (2,92 → 2,13 tri). O texto explica por que o total
  passa do PIB (refinanciamento + transferências contadas duas vezes) e que o PIB dos rankings está **em dólares**
  (US$ 2,28 tri) — era a dúvida do dono. **Divergência não explicada com o Portal** (6,43 e 4,76 tri lá; Siafi × SIOP,
  1,6% e 3,8%; não é a reserva de contingência, que são 13,1 bi) declarada na página e na metodologia §7.
- A página usa `new Date().getFullYear()` para o ano em curso: se o JSON do ano não existir, a coluna simplesmente não
  aparece. Gerar com `python -m etl.portal_transparencia.extract_poderes --ano <ano>` + `transform_poderes --ano <ano> --populacao 212600000`.
- Página mostra **"Manter a máquina" × políticas públicas**: categoria = Programa de Gestão e Manutenção da LOA
  (0031–0035) vs finalísticos vs 09xx encargos especiais; subcategoria por GND/ação (ativos, aposentados, custeio,
  investimento) em `poderes_categoria_<ano>.json`. 2025: máquina Executivo 309 bi, Judiciário 62,3 bi, Legislativo
  15,4 bi, MPU/DPU 9,9 bi. Metodologia §3b.

## Painel Emendas (página pronta; ver estado do run 2025 abaixo)
- `/emendas?ano=` funciona; campos confirmados: codigoEmenda, ano, tipoEmenda, autor, nomeAutor, numeroEmenda,
  localidadeDoGasto, funcao, subfuncao, valorEmpenhado/Liquidado/Pago, valorResto{Inscrito,Cancelado,Pago}
  (strings pt-BR "8.000,00"). `nomeAutor` pode ter sufixo "(EX-PARLAMENTAR …)" — transform corta no parêntese.
- `/emendas/documentos` é **restrito (403)** para a chave comum → destino por município/favorecido virá do
  CSV "Emendas parlamentares" em download-de-dados (sem chave) ou TransfereGov. Ainda não implementado.
- Bug de 26/10/2026 corrigido: o passo rodava o transform da Câmara inteiro (exigia `ceap_bulk_2026`) para ter
  `deputados.parquet`. Agora `transform_emendas` usa o parquet se existir, senão `deputados_leg57.jsonl.gz`
  (só `extract deputados`, sem CEAP). Teste sintético em `tests/test_portal.py`.
- Regras: emenda NÃO soma ao custo do deputado; "recebeu" = pago, "alocou" = empenhado; só individuais
  (RP6) têm autor único.

## Próximos passos combinados
1. Senado: custo do gabinete por senador via folha de servidores (lotação); teto CEAPS por UF; auxílio-moradia com fonte.
   STF: composição da remuneração; replicar para STJ/TST/TSE/CNJ.
2. Página por deputado `/deputado/{id}` (foto, cota mês a mês, categorias, fornecedores, link da NF) — maior
   ganho de SEO e o link para os comentários do Instagram.
3. Painel "No que gastaram" (categorias) e fornecedores em rede.
4. Obras: feito em 27/10/2026 (ver seção do painel). Falta reconciliar a contagem com o relatório de obras paralisadas do TCU
   (abr/2025: 11.469 de 22.621) e buscar valor liquidado/pago por obra, que o CIPI não publica.
5. `etl/camara/validate.py`: invariantes (513±, liquido = documento − glosa, total ≥ 95% do run anterior),
   reconciliação api × bulk × total oficial, falhar o job antes de commitar dado ruim.
6. Judiciário fase 3: TCU e os seis TRFs no molde de `etl/tribunais/`; série histórica (STJ desde 2020, STM desde 2013);
   Justiça em Números do CNJ; TJs estaduais via SICONFI (função 02).
7. DNS: adicionar `www` como custom domain no Pages; TXT anti-spoofing (SPF `v=spf1 -all`, DMARC `p=reject`).

## Descoberta / SEO (feito 27/10/2026)
- `@astrojs/sitemap` → `/sitemap-index.xml` (5.622 URLs; prioridade 0.9 painéis, 0.6 filtros UF/partido, 0.4 municípios);
  `public/robots.txt` libera tudo (decisão do dono: crawlers de IA bem-vindos, nada bloqueado).
- JSON-LD no `Base.astro`: `WebSite` na home; `Dataset` (schema.org, CC BY, `distribution` → `/data/*.json`, `isBasedOn` → fonte
  primária) resolvido pela rota a partir de `site/src/lib/datasets.ts`; subpáginas herdam o do painel-pai. **Painel novo = uma
  entrada em `datasets.ts`** (nome, descrição, arquivos, fontes, período, cadência) — alimenta também a página `/dados/` (catálogo).
- Google Search Console: domínio verificado por TXT no DNS (não remover o registro); sitemap enviado em 27/10/2026.
  Pendente: Bing Webmaster Tools ("Import from GSC"); testar rich results em search.google.com/test/rich-results.
- Analytics da Cloudflare conta bots (picos de 5 mil pageviews = crawler varrendo os municípios); para humanos, Web Analytics
  (beacon) ainda não ligado.

## Painel Agora (ao vivo; feito 28/10/2026)
- **Única página que não publica dado de órgão público**: mostra o movimento do próprio site. `/agora/` + menu antes de Dados.
- Infra nova no repo: `wrangler.toml` (Pages com `pages_build_output_dir = "site/dist"`), `functions/api/e.js` (recebe o
  sinal), `functions/api/agora.js` (agrega, cache de 20 s), `db/agora.sql`, `site/public/agora.js`, e um beacon inline no
  `Base.astro`. Deploy passou a ser `wrangler pages deploy` **sem diretório** (lê a config).
- **D1 é opcional por desenho**: o passo do deploy cria o banco `nossodinheiro-agora` se não existir, injeta o
  `database_id` no `wrangler.toml` (o bloco não fica no repo) e tem `continue-on-error`. Sem banco, o site publica igual
  e `/agora/` diz "indisponível"; o beacon responde 204 em silêncio.
- **Privacidade (o que está escrito na página)**: grava caminho, título, horário e **domínio** de origem. Não grava IP,
  cookie, user-agent nem aparelho. O id de sessão é aleatório, vive no `sessionStorage` e morre com a aba. Retenção de
  48 h, limpeza preguiçosa (1 em 200 gravações). Robôs filtrados por user-agent (lido, não gravado) e `navigator.webdriver`.
- Testado localmente com `wrangler pages dev` + D1 local: beacon 204, bot ignorado, agregados corretos (UF vem de
  `/municipios/<uf>/…`, partido de `/deputados/partido/…`, origem do referrer).
- `/sugestoes/` na mesma infra (`functions/api/sugestao.js`, tabela `sugestao`): grava texto, contato opcional, página
  e sessão; **nunca** IP/UA/cookie. Anti-robô por campo-armadilha escondido (descarta em silêncio respondendo ok) e
  limite de 3 por sessão/hora e 1 por 20 s. Funciona **sem JavaScript** (POST comum → 303 para `/sugestoes/obrigado/`).
  O site mostra só a **contagem** de 24 h, nunca o texto — publicar texto de terceiro exigiria moderação. Ler com
  `make sugestoes`. `/sugestoes/` entrou no menu depois de Agora.
- **O token da Cloudflare não tem permissão de D1** (deploy de 28/10 falhou com "Authentication error [code: 10000]" no
  passo do banco e seguiu sem o binding, como projetado). Enquanto não for adicionada a permissão **D1:Edit** ao token
  do secret `CLOUDFLARE_API_TOKEN`, `/agora/` e `/sugestoes/` respondem "indisponível" e o resto do site funciona igual.
- **Pendências**: duelos lado a lado (exige antes uma página de comparação entre dois parlamentares, que não existe);
  separar cidade de estado no agregado; amostrar quando passar de ~100 mil gravações/dia (limite do plano gratuito do D1).

## Convenções
- Nunca persistir o CPF do parlamentar que vem no CSV da CEAP.
- Todo número fixo em `config.py` com fonte e data; mudou lá → muda a metodologia na mesma PR.
- Rótulo explícito do que é gasto real vs teto vs projeção. Ano corrente: `meses_considerados = mês atual`.
- Commits: `feat|fix|ci|site|data: …`. O etl-bot commita só `data/public` e `site/public/data`.
- Logs do Actions: `gh run view <id> --log-failed`. Ambiente local: `.venv/` (python -m venv; `pip install -r requirements.txt`).
