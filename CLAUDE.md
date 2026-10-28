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

## Estrutura do site (26/10/2026)
- `/` = painel Geral (panorama: União por função via `poderes_funcao_<ano>.json`, três níveis via SICONFI, cartões dos painéis).
  Deputados mudou para `/deputados/`. `/judiciario/` = índice dos tribunais (SIOP) com link para `/stf/`; demais tribunais
  pendentes (mesmo molde do STF). Menu: Geral, Deputados, Senadores, Presidência, Judiciário, Emendas, Poderes, Estados,
  Municípios, Obras, Impostos, Imposto de Renda, Inflação, Trabalho, INSS, Aposentadoria, Renda, Educação, Segurança, Saúde, Inadimplência, Corrupção, Rankings, Histórico, Metodologia, Sobre. Pedidos na fila: painel "Presença e votações" (Câmara/Senado),
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
  Metodologia `docs/metodologia/painel-tribunais.md` §7. Próximos: TCU e os seis TRFs.

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
- Pendentes sem arquivo aberto: Heritage (liberdade econômica), Freedom House (sem planilha gratuita), PISA (SDMX
  OCDE), Global Peace Index. Metodologia: `docs/metodologia/painel-rankings.md`.
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

## Convenções
- Nunca persistir o CPF do parlamentar que vem no CSV da CEAP.
- Todo número fixo em `config.py` com fonte e data; mudou lá → muda a metodologia na mesma PR.
- Rótulo explícito do que é gasto real vs teto vs projeção. Ano corrente: `meses_considerados = mês atual`.
- Commits: `feat|fix|ci|site|data: …`. O etl-bot commita só `data/public` e `site/public/data`.
- Logs do Actions: `gh run view <id> --log-failed`. Ambiente local: `.venv/` (python -m venv; `pip install -r requirements.txt`).
