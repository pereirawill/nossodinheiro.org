# Painel — Quanto o Brasil paga de imposto federal

Última revisão: 2026-10-26. Código: `etl/impostos/extract.py` → `data/public/impostos.json`. Atualização mensal (dia 25).

## 1. Fonte

Receita Federal, dados abertos "Arrecadação por estado": `https://www.gov.br/receitafederal/dados/arrecadacao-estado.csv`
(latin-1, `;`, valores em R$ correntes). Uma linha por ano × mês × UF, uma coluna por tributo, de janeiro de 2000 ao último
mês publicado (jul/2026 em 26/10/2026). É a arrecadação **administrada pela Receita Federal** (impostos e contribuições
federais, inclusive previdência e Simples Nacional) mais "administradas por outros órgãos" (royalties etc.).
**Não inclui** tributos estaduais e municipais (ICMS, IPVA, ITCMD, ISS, IPTU, ITBI), que são ~1/3 da carga tributária.

## 2. Leitura do CSV (armadilhas documentadas)

- Formatos numéricos misturados no mesmo arquivo: `65512,84` e `8762245,567` (decimal com vírgula, 1–3 casas),
  `47.953.915` e `1,006,523,961` (milhares, sem decimais), `1.234,56`. Regra em `_brl()`: com os dois separadores o
  último é o decimal; só vírgula: uma = decimal, várias = milhar; só ponto: vários = milhar, um seguido de exatamente 3
  dígitos = milhar, senão decimal. Testado em `tests/test_impostos.py`.
- Famílias com coluna agregada e detalhadas (COFINS / COFINS-FINANCEIRAS / COFINS-DEMAIS; PIS; CSLL; CIDE; CPSSS;
  Receita previdenciária): o CSV preenche uma OU outra conforme o ano; `_sem_duplicidade()` garante que nunca somamos as duas.
- Conferência: mar/2026 R$ 224,6 bi aqui vs R$ 229,25 bi divulgados pela Receita; mai/2026 R$ 257,1 bi vs R$ 266,8 bi;
  2025 R$ 2,86 tri. A diferença (2–4%) são receitas não administradas pela RFB e ajustes posteriores; está na página.

## 3. Bases de incidência (agrupamento nosso, declarado)

| Base | Tributos (colunas do CSV) |
|---|---|
| Renda do trabalho | IRPF; IRRF – rendimentos do trabalho; CPSSS (previdência dos servidores) |
| Folha (previdência) | Receita previdenciária (INSS: parte do empregado + parte da empresa, a fonte não separa) |
| Lucro das empresas | IRPJ (financeiras e demais); CSLL |
| Consumo e produção | IPI (todas as linhas); COFINS; PIS/PASEP; CIDE-combustíveis; impostos de importação e exportação |
| Renda do capital e operações financeiras | IRRF – capital, remessas ao exterior, outros rendimentos; IOF |
| Patrimônio | ITR |
| Simples Nacional e outros | Pagamento unificado (Simples), retenção Lei 10.833, REFIS, PAES, FUNDAF, outras receitas administradas, demais receitas, administradas por outros órgãos, CPMF/IPMF (extintos) |

**Quem recolhe não é quem paga.** A página não rotula nada como "imposto dos trabalhadores" ou "das empresas": COFINS e
PIS são recolhidos pela empresa e repassados no preço; a previdência tem as duas partes na mesma linha. "Vem do
trabalho" na página = renda do trabalho + folha; "vem do consumo" = consumo e produção. É a convenção econômica usual,
não um dado da Receita.

## 4. Derivados

- Por dia = total do ano ÷ dias decorridos até o fim do último mês publicado. Por habitante = ÷ 212,6 milhões (IBGE).
- Série anual só com anos de 12 meses; valores nominais (sem inflação). Por UF = onde o tributo foi recolhido (sede da
  empresa, DF com órgãos federais e royalties), não onde a atividade ocorreu.

## 5. Pendências

1. Estados e municípios (ICMS, IPVA, ISS, IPTU) via SICONFI/RREO (27 estados = 27 chamadas; municípios agregados pelo
   Tesouro) para um "quanto já foi arrecadado no Brasil" oficial, alternativa ao Impostômetro (que é contador privado da ACSP).
2. Deflacionar a série anual (IPCA, IBGE).
3. Carga tributária % do PIB (Receita publica anualmente; Tesouro "Estimativa da carga tributária").

## Carga tributária ano a ano (28/10/2026)

O gráfico da carga usa a tabela **TRIB 01-B** do estudo "Carga Tributária no Brasil" da Receita (receita tributária por
tributo em % do PIB), cuja linha "Total da Receita Tributária" dá a série **ano a ano de 2002 ao último ano publicado**,
num arquivo único. A Tab_01, que usávamos antes, traz só os anos recentes mais alguns de referência — era por isso que a
série pulava anos.

**Por que não vai a 1989.** As edições do estudo anteriores a 2015 não estão no endereço que a Receita mantém hoje (dão
404), e cada edição republica a série com o PIB revisado pelo IBGE e com mudanças de metodologia. Chegar a 1989 exigiria
emendar edições de bases diferentes, o que esta página não faz — a mesma regra que vale para o analfabetismo em Educação
e para a série do CNJ no Judiciário. 2002 é o começo da série que a própria Receita publica de uma vez.

Resultado: 30,3% do PIB em 2002, mínimo de 29,0% em 2020, máximo de 32,2% em 2024.

## Brasil × média da OCDE

A tabela **07** do mesmo estudo compara Brasil e média de 36 países da OCDE por base de incidência, com números que a
Receita monta a partir do Revenue Statistics da OCDE. Em 2023: carga total 32,0% contra 34,1%, mas **bens e serviços
13,0% contra 10,5%** e **renda, lucro e ganho de capital 9,1% contra 12,3%**. A carga total é parecida; o que se cobra é
diferente. Está na aba Comparação.
