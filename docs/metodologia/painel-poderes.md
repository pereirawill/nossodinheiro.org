# Painel — Quanto custa cada Poder da União

Última revisão: 2026-10-26.

## 1. Fonte

**SIOP** (Sistema Integrado de Planejamento e Orçamento, Ministério do Planejamento e Orçamento),
dados abertos da LOA e da execução orçamentária, consultados no endpoint SPARQL público
`https://www1.siop.planejamento.gov.br/sparql/`, grafo `http://orcamento.dados.gov.br/<ano>/`
(documentação: `https://www1.siop.planejamento.gov.br/siopdoc/doku.php/acesso_publico:dados_abertos`).
Sem chave. Uma consulta agregada por órgão × unidade orçamentária × grupo de natureza da despesa (GND)
devolve dotação (lei + créditos), empenhado, liquidado e pago. Código: `etl/portal_transparencia/extract_poderes.py`.

**Por que não o Portal da Transparência.** A API `/despesas/por-orgao` é documentada como
"Consulta as despesas dos órgãos do Poder Executivo Federal" (OpenAPI do Portal, 2026-10-26). Câmara,
Senado, TCU, tribunais, MPU e DPU não aparecem nela com nenhum código; o CSV anual "Orçamento da
Despesa" do Portal tem a mesma cobertura. Até 2026-10-26 o painel usou essa API e por isso só mostrava
o Executivo — corrigido nesta data.

## 2. O que é o número

- **Despesa paga no ano** (caixa), por unidade orçamentária da LOA. Não é "custo da máquina": o Executivo
  paga Previdência, SUS e Bolsa Família, que são política pública. Empenhado, liquidado e dotação ficam
  como colunas em `poderes_orgaos_<ano>.json`.
- O SIOP publica a execução com atualização contínua; o valor do ano corrente é parcial.
- Valores no SPARQL vêm arredondados ao real (sem centavos).

## 3. Classificação por Poder (`classificar()` em `extract_poderes.py`)

| Órgão (código LOA) | Grupo |
|---|---|
| 01000 Câmara, 02000 Senado, 03000 TCU | Legislativo |
| 10000 STF, 11000 STJ, 12000 Justiça Federal, 13000 JMU, 14000 Justiça Eleitoral, 15000 Justiça do Trabalho, 16000 TJDFT, 17000 CNJ | Judiciário |
| 29000 DPU, 34000 MPU, 59000 CNMP | Funções essenciais |
| 71000 Encargos Financeiros, 72000 Encargos Previdenciários, 73000 Transferências a estados e municípios, 74000 Operações Oficiais de Crédito, 75000 Dívida Pública Federal, 90000 Reserva | Dívida/Transferências (fora da comparação) |
| qualquer outro (ministérios, 83000 Bacen, 60000 Vice-Presidência…) | Executivo |

TCU entra no Legislativo porque é órgão auxiliar do controle externo (CF art. 71). MPU e DPU não são Poder
(CF arts. 127 e 134), por isso ficam em grupo próprio.

## 3b. "Manter a máquina" × políticas públicas (`poderes_categoria_<ano>.json`)

A divisão usa a classificação programática da própria LOA, sem juízo nosso (`categorizar()` em
`extract_poderes.py`):

| Programa da LOA | Categoria |
|---|---|
| 0031 Gestão e Manutenção do MPU, 0032 do Poder Executivo, 0033 do Poder Judiciário, 0034 do Poder Legislativo, 0035 das estatais | **Manter a máquina** |
| 09xx Operações especiais (0901 sentenças judiciais, 0909 outros encargos, 0999 reserva…) | Encargos especiais |
| qualquer outro programa (finalístico: Previdência, SUS, Bolsa Família, Fundo Eleitoral…) | Políticas públicas |

Dentro de "Manter a máquina", a subcategoria vem do GND e da ação: GND 1 com ação de aposentadoria,
pensão, inativos ou benefício especial (ex.: 0181, 00UX, 214H, 0179, 00S6) = **Aposentados e pensionistas**;
GND 1 restante (ex.: 20TP Ativos Civis, 2867 Ativos Militares, 09HB contribuição patronal) = **Pessoal
ativo e encargos**; GND 3 = Custeio; GND 4 e 5 = Investimento.

Ressalvas: (a) no Executivo, "pessoal" inclui militares (ativos ~R$ 32 bi; inativos e pensões ~R$ 58 bi em
2025) e o pessoal da saúde do DF pago pela União (00WW); (b) aposentadorias de órgãos extintos correm no
órgão 72000 Encargos Previdenciários da União, que está em Dívida/Transferências e não em nenhum Poder;
(c) a Justiça Eleitoral tem ~13% em programa finalístico (Fundo Partidário/Fundo Eleitoral), que aparece
como "Políticas públicas" do Judiciário. Per capita da máquina: população IBGE (§5).

## 4. Grupo de natureza da despesa (`poderes_gnd_<ano>.json`)

Por Poder × GND: 1 Pessoal e encargos, 2 Juros, 3 Outras despesas correntes, 4 Investimentos,
5 Inversões financeiras, 6 Amortização, 9 Reserva. "Custo de funcionar" = GND 1 + 3 + 4; dívida = 2 + 6.
Ainda não exibido no site (fase 2 do painel).

## 5. Per capita

`pago / população`, com a população passada explicitamente ao transform (`--populacao`, IBGE; 2025:
212.600.000, estimativa IBGE 2024 arredondada — a trocar pela estimativa oficial do ano quando publicada).

## 6. Fora do escopo

Judiciário e Legislativo **estaduais e municipais** (TJs, Assembleias, Câmaras Municipais) são orçamento
dos entes; fonte prevista: SICONFI (função 01 Legislativa e 02 Judiciária). Remuneração de magistrados: CNJ.
