# Painel — Inflação: IPCA desde 1979

Última revisão: 2026-10-27. Código: `etl/inflacao/extract.py` → `data/public/inflacao.json`. Atualização mensal (dia 12, depois da divulgação do IBGE). Página: `/inflacao/`.

## 1. Fontes

| Série | Fonte | Desde |
|---|---|---|
| IPCA: número-índice, variação no mês, no ano e em 12 meses | IBGE, SIDRA tabela 1737 | dez/1979 |
| IPCA por grupo de gasto (9 grupos) e peso de cada um | IBGE, SIDRA tabela 7060, classificação 315, nível 1 | jan/2020 |
| IPCA por região (10 regiões metropolitanas + 6 municípios) | IBGE, SIDRA tabela 7060, níveis N7 e N6 | jan/2020 |
| INPC em 12 meses | IBGE, SIDRA tabela 7063 | jan/2020 |
| Meta de inflação | Banco Central, SGS série 13521 (meta do Conselho Monetário Nacional) | 1999 |

Os códigos dos 9 grupos na classificação 315 estão fixos em `GRUPOS` (a API de metadados do IBGE deu timeout a partir dos
runners do GitHub); conferir em `/api/v3/agregados/7060/metadados` quando o IBGE trocar a cesta (a última troca foi em 2020,
com base na POF 2017-2018).

## 2. Regras

- **IPCA ≠ inflação de uma pessoa.** O índice mede a cesta média das famílias com renda de 1 a 40 salários mínimos nas 16 áreas
  pesquisadas; o INPC, de 1 a 5. A página diz isso no aviso e mostra o peso de cada grupo.
- **Ano fechado** = variação acumulada no ano em dezembro. O ano corrente aparece como parcial, em cinza, e fora da contagem de
  "anos acima/abaixo da meta".
- **Meta**: comparamos só com o **valor central** da série 13521. A margem de tolerância definida pelo CMN não entra no gráfico,
  e isso está dito no rótulo e na conclusão — um ano "acima do valor central" pode ter ficado dentro da banda.
- **Gráfico desde 1996**: antes do Plano Real a variação chegava a milhares por cento e achataria o resto. A série completa fica
  no JSON e aparece na tabela "quanto os preços subiram desde…".
- **"R$ 100 daquela época"**: razão entre o número-índice do mês atual e o de dezembro do ano escolhido. De 1980 a 1994 o país
  trocou de moeda cinco vezes; o fator serve para mostrar escala, não para converter valores antigos (a página avisa).
- Não existe IPCA por estado: o IBGE pesquisa 16 áreas, e o índice nacional é a média ponderada delas. Por isso esta página não
  tem mapa.

## 2b. Poder de compra (acrescentado em 27/10/2026)

- **Curva do poder de compra**: `poder(mês) = 100 × índice(jul/1994) ÷ índice(mês)`, ou seja, quanto compram em cada mês os mesmos
  R$ 100 de julho de 1994, quando o real nasceu. Em set/2026: R$ 11,90, uma perda de 88,1% em 32 anos.
- **Não é cotação de moeda**: não tem relação com o dólar nem com o valor do real no exterior; é só quanto o dinheiro compra dentro
  do país, medido pelo IPCA. Dito na página e no glossário (`poder_de_compra`).
- **A tabela "quanto os preços subiram desde…"** ganhou rótulos sem ambiguidade — "para comprar hoje o que R$ 100 compravam, preciso
  de" e "R$ 100 de hoje compram o que comprava" —, uma coluna de poder de compra perdido e a linha de julho de 1994. Os títulos
  antigos ("R$ 100 daquela época valem hoje" / "R$ 100 de hoje valiam") eram ambíguos: davam a entender tanto correção monetária
  quanto dinheiro guardado no colchão. O dono apontou a ambiguidade em 27/10/2026.
- **"E o dinheiro parado, quanto perde?"**: projeção simples que repete a inflação de 12 meses para a frente (1, 2, 5, 10 e 20 anos),
  rotulada como projeção e não previsão, para mostrar o juro composto ao contrário.

## 3. Pendências

1. IPCA-15 (prévia mensal) e a série de itens (457 subitens já disponíveis na tabela 7060).
2. INPC por região e por grupo (mesma tabela 7063).
3. Selic e juros reais ao lado da inflação (BCB, SGS 432 e 11); a série 432 deu HTTP 502 no teste de 27/10/2026.
4. Série longa de IGP-M e INCC: a FGV cobra pelo acesso, fora do critério de fonte pública aberta.
