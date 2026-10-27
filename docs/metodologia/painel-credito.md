# Painel — Inadimplência: crédito em atraso por estado (SCR.data)

Última revisão: 2026-10-26. Código: `etl/credito/extract.py` → `data/public/credito.json`. Atualização mensal (dia 10); o BCB publica com ~30 dias de defasagem.

## 1. Fonte

Banco Central do Brasil, **SCR.data** (dados agregados do Sistema de Informações de Crédito), dados abertos: `https://www.bcb.gov.br/pda/desig/scrdata_<ano>.zip`, um CSV por mês (`;`, decimal com vírgula), colunas: data_base, uf, segmento, cliente (PF/PJ), cnae_ocupacao, porte, modalidade, submodalidade, origem, indexador, numero_de_operacoes, faixas a vencer/vencido, carteira_ativa, carteira_inadimplencia, ativo_problematico. Metodologia v2 do BCB. Baixamos os zips do ano corrente e do anterior (série de até 24 meses) e detalhamos o último mês.

## 2. Definições (do BCB)

- **carteira_ativa** = tudo emprestado (a vencer + vencido).
- **carteira_inadimplencia** = parcelas vencidas há mais de 90 dias.
- **taxa** = inadimplência ÷ carteira ativa, em %. É inadimplência **em reais**, não em pessoas; o BCB não publica "quantas pessoas estão negativadas" (dado de birôs privados, que não usamos).
- `numero_de_operacoes` = −1 quando há menos de 15 operações no agrupamento (sigilo); por isso não somamos operações.
- **porte** (PF) = faixa de renda informada ao banco; (PJ) = porte da empresa.

## 3. Alcance

UF é o menor recorte geográfico do SCR.data (endereço do tomador). O BCB tem também "SCR por sub-região" (105 áreas, códigos sem nome legível) — **não há dado oficial por município**; a página diz isso. Séries mais longas existem no SGS do BCB (não integradas).

## 4. Pendências

1. Série longa de inadimplência PF/PJ (SGS, séries 21082+), desde 2011.
2. Inadimplência por CNAE (empresas) e por ocupação (PF): colunas já existem no CSV.
3. Desenrola/renegociações: dados abertos do BCB.
