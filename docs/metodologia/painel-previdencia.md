# Painéis — INSS e Aposentadoria

Última revisão: 2026-10-27. Código: `etl/previdencia/extract.py` → `data/public/previdencia.json`. Atualização mensal (dia 14).
Páginas: `/inss/` (tudo que o INSS paga) e `/aposentadoria/` (os dois regimes de aposentadoria).

## 1. Por que são duas abas

O INSS e "aposentadoria" não são a mesma coisa, nos dois sentidos:

- **O INSS paga muito mais que aposentadoria**: pensão por morte, auxílio por incapacidade, auxílio-acidente, auxílio-reclusão,
  salário-maternidade e o BPC (assistência social, sem contribuição). Em ago/2026, 42,2% dos benefícios do instituto não eram
  aposentadoria.
- **Aposentadoria não é só o INSS**: servidor público concursado se aposenta pelo regime próprio (RPPS) do ente que o contratou,
  com outra caixa, outras regras e outro orçamento. Militares têm sistema à parte.

Por isso `/inss/` responde "o que o instituto paga" e `/aposentadoria/` responde "como o país aposenta", comparando os regimes.
Cada página explica a diferença no primeiro parágrafo e aponta para a outra.

## 2. Fontes

| Bloco | Fonte | Observação |
|---|---|---|
| Benefícios do INSS por espécie: quantidade, valor e valor médio | BEPS, tabela 15 | competência mensal |
| Benefícios do RGPS por estado, com clientela rural | BEPS, tabela 19 | não inclui BPC |
| Série de benefícios emitidos desde 2000 | BEPS, tabela 13 | dezembro de cada ano + último mês |
| Aposentados e pensionistas do regime próprio da União | SIOP, subcategoria "Aposentados e pensionistas" (`poderes_categoria_<ano>.json`) | despesa paga, por Poder |
| Previdência dos estados | SICONFI, DCA anexo I-E, função 09 (`estados_<ano>.json`) | quase toda RPPS de servidor |
| Servidores estatutários e militares na ativa | IBGE, PNAD Contínua (`trabalho.json`) | base das futuras aposentadorias do RPPS |

Os rótulos da tabela 15 trazem notas de rodapé no próprio texto da célula ("BENEFÍCIOS DE LEGISLAÇÃO ESPECÍFICA (BLE) (3)");
o extrator corta tudo a partir do primeiro parêntese antes de casar com a tabela de grupos.

## 3. Regras

- **Benefício não é pessoa**: as estatísticas contam benefícios emitidos; quem recebe aposentadoria e pensão aparece duas vezes.
  Dito no aviso das duas páginas; por isso nunca somamos benefícios com população.
- **Ano do INSS** = valor do mês × 13 (12 parcelas mais o 13º, que a lei manda pagar), sempre rotulado como projeção do mês.
- **Não comparamos valor médio entre regimes**: carreiras, tempo de contribuição e tetos são diferentes, e do RPPS não existe
  contagem nacional aberta de aposentados — só o valor pago. Isso está escrito no aviso de `/aposentadoria/`.
- A função 09 da União (R$ 1,04 tri em 2025) inclui os benefícios do INSS; a subcategoria "aposentados e pensionistas"
  (R$ 135,4 bi) é a parte de servidor. A página mostra as duas e explica a diferença.

## 4. Pendências

1. Quantidade de servidores aposentados e pensionistas do RPPS (União, estados, municípios): não há base nacional aberta;
   avaliar o Painel Estatístico de Pessoal e os dados do DIPR/SPREV.
2. Previdência dos **municípios**: a função 09 municipal ainda não é extraída pelo ETL de municípios.
3. Receita da previdência (contribuições) ao lado da despesa, para mostrar o resultado do regime.
4. Idade média de concessão e tempo médio de recebimento (BEPS tem tabelas de concessões).
5. Valor da folha de inativos militares separado dos civis.
