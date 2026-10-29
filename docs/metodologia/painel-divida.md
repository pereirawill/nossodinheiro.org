# Painel — Dívida pública: o que ela custa

Última revisão: 2026-10-29. Código: `etl/divida/extract.py` → `data/public/divida.json`. Atualização mensal (dia 20).
Página: `/divida/`.

## 1. Três números, três conceitos

| O que | 2025 | O que mede | Fonte |
|---|---|---|---|
| **Juros nominais** (Governo Central) | R$ 891,9 bi | custo econômico do ano, inclusive juros apropriados no estoque dos títulos | Tesouro, RTN, tabela 2.1, linha "9. JUROS NOMINAIS" |
| **Juros e encargos pagos** | R$ 362,7 bi | saída de caixa no Orçamento, função 28 | SIOP (`poderes_categoria_<ano>.json`) |
| **Amortização** | R$ 1,77 tri | principal vencido, quase todo refinanciado — **não é custo** | SIOP |

Os três são oficiais e nenhum é errado: medem coisas diferentes. Somar amortização e juros, como se fosse despesa do
ano, é o erro mais comum — dobra a conta. A página diz isso antes de qualquer gráfico.

**Recorte**: Governo Central (Tesouro, Previdência e Banco Central). O número de cerca de **R$ 1,1 trilhão** que
circula na imprensa é o do **setor público consolidado** (inclui estados, municípios e estatais), apurado pelo Banco
Central, com outra metodologia. Usamos o Governo Central porque é o recorte do resto do site, e declaramos a diferença.

## 2. Fontes

- **Juros nominais**: planilha *Resultado do Tesouro Nacional — Série Histórica*, aba **2.1** (anual, R$ milhões
  correntes), linha `9. JUROS NOMINAIS`, **desde 1997**. O arquivo muda de nome a cada mês e é resolvido pela API do
  CKAN do Tesouro Transparente — o mesmo caminho já usado no painel de Estatais para os dividendos. Despesa vem com
  sinal negativo na planilha; o extrator guarda o valor absoluto.
- **Estoque**: *Estoque da Dívida Pública Federal* (CSV, ~12 MB), um registro por **título e mês**, desde set/2017.
  Dele saem o total por mês, a divisão interna/externa, o perfil de vencimento e a composição por indexador.

## 3. Composição por indexador

O indexador é deduzido da família do título, pelas definições do próprio Tesouro: **LFT** → Selic, **NTN-B** → IPCA,
**NTN-C** → IGP-M, **LTN** e **NTN-F** → prefixado, dívida externa → câmbio. O mapeamento está em `INDEXADOR`, no
código. Em ago/2026: 47,9% Selic, 24,5% prefixado, 24,0% IPCA, 2,9% câmbio.

É isso que explica por que o custo reage rápido: quase metade do estoque acompanha a taxa básica, sem esperar
vencimento.

## 4. O que não entra

- Estados, municípios e estatais (só União).
- Dívida bruta em % do PIB — depende de um PIB revisado; a página explica por que não mistura com valores em reais.
- Perfil dos detentores (quem são os credores): o Tesouro publica em outro relatório, ainda não lido.
- Dívida contratual de estados, que tem arquivo aberto próprio.

## 5. Conferências

- A soma do estoque por título em cada mês bate com o total que o Tesouro divulga no Relatório Mensal da Dívida (mesma
  fonte, outro arquivo) — conferido para ago/2026.
- Os juros nominais do RTN (R$ 891,9 bi em 2025) são maiores que os juros pagos no Orçamento (R$ 362,7 bi) por
  construção, e a página explica a diferença em vez de escolher um dos dois.
