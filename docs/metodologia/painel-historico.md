# Painel — Histórico: séries longas corrigidas pela inflação

Última revisão: 2026-10-26. Código: `etl/historico/extract.py` → `data/public/historico.json`. Atualização mensal (dia 6).

## 1. Fontes e alcance

| Série | Fonte | Desde | Como lemos |
|---|---|---|---|
| União por função (pago e empenhado) | SIOP, SPARQL, um grafo por ano `orcamento.dados.gov.br/<ano>/` | 2000 | 1 consulta agregada por função por ano (26+ consultas, ~10 s cada); 2026 é parcial |
| Arrecadação federal | Receita Federal (CSV já usado no painel Impostos), anos com 12 meses | 2000 | reaproveita `impostos.json` |
| Benefícios do INSS | BEPS tabela 14 | 2000 | dezembro de cada ano; no ano corrente, o último mês publicado |
| IPCA | IBGE, SIDRA tabela 1737, variável 2266 (número-índice, dez/1993 = 100) | 1979 | índice de dezembro de cada ano; no ano corrente, o último mês |

## 2. Correção pela inflação

Todos os valores em reais do **ano-base** = último ano fechado (2025 em out/2026). `deflator[ano] = IPCA_dez(ano_base) ÷
IPCA_dez(ano)`; o site multiplica o valor nominal pelo deflator. R$ 1 de 2000 = R$ 4,40 de 2025. Escolhemos o índice de
dezembro (e não a média do ano) por simplicidade e por ser a convenção do Tesouro nas séries de "valores constantes"; a
diferença para a média anual é pequena e está declarada aqui. O JSON guarda os nominais; a conversão é feita na página.

## 3. Leitura honesta

- **Encargos especiais** (função 28: juros, amortização, refinanciamento, transferências constitucionais) ficam separados em
  todos os gráficos: são ~58% do total da União em 2025 e sua variação (refinanciamento da dívida) distorce qualquer comparação.
- O ano corrente aparece como "parcial" nas tabelas e fora dos gráficos reais.
- As séries começam quando a fonte aberta começa. **Nenhuma chega a 1988**; a tabela "Até onde cada fonte volta no tempo",
  na página e na Metodologia, diz o primeiro ano de cada painel e o que existe antes (quase sempre PDF ou metodologia diferente).

## 4. Pendências

1. Finbra antigo (municípios e estados, 1989–2012): arquivos anuais do Tesouro em formatos variados; avaliar e integrar.
2. Cartão corporativo desde 2003, cota parlamentar desde 2008, PNAD anual 1992–2011 (não comparável à Contínua sem ajuste).
3. Deflacionar também os painéis de Deputados, Senadores e STF quando ganharem série.
