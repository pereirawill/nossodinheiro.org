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
