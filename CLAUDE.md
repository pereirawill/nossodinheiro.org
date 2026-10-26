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
- `etl.yml` — Câmara. Segunda 06:17 BRT e em push em `etl/**`. Commita JSONs, dispara deploy.
- `etl-portal.yml` — Portal da Transparência. Terça 03:23 BRT (janela de 700 req/min). `workflow_dispatch`
  com inputs `etapa` (inspect | poderes | emendas | emendas-documentos) e `ano`.
- `deploy.yml` — após qualquer ETL ou push em `site/**`. Usa secrets `CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_ACCOUNT_ID`.
Secrets existentes: os dois da Cloudflare + `PORTAL_TRANSPARENCIA_KEY`. Workflow permissions = read/write.

Comandos: `make test` (smoke test com fixtures sintéticas), `make etl ANO=2026` (FONTE=bulk padrão),
`make site`. Disparar workflow via REST (GraphQL bloqueado no gh):
`gh api -X POST repos/pereirawill/nossodinheiro.org/actions/workflows/etl-portal.yml/dispatches -f ref=main -f 'inputs[etapa]=poderes' -f 'inputs[ano]=2025'`

## Painel 1 — Custo por deputado (NO AR, dados reais)
- Fonte CEAP: **CSV anual** `camara.leg.br/cotas/Ano-YYYY.csv.zip` (o endpoint `/deputados/{id}/despesas`
  da API v2 respondia 200 com lista vazia em 26/10/2026 — registrado na metodologia). API v2 usada para
  `/deputados?idLegislatura=57` (dedupe por id: 648 na legislatura) e `/deputados/{id}` → `ultimoStatus`
  (filtro `situacao == "Exercício"` → 513).
- Fórmula: subsídio (DL 172/2022, R$ 46.366,19 desde fev/2026, 13 + 1/3 por ano) + CEAP líquida (valor
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
  utilizou/não). 2026 (10 meses): 81 senadores, média R$ 90,8 mil/mês. Workflow `etl-senado.yml` (segunda 06:47 BRT).
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
