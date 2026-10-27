# Painel — Quem trabalha, quem empreende, quem recebe

Última revisão: 2026-10-26. Código: `etl/trabalho/extract.py` → `data/public/trabalho.json`. Atualização mensal (dia 5).

## 1. Fontes (sem chave)

| Bloco | Fonte | Como lemos |
|---|---|---|
| Pessoas de 14+ por condição (ocupadas, desocupadas, fora da força) | IBGE, PNAD Contínua, SIDRA tabela 6318 (trimestre móvel) | API `apisidra.ibge.gov.br`, último período; valores em mil pessoas |
| Ocupados por posição (carteira, sem carteira, doméstico, setor público, estatutário/militar, empregador, conta própria, familiar) | IBGE, PNAD Contínua, SIDRA tabela 4097 (trimestre) | idem |
| Taxa de desocupação | IBGE, SIDRA tabela 6381 | idem |
| Empresas ativas por natureza jurídica e porte (MEI, ME, EPP, demais) | Governo federal (MEMP/DREI), Mapa de Empresas, planilha mensal aberta | última `*_arquivodados_<mes><ano>-mapa-de-empresas.xlsx` do repositório, aba "Empresas Ativas por NJ e Porte"; leitor xlsx próprio |
| Benefícios pagos pelo INSS (RGPS, assistenciais/BPC, legislação especial) | Ministério da Previdência, Boletim Estatístico da Previdência Social (BEPS), tabela 14 | último `beps<mm><aaaa>_final.xls` (xlrd); a linha mais recente com mês e quantidade; o ano aparece só na 1ª linha de cada bloco (número até 2015, texto depois) e as células mescladas deslocam as colunas |

## 2. Leitura honesta

- Os grupos se sobrepõem: MEI pode ser empregado; aposentado pode trabalhar; uma pessoa pode ter dois benefícios ou duas
  empresas. A PNAD conta pessoas (amostra); o Mapa de Empresas conta CNPJs. Não somamos "quem sustenta" com "quem recebe".
- "Conta própria" da PNAD inclui MEI e informais; "setor público" inclui estatutários, militares e celetistas de órgãos públicos.
- Benefícios do INSS não incluem aposentados de regimes próprios (servidores da União, estados e municípios).
- Vínculo formal (herói) = carteira assinada no setor privado + domésticos com carteira + setor público.

## 3. Pendências

1. **Bolsa Família**: famílias e valor por mês. Fonte oficial agregada legível por máquina não localizada (dados.gov.br exige
   chave; portal do MDS fora do ar em 26/10/2026). Alternativa: API do Portal da Transparência `novo-bolsa-familia-por-municipio`
   (5.570 chamadas por mês, com chave, no Actions) ou o CSV mensal por beneficiário (330 MB) agregado no servidor.
2. **Optantes do Simples Nacional** (ME/EPP): a Receita publica estatísticas, mas sem arquivo aberto localizado; o Mapa de
   Empresas traz o porte, não a opção pelo regime.
3. Série histórica (PNAD desde 2012; BEPS desde 2000, já na tabela 14).

## Empresas por tamanho e porte (acrescentado em 27/10/2026)

- **Fonte:** IBGE, Cadastro Central de Empresas (CEMPRE), tabela 7528 do SIDRA: número de empresas, pessoal ocupado, assalariados e
  salário médio por **faixa de pessoal ocupado** (0 a 4 … 500 ou mais) e por seção da CNAE. Anual, com ~2 anos de defasagem.
- **Porte (micro, pequena, média, grande):** não existe definição única no Brasil. A **lei** (LC 123/2006) classifica por
  **faturamento** — é o MEI/ME/EPP que aparece no bloco do Mapa de Empresas. As **estatísticas** usam **pessoal ocupado**, com o
  critério do **Sebrae**, que tem cortes diferentes por setor: indústria e construção (micro ≤19, pequena 20–99, média 100–499,
  grande 500+) e comércio e serviços (micro ≤9, pequena 10–49, média 50–99, grande 100+). Aplicamos esse critério **seção a seção**
  da CNAE, somando os dois grupos; a página diz que não é classificação legal e que uma empresa pode ser "de pequeno porte" na lei
  e "média" aqui. A soma por porte fica ~37,7 mil pessoas abaixo do total porque algumas linhas do cadastro não entram na divisão
  por seção de atividade; isso está declarado na página.
- **Por que o total do CEMPRE (10,6 mi) é menor que o do Mapa de Empresas (25,5 mi):** o CEMPRE conta empresas que entregaram
  declarações no ano de referência; o Mapa conta CNPJs ativos hoje, incluindo MEIs sem atividade declarada. Os dois aparecem na
  página, com a diferença explicada.

## Força de trabalho contribuinte (acrescentado em 27/10/2026)

- **Fonte:** IBGE, PNAD Contínua trimestral, tabela 5947 (ocupados contribuintes e não contribuintes de instituto de previdência),
  com 6318 (condição na força de trabalho) e a estimativa de população (SIDRA 6579).
- A pizza divide a **população inteira** em cinco grupos que não se sobrepõem: contribuem, trabalham sem contribuir, procuram
  trabalho, estão fora da força de trabalho e crianças até 13 anos (estas por diferença entre a população estimada e a população
  de 14 anos ou mais da PNAD, portanto aproximadas).
- **Não dá para dizer "quantos sustentam quantos"** a partir dela: entre os que estão fora da força há aposentados que já
  contribuíram a vida toda, e entre os contribuintes há quem também receba benefício. A página diz isso.
