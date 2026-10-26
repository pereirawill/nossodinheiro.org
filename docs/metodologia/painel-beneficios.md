# Página — Benefícios de deputados, senadores e ministros do STF

Última revisão: 2026-10-26. Dados em `site/src/lib/beneficios.ts` (uma linha por benefício, com fonte, URL e data
de leitura). Mudou um valor → muda lá e aqui na mesma alteração.

## 1. Natureza da página

Benefício é **regra**, não transação: não existe API. A lista vem das normas (decretos legislativos, atos da Mesa e
da Comissão Diretora) e das páginas oficiais de transparência de cada casa. Para cada linha dizemos:
- **valor ou regra**, em uma frase, com os números da fonte;
- **uso por pessoa**: se a casa publica quem usa / quanto usou (e se isso já está num painel do site);
- **no custo**: se a linha entra na conta dos painéis de custo (gasto real, teto, ou não entra);
- **fonte** e **data de leitura**.

Só entra o que a fonte confirma. O que circula sem base (ex.: "auxílio-paletó", "auxílio-educação",
"auxílio-cultural") fica fora ou aparece como desmentido pela própria casa (Câmara, Comprove).

## 2. Fontes por casa

**Câmara**: `camara.leg.br/transparencia/gastos-parlamentares` (subsídio, cota, verba de gabinete, apartamentos,
auxílio-moradia, diárias, totais 2026); guia para jornalistas "Salário de deputados" e "Atendimento médico para
deputados"; Comprove sobre auxílio-paletó; DL 172/2022; Ato da Mesa 89/2013 (saúde); Decreto 5.978/2006 (passaporte).

**Senado**: FAQs oficiais "Quanto ganha um senador?", "Os senadores recebem mais alguma verba além do subsídio?",
"Os senadores têm direito a imóvel funcional e auxílio-moradia?", "Como funciona a aposentadoria dos senadores?" e,
na Transparência, "Como funciona o plano de saúde de Senadores e ex-Senadores?"; página "Recursos utilizados" por
senador (quantidade de pessoal, benefícios usados); DL 172/2022; ACD 3/2003, 9/2011, 24/1992, 6/2012.

**STF**: contracheque detalhado por ministro no Portal da Transparência (`rendimento_folha` → "Mais informações",
blocos A a S: subsídio, vantagens pessoais, abono de permanência, auxílios, auxílio-moradia, férias, 13º); folha
por lotação (gabinete); Informativo STF 1210 (abr/2026) sobre a extinção de auxílios para magistrados.

**Ex-presidentes**: Lei 7.474/1986, Decreto 6.381/2008; dataset "Custos das equipes de segurança e apoio aos
ex-Presidentes da República (2021 a 2026)" no portal de dados abertos da Presidência (fora do ar em 26/10/2026).

## 3. Premissas e lacunas declaradas

- 13º e ⅓ de férias dos senadores: o FAQ do Senado não menciona; assumimos igual à Câmara (confirmado pela Câmara
  em "esclarecimentos sobre consulta de remuneração"). Premissa.
- Verba de gabinete do Senado: não há teto em reais publicado; a página mostra só a quantidade de pessoas.
- Auxílio-saúde dos ministros do STF: aparece zerado nos contracheques de ago/2026; valores de ressarcimento, se
  houver, não estão discriminados no CSV.
- Valores da Câmara citados pelo Comprove (verba de gabinete R$ 133.170,54; cota R$ 36,5–51,4 mil) são de anos
  anteriores; usamos os da página "Gastos parlamentares" (2026).
- Ex-presidentes: sem carga enquanto o portal de dados abertos da Presidência estiver indisponível.

## 4. Correção registrada em 2026-10-26

O escalonamento do subsídio (DL 172/2022) estava com as datas deslocadas um ano no `config.py` (R$ 46.366,19 só a
partir de fev/2026). O texto do decreto e o FAQ do Senado confirmam **1º/fev/2025**. Corrigido em todos os painéis.
