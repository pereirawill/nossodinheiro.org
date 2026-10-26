---
layout: ../layouts/Base.astro
title: Metodologia — Nosso Dinheiro
---

Versão 0.1 · 26/10/2026 · Status: MVP

## 1. Pergunta

**Quanto custa, para o contribuinte, manter cada um dos 513 deputados federais em um ano?**
O painel decompõe o custo em parcelas com naturezas diferentes — o que é remuneração
pessoal (subsídio), o que é reembolso de despesa de mandato (cota parlamentar) e o que é
folha de pessoal do gabinete (verba de gabinete) — e deixa explícito o que é **gasto real**
e o que é **teto/estimativa**.

## 2. Fontes

| Parcela | Fonte | Tipo | Granularidade |
|---|---|---|---|
| Lista de deputados | API Dados Abertos da Câmara, `GET /deputados?idLegislatura=57` | primária, oficial | por deputado |
| Cota parlamentar (CEAP) — gasto real | API, `GET /deputados/{id}/despesas?ano=` **ou** CSV anual `camara.leg.br/cotas/Ano-YYYY.csv.zip` | primária, oficial | por documento (nota fiscal/recibo) |
| Subsídio mensal | Decreto Legislativo 172/2022 (escalonamento 2023-2026) | norma | valor fixo por período |
| Verba de gabinete (teto) | camara.leg.br/transparencia/gastos-parlamentares (lido em 26/10/2026) | oficial | valor fixo mensal |
| Auxílio-moradia | idem | oficial | valor fixo mensal |

**Fonte padrão da CEAP: CSV anual** (`Ano-YYYY.csv.zip`). Em 26/10/2026 o endpoint
`/deputados/{id}/despesas` da API respondia 200 com lista vazia para qualquer filtro; o CSV
é a mesma base publicada pela Câmara. A API fica como alternativa (`--fonte api`).

A API é consumida sem autenticação; os dados são coletados pelo ETL em `etl/camara/`
e versionados em `data/public/` (JSON agregado). O raw e o Parquet ficam fora do git
e são publicados como artefato do GitHub Actions.

## 3. Fórmula

```
custo_total_estimado(deputado, ano) =
      subsídio(ano)                       # §3.1 — fixo, igual para todos
    + CEAP_líquida(deputado, ano)         # §3.2 — gasto REAL, varia por deputado
    + verba_gabinete_teto(ano)            # §3.3 — TETO, igual para todos (estimativa superior)
```

### 3.1 Subsídio
Valor bruto mensal, com reajuste em fevereiro de cada ano (DL 172/2022):
R$ 39.293,32 (2023) → 41.650,92 (2024) → 44.008,52 (2025) → **46.366,19 (2026)**.
Somamos mês a mês (janeiro de 2026 ainda usa o valor de 2025) e acrescentamos
13º subsídio e 1/3 de férias, proporcionais aos meses considerados
(`SUBSIDIOS_POR_ANO = 13 + 1/3`).
**Premissa a confirmar:** a incidência exata de 13º/férias deve ser conferida na folha
publicada pela Câmara (transparência → remuneração). Até lá, está sinalizada como premissa.

### 3.2 Cota parlamentar (CEAP)
Soma de `valorLiquido` de todos os documentos do deputado no ano.
- `valorLiquido = valorDocumento − valorGlosa`. Glosa é o valor **não** reembolsado
  pela Câmara; usar o líquido evita inflar o custo com despesas rejeitadas.
- Inclui todos os tipos (passagens, divulgação, combustível, escritório etc.).
- Sem rateio de teto: a cota não gasta não é custo.
- O ETL **não** persiste o CPF do parlamentar presente no CSV anual.

### 3.3 Verba de gabinete
Teto mensal de **R$ 165.806,07** para até 25 secretários parlamentares.
**Limitação central do MVP:** o gasto real por gabinete não está na API de Dados
Abertos; é publicado por deputado no site da Câmara. Usamos o teto como
estimativa superior e declaramos isso no gráfico. Roadmap: raspar a página de
verba de gabinete por deputado e substituir o teto pelo real (v0.2).
Encargos (13º, férias, auxílio-alimentação dos secretários) são pagos pela Câmara
fora desse teto e **não** estão contabilizados — o custo real do gabinete é maior.

### 3.4 O que fica de fora do total (e por quê)
- **Auxílio-moradia (R$ 4.253/mês):** só recebe quem não ocupa um dos 447
  apartamentos funcionais. Sem lista pública fácil de quem ocupa, não há como
  atribuir individualmente sem chutar. Aparece como coluna separada `auxilio_moradia_max`.
- **Ajuda de custo** (um subsídio no início e no fim da legislatura), **plano de saúde**,
  **previdência**, **passaporte diplomático**, **estrutura física/TI da Câmara**: custos
  reais, mas sem base individual na fonte. Documentados como lacuna.
- **Emendas parlamentares:** não são "custo do deputado" — são despesa pública
  alocada por ele. Painel próprio no futuro.

## 4. Período e atualização
- Ano corrente: `meses_considerados = mês atual` (o mês corrente entra parcial;
  despesas da CEAP têm atraso de lançamento de semanas). Anos fechados: 12.
- Atualização semanal via GitHub Actions (segunda, 06:17 BRT). Cada execução
  reprocessa o ano inteiro — a API corrige/glosa documentos retroativamente.

## 5. Como ler o gráfico
- Como subsídio e verba de gabinete são iguais para todos, **o ranking é decidido
  pela cota parlamentar**. O gráfico empilhado existe para mostrar a *proporção*,
  não para sugerir que um deputado "ganha" mais salário.
- "Mais caro" ≠ "pior". Deputados de estados distantes têm teto de cota maior
  (R$ ~41,6 mil no DF a ~57,3 mil em RR) porque passagens custam mais.
  Versão futura: coluna "% do teto da UF" para comparar justo.

## 6. Reprodutibilidade
```
pip install -r requirements.txt
python -m etl.camara.extract deputados
python -m etl.camara.extract despesas --ano 2026     # ou: ceap-bulk --ano 2026
python -m etl.camara.transform --ano 2026 --fonte api # ou --fonte bulk
python -m etl.camara.chart --ano 2026 --top 20
```
Todas as constantes e suas fontes/datas estão em `etl/camara/config.py`.
Mudou um número lá → mudou aqui, na mesma PR.

## 6b. Reconciliação com a fonte (26/10/2026)
| Métrica | Oficial | Nosso ETL | Diferença | Explicação |
|---|---|---|---|---|
| CEAP 2026, todos os registros do CSV | R$ 179,09 mi (camara.leg.br/transparencia) | R$ 141,32 mi (só linhas com `ideCadastro`) | −21% | Lideranças partidárias/do governo têm cota própria e ficam fora do custo individual; o CSV também inclui lançamentos de ex-deputados da legislatura. A conferir: somar as linhas sem `ideCadastro` e verificar se fecha. |

## 7. Pendências conhecidas (v0.1)
- [ ] Tabela completa do teto da CEAP por UF, de fonte primária (Ato da Mesa 43/2009 e atualizações).
- [ ] Gasto real da verba de gabinete por deputado (substituir teto).
- [ ] Confirmar 13º/férias do subsídio na folha publicada.
- [x] Só deputados com `ultimoStatus.situacao = Exercício` entram (v0.2). Pendente: proporcionalizar o subsídio pelo período real de exercício de quem assumiu no meio do ano.