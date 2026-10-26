# Painel — Quanto custa um ministro do STF

Última revisão: 2026-10-26.

## 1. Fonte (sem chave)

Portal da Transparência do STF → Remuneração: `https://egesp-portal.stf.jus.br/transparencia/rendimento_folha`.
É um formulário com exportação CSV (parâmetro `tipo_relatorio=CSV`) filtrável por ano, mês, cargo efetivo e
lotação. Usamos duas consultas por mês:

| Consulta | Parâmetros | O que devolve |
|---|---|---|
| Ministros | `q[ano_eq]`, `q[mes_eq]`, `q[cdg_cargo_efetivo_in][]=55` (MINISTRO) | 1 linha por ministro, em atividade e aposentado |
| Gabinete | `q[ano_eq]`, `q[mes_eq]`, `q[cdg_unidade_in][]=<id da lotação>` | 1 linha por pessoa lotada no gabinete |

Os ids das lotações (ex.: "GABINETE MINISTRO LUIZ FUX" = 1000000625.0) são lidos do próprio formulário em cada
execução. Colunas usadas: Nome, Matrícula, Cargo Efetivo, Situação Funcional, Nome da Unidade,
**"Remuneração Bruta após o teto constitucional somada com outras verbas"** e "Remuneração Liquida".
Código: `etl/stf/extract.py`, `etl/stf/transform.py`. A folha de um mês costuma sair na primeira quinzena do
mês seguinte; o extrator para quando encontra dois meses seguidos sem folha.

**Atualização.** O portal responde 403 a requisições vindas de fora do Brasil (runners do GitHub Actions),
com qualquer user-agent. A atualização é mensal e manual (`make stf ANO=<ano>`) a partir de uma máquina no Brasil;
a data da última carga aparece na página.

## 2. Fórmula

```
remuneracao_bruta   = Σ meses da coluna "Remuneração Bruta após o teto…" do ministro
gabinete            = Σ meses da mesma coluna para todas as pessoas lotadas no gabinete, exceto o ministro
custo_total_estimado = remuneracao_bruta + gabinete           (só meses com folha publicada)
custo_mensal_medio   = custo_total_estimado / meses_com_folha
custo_anual_projetado = custo_mensal_medio × 12                (ano corrente = projeção)
```

"Remuneração bruta após o teto constitucional somada com outras verbas" é o rótulo do STF: subsídio limitado
ao teto (R$ 46.366,19 desde fev/2025, DL 172/2022) **mais** verbas indenizatórias e
eventuais (auxílio-alimentação, auxílio pré-escolar, retroativos, substituições). É por isso que o valor varia
entre ministros e pode passar do teto. Não interpretamos nem separamos essas verbas: a fonte não as discrimina
no CSV (a composição está em "Estrutura remuneratória" do mesmo portal).

## 3. O que entra no gabinete

Todas as pessoas com lotação no gabinete do ministro na folha do mês: servidores efetivos do STF, cedidos de
outros órgãos (a folha do STF paga a parte do STF), sem vínculo efetivo (cargos em comissão), juízes auxiliares.
Em 2026 um gabinete tem ~30–37 pessoas. O presidente do Tribunal (Fachin em 2026) aparece lotado no
**Gabinete da Presidência** (~7 pessoas); seu gabinete judicial não existe como lotação separada no
formulário, então o custo dele fica subestimado e a página avisa.

## 4. O que NÃO entra

Prédio, segurança, transporte, viagens, diárias, saúde, apartamentos funcionais e a estrutura comum do Tribunal
(Secretaria, TI, biblioteca). Ministros aposentados (16 em ago/2026, ~R$ 1 mi/mês) aparecem como estatística
separada e não entram no custo de ninguém em atividade. Não há CPF na fonte.

## 5. Resultado 2026 (jan–ago, lido em 2026-10-26)

10 ministros em atividade (1 vaga). Remuneração bruta média R$ 53,4 mil/mês; gabinete médio R$ 758 mil/mês
(33 pessoas); custo médio R$ 811 mil/mês por ministro; acumulado 8 meses R$ 64,9 mi.

## 6. Pendências

1. Composição da remuneração (verbas indenizatórias × subsídio) via "Estrutura remuneratória".
2. Mesmo modelo para STJ, TST, TSE e CNJ (portais próprios, formulários semelhantes).
