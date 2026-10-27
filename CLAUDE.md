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
- `etl-{renda,seguranca,credito}.yml` — mensais (dias 7, 9, 10); `etl-educacao.yml` só dispatch (INEP bloqueia o GitHub). `deploy.yml` — após qualquer ETL ou push em `site/**`. Usa secrets `CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_ACCOUNT_ID`.
Secrets existentes: os dois da Cloudflare + `PORTAL_TRANSPARENCIA_KEY`. Workflow permissions = read/write.

Comandos: `make test` (smoke test com fixtures sintéticas), `make etl ANO=2026` (FONTE=bulk padrão),
`make site`. Disparar workflow via REST (GraphQL bloqueado no gh):
`gh api -X POST repos/pereirawill/nossodinheiro.org/actions/workflows/etl-portal.yml/dispatches -f ref=main -f 'inputs[etapa]=poderes' -f 'inputs[ano]=2025'`

## Estrutura do site (26/10/2026)
- `/` = painel Geral (panorama: União por função via `poderes_funcao_<ano>.json`, três níveis via SICONFI, cartões dos painéis).
  Deputados mudou para `/deputados/`. `/judiciario/` = índice dos tribunais (SIOP) com link para `/stf/`; demais tribunais
  pendentes (mesmo molde do STF). Menu: Geral, Deputados, Senadores, Presidência, Judiciário, Emendas, Poderes, Estados,
  Municípios, Impostos, Trabalho, Renda, Educação, Segurança, Inadimplência, Rankings, Histórico, Metodologia, Sobre. Pedidos na fila: painel "Presença e votações" (Câmara/Senado),
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
- Site: `/stf/`. Metodologia: `docs/metodologia/painel-stf.md`. Próximo: STJ/TST/TSE/CNJ no mesmo molde.

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

## Painéis Renda, Educação, Segurança, Inadimplência (NO AR, sem chave, mensais dias 7–10; feitos 26–27/10/2026)
- `etl/ufs.py`: tabela fixa das 27 UFs (código IBGE, sigla, nome) + `normalizar()`; usada pelos quatro.
- **Renda** `etl/renda/extract.py` → `renda.json`, `/renda/`: SIDRA 4659 (rendimento por posição, Brasil série + UF), 7527/7530
  (massa por percentil), 7533, 7438 (limites P90/P99), 7535 (ocupados por percentil), 7435 (Gini). Público 5.301 × privado c/
  carteira 3.176 (2025); 1% com 11,0% da renda.
- **Educação** `etl/educacao/extract.py` → `educacao.json`, `/educacao/`: INEP zips `divulgacao_{brasil,regioes_ufs}_ideb_<ano>` e
  `divulgacao_<etapa>_municipios_<ano>` (openpyxl; md5 do zip conferido; TLS do INEP falha → retry sem verify + md5; abreviações
  "R. G. do Sul"). Município = rede pública. 2023 é a última edição (2025 sai em 2026). **INEP bloqueia runners do GitHub**
  (connection reset) → workflow só com dispatch; rodar local e commitar o JSON, como o STF.
- **Segurança** `etl/seguranca/extract.py` → `seguranca.json`, `/seguranca/`: MJSP Sinesp VDE `bancovde-<ano>.xlsx` (26 MB, servidor
  corta download → 4 tentativas; cache em data/raw), abrangência Estadual, eventos separados (sem MVI), vítimas × ocorrências,
  população SIDRA 6579 do mesmo ano; municípios ≥100 mil + capitais; série 2015+ por UF (baixa 11 arquivos, ~5 min).
  Roubo/furto/estupro/intervenção só por UF. dados.mj.gov.br não resolve DNS; gov.br/mj é a fonte.
- **Inadimplência** `etl/credito/extract.py` → `credito.json`, `/inadimplencia/`: BCB `bcb.gov.br/pda/desig/scrdata_<ano>.zip` (ano
  corrente + anterior, ~300 MB; CSV mensal, DuckDB), inadimplência = >90 dias ÷ carteira ativa, por UF/cliente/modalidade/porte;
  série 24 meses. Sem dado municipal (só UF; "sub-região" do BCB é codificada).
- `openpyxl` entrou em requirements. Glossário ganhou 14 termos (rendimento_habitual … modalidade_credito).

## Painel Histórico (NO AR, sem chave, mensal dia 6)
- `etl/historico/extract.py`: SIOP por função, 1 grafo por ano desde 2000 (26+ consultas SPARQL); IPCA SIDRA 1737/2266
  (índice de dezembro → `deflator[ano]` para reais do último ano fechado); BEPS tabela 14 (dezembro de cada ano); receita vem
  de `impostos.json`. Saída `historico.json` com nominais; a página deflaciona. `/historico/` + tabela "até onde cada fonte volta"
  (também na Metodologia). Pendentes: Finbra 1989–2012, CPGF 2003+, CEAP 2008+, PNAD anual.

## Painel Trabalho (NO AR, sem chave, mensal dia 5)
- `etl/trabalho/extract.py`: IBGE SIDRA (6318, 4097, 6381), Mapa de Empresas (xlsx do gov.br/memp, aba NJ × porte), BEPS
  tabela 14 (xls via xlrd; anos como texto a partir de 2016; células mescladas). Saída `trabalho.json`; página `/trabalho/`.
  Pendentes: Bolsa Família (API do Portal por município ou CSV de 330 MB), optantes do Simples.
- Home usa "trilhões/bilhões/milhões" por extenso (pedido de 26/10); demais páginas mantêm "tri/bi/mi".

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
4. Painel 4 Obras paralisadas: API pública Obrasgov `https://api-publica.obrasgov.gestao.gov.br` (CIPI; sem
   auth; situação/valor executado; API antiga válida até 31/08/2026). TCU abr/2025: 11.469 de 22.621 paradas.
5. `etl/camara/validate.py`: invariantes (513±, liquido = documento − glosa, total ≥ 95% do run anterior),
   reconciliação api × bulk × total oficial, falhar o job antes de commitar dado ruim.
6. Judiciário fase 2: remuneração de magistrados (CNJ), Justiça em Números; TJs via SICONFI.
7. DNS: adicionar `www` como custom domain no Pages; TXT anti-spoofing (SPF `v=spf1 -all`, DMARC `p=reject`).

## Convenções
- Nunca persistir o CPF do parlamentar que vem no CSV da CEAP.
- Todo número fixo em `config.py` com fonte e data; mudou lá → muda a metodologia na mesma PR.
- Rótulo explícito do que é gasto real vs teto vs projeção. Ano corrente: `meses_considerados = mês atual`.
- Commits: `feat|fix|ci|site|data: …`. O etl-bot commita só `data/public` e `site/public/data`.
- Logs do Actions: `gh run view <id> --log-failed`. Ambiente local: `.venv/` (python -m venv; `pip install -r requirements.txt`).
