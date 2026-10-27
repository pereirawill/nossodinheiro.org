# Painel — Saúde: gasto público, planos e indicadores

Última revisão: 2026-10-27. Código: `etl/saude/extract.py` → `data/public/saude.json`. Atualização mensal (dia 11). Página: `/saude/`.

## 1. Fontes

| Bloco | Fonte | Observação |
|---|---|---|
| Gasto da União | SIOP, execução orçamentária, função 10 (Saúde) — já vem de `poderes_funcao_<ano>.json` | despesa paga |
| Gasto de estados e prefeituras | SICONFI/Tesouro, DCA anexo I-E, mesma função — já vem de `estados_<ano>.json` e `municipios_<ano>.json` | despesa paga |
| Planos de saúde | ANS, dados abertos, "Taxa de cobertura de planos de saúde" (PDA 047), CSV por município × sexo × faixa etária | competência mensal |
| Esperança de vida e mortalidade infantil | IBGE, Projeção da População (SIDRA 7362) | **projeção**, rotulada como tal |
| Mortalidade de menores de 5 anos, neonatal e materna | IBGE, indicadores dos ODS (SIDRA 6695, 6696, 6694), a partir do SIM/Ministério da Saúde | observado |
| Mortalidade infantil observada | IBGE, SIDRA 3834 | série encerrada em 2016 |
| População | IBGE, estimativas (SIDRA 6579) | base de todas as taxas |

Este ETL baixa só o que ainda não existia no projeto (ANS e indicadores do IBGE); o dinheiro vem dos ETLs já publicados, sem duplicar dado.

## 2. Regras

- **Os três níveis não são somados.** Parte do que a União paga é repassada a estados e prefeituras (transferências fundo a fundo
  do SUS) e reaparece na despesa deles. A página mostra os três separados e diz isso no aviso; não existe "total do país" aqui.
  Separar recursos próprios de repasse exigiria o SIOPS, ainda não integrado (pendência 1).
- **Beneficiário não é pessoa.** A ANS conta vínculos: quem tem dois planos conta duas vezes, e a própria agência admite taxa
  acima de 100% em alguns municípios. "Quem depende só do SUS" = população − beneficiários de planos de assistência médica,
  e está rotulado como estimativa pela mesma razão. Planos exclusivamente odontológicos ficam fora da taxa.
- O código de município da ANS tem **6 dígitos** (sem o dígito verificador do IBGE); o casamento com as capitais usa `cod_ibge // 10`.
- A taxa usa a população do IBGE, não a coluna POPULACAO do arquivo da ANS, que vem zerada na maior parte das linhas.
- Esperança de vida e mortalidade infantil do ano corrente são **projeção** do IBGE (revisão vigente), porque é a única série
  por UF que chega até aqui. A série observada de mortalidade infantil para em 2016, e a página mostra as duas linhas separadas.
- Nenhuma nota de eficiência: gastar mais não garante atender melhor, e gastar pouco pode significar dependência do repasse federal.

## 3. Pendências

1. SIOPS (Sistema de Informações sobre Orçamentos Públicos em Saúde): recursos próprios por ente, para poder falar em total do país.
2. Leitos e estabelecimentos (CNES): `apidadosabertos.saude.gov.br` recusa conexão (connection reset) e o TabNet não tem API estável.
3. Equipes de Saúde da Família e cobertura da atenção básica (e-Gestor/MS).
4. Fila de cirurgias e tempo de espera: não há base nacional aberta.
5. Gasto por habitante com recorte de faixa etária (a população idosa custa mais e é distribuída de forma desigual entre estados).
