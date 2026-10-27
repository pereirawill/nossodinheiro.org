# Painel — Renda: setor público × privado e os 10% e 1% mais ricos

Última revisão: 2026-10-26. Código: `etl/renda/extract.py` → `data/public/renda.json`. Atualização mensal (dia 7); a PNAD anual sai uma vez por ano.

## 1. Fonte

IBGE, PNAD Contínua (Pesquisa Nacional por Amostra de Domicílios Contínua), divulgação anual de rendimento de todas as fontes, via API SIDRA, sem chave. Valores "a preços médios do último ano" (o IBGE já corrige a inflação). Série 2012 → último ano.

| Tabela | O que traz | Uso na página |
|---|---|---|
| 4659 | rendimento médio mensal real habitual do trabalho principal, por posição na ocupação e categoria do emprego (Brasil e UF) | barras por vínculo, série, tabela por estado |
| 7527 | distribuição da massa de rendimento domiciliar per capita por classes simples de percentual (até P10 … > P99) | quanto da renda fica com cada faixa; 10% e 1% por UF |
| 7530 | idem, classes acumuladas (até o P50) | "metade mais pobre" |
| 7533 | rendimento médio domiciliar per capita por classe | renda média de cada faixa; renda por pessoa por UF |
| 7438 | limites superiores das classes (P10, P50, P90, P95, P99) | "quanto é preciso ter para estar no 1%" |
| 7535 | rendimento médio dos ocupados por classes de percentual **dos ocupados** | quanto ganha o 1% dos trabalhadores |
| 7435 | índice de Gini do rendimento domiciliar per capita (Brasil e UF) | desigualdade |

## 2. Definições que importam

- **Setor público (PNAD)** = empregados de órgãos públicos das três esferas: estatutários, militares e celetistas (categorias 31727–31730). Inclui professor municipal, agente de saúde, policial. **Setor privado** exclui trabalhador doméstico (classe própria).
- **Rendimento habitual** = o que o entrevistado declara receber normalmente, bruto. Média entre quem tem rendimento. Pesquisa por amostra: tem coeficiente de variação (não publicado na página; disponível na mesma tabela).
- **Renda domiciliar por pessoa** = todos os rendimentos do domicílio ÷ moradores. É a base de P10…P99, da massa e do Gini.
- As duas ordenações (pessoas por renda domiciliar; ocupados por renda do trabalho) são diferentes e estão rotuladas na tabela.

## 3. Leitura honesta

Comparar a média do setor público com a do privado mistura ocupações, escolaridade e jornada; o próprio IBGE alerta. A página mostra a razão aritmética e diz isso no aviso. Não há "salário típico" (mediana) por posição na divulgação anual em tabela aberta; registrado como pendência.

## 4. Pendências

1. Receita Federal, "Grandes Números do IRPF": renda declarada do topo (0,1%); planilhas de formato variável, não automatizadas.
2. Mediana por posição na ocupação (microdados da PNAD).
3. Painel Estatístico de Pessoal (servidores federais): remuneração média por carreira.
