# Painel — Quanto custa a Câmara Municipal da sua cidade (e os estados)

Última revisão: 2026-10-26. Código: `etl/municipios/`. Atualização: maio, agosto e novembro (a DCA do ano anterior vence em
abril; retardatários entram nas cargas seguintes).

## 1. Fontes (sem chave)

| Dado | Fonte | Detalhe |
|---|---|---|
| Lista de entes, população, capital | SICONFI/Tesouro, API `…/siconfi/tt/entes` | 5.570 municípios, 26 estados, DF; população usada pelo próprio Tesouro |
| Despesa por função de cada ente | SICONFI/Tesouro, API `…/siconfi/tt/dca?an_exercicio=AAAA&no_anexo=DCA-Anexo I-E&id_ente=<IBGE>` | Declaração de Contas Anuais, anexo I-E; uma chamada por ente (5.597 por ano, ~10 min com 4 em paralelo); guardamos nível "função" e total, colunas empenhada, liquidada e paga |
| Vagas de vereador | TSE, dados abertos "Consulta vagas" `consulta_vagas_<ano>.zip` | CD_CARGO 13; o código TSE (SG_UE) não é o IBGE: casamos por UF + nome normalizado (sem acento, maiúsculo) |

## 2. O que é o número

- **Custo da Câmara** = despesa **paga** na função **01 Legislativa** da prefeitura no exercício. É a Câmara Municipal
  inteira: subsídio dos vereadores, servidores, prédio, contratos. Nos estados, 01 Legislativa = Assembleia (ou Câmara
  Legislativa do DF) + Tribunal de Contas; 02 Judiciária = Tribunal de Justiça; 03 Essencial à Justiça = Ministério Público e Defensoria.
- **Por habitante** = ÷ população do SICONFI. **Por vereador** = ÷ vagas do TSE (é escala, não o que cada vereador recebe).
- **% do orçamento** = função 01 ÷ total pago pela prefeitura ("Despesas Exceto Intraorçamentárias").
- Salário de vereador **não** está aqui: é lei de cada município, dentro do teto da CF art. 29, VI (20% a 75% do subsídio de
  deputado estadual, conforme a população). Não há base nacional.

## 3. Cobertura e cuidados

- Nem toda prefeitura entrega a DCA no prazo; o `municipios_meta_<ano>.json` diz quantas há. Município sem DCA **não aparece**
  (não é zero). Erros de preenchimento da própria prefeitura (ex.: função Legislativa zerada) aparecem como estão; não corrigimos.
- Rankings "mais caras / mais baratas" usam só cidades com ≥ 50 mil habitantes, e as medianas são por faixa de população
  (até 10 mil; 10–50 mil; 50–100 mil; 100–500 mil; > 500 mil), porque Câmara de cidade pequena é proporcionalmente mais cara.
- Homônimos no mesmo estado (raro) ficam com a primeira página; o código IBGE está na página para desambiguar.
- Casamento TSE × IBGE por nome falha em alguns municípios (grafias diferentes); eles ficam sem "por vereador".

## 4. Páginas

`/municipios/` (totais, medianas por faixa, capitais, rankings ≥ 50 mil, maior custo por vereador), `/municipios/uf/{uf}/` (todas
as cidades do estado + Assembleia, TJ e total do governo estadual), `/municipios/{uf}/{cidade}/` (uma página por município).

## 5. Pendências

1. Painel dos estados completo (Executivo, Assembleia, TJ, MP, Previdência) com ranking e subsídio dos governadores (27 leis estaduais, à mão).
2. Vereador a vereador nas capitais com dados abertos (São Paulo, Rio, BH, Curitiba, Porto Alegre).
3. Série histórica (DCA desde 2013) e deflação.
