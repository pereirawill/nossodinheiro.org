# Painel — Educação: IDEB por estado e município

Última revisão: 2026-10-26. Código: `etl/educacao/extract.py` → `data/public/educacao.json`. Sem agenda no GitHub Actions: o INEP recusa conexões dos runners do GitHub (connection reset), como o STF; rodar `python -m etl.educacao.extract` localmente a cada edição (bienal: 2023 divulgada em ago/2024; 2025 prevista para 2026) e commitar o JSON.

## 1. Fonte

INEP, planilhas de divulgação do IDEB em `download.inep.gov.br/ideb/resultados/`:
- `divulgacao_brasil_ideb_<ano>.zip` e `divulgacao_regioes_ufs_ideb_<ano>.zip` — 3 abas (anos iniciais, anos finais, ensino médio), linhas por Brasil/região/UF × rede (Total, Pública, Privada, Estadual, Municipal, Federal), colunas `VL_OBSERVADO_<edição>` de 2005 à última.
- `divulgacao_{anos_iniciais,anos_finais,ensino_medio}_municipios_<ano>.zip` — 1 linha por município × rede.
Cada zip traz o md5 do xlsx; conferimos antes de ler. O INEP abrevia "M. G. do Sul", "R. G. do Norte", "R. G. do Sul" (mapeado).

TLS: o certificado de `download.inep.gov.br` não fecha a cadeia em alguns ambientes. O extrator tenta com verificação; se falhar por certificado, baixa sem verificação e **confere o md5 publicado dentro do zip**.

## 2. Definições

- **IDEB** = indicador de rendimento (aprovação) × nota média padronizada do Saeb (português e matemática), 0 a 10. Só o `VL_OBSERVADO`; as metas (projeções) não entram.
- **Município** = rede **pública** (estadual + municipal + federal); o INEP não calcula IDEB municipal da rede privada. Município sem turma avaliada ou com participação insuficiente não tem IDEB.
- Δ = diferença para a edição anterior publicada.

## 3. Leitura honesta

O IDEB mede escolas e redes; a nota da rede privada reflete também renda e escolaridade das famílias. Décimos não são ranking: a página ordena por padrão pelos anos iniciais mas avisa. Em municípios pequenos a nota depende de poucas turmas.

## 4. Pendências

1. Saeb por disciplina e nível de proficiência; taxa de abandono.
2. Gasto por aluno (SIOPE/FNDE) ao lado do IDEB, sem inferir causalidade.
3. Censo Escolar: matrículas por rede, para ponderar.

## Escolaridade da população adulta e analfabetismo (28/10/2026)

O IDEB mede a escola. Estas duas seções medem a **população**, e vêm do IBGE, PNAD Contínua anual (módulo Educação),
via SIDRA:

| Tabela | O que mede | Universo | Série |
|---|---|---|---|
| 7189 | pessoas por nível de instrução (mil pessoas e distribuição %) | 25 anos ou mais | 2016 → |
| 7113 | taxa de analfabetismo | 15 anos ou mais | 2016 → |

- **Por que 25 anos ou mais** para escolaridade: é a idade em que a maioria já terminou os estudos. Usar a população
  inteira contaria toda criança em idade escolar como "fundamental incompleto".
- As faixas são **acumulativas**: quem tem superior completo também concluiu médio e fundamental. Por isso os três
  destaques (fundamental 69,4%, médio 57,4%, superior 21,4%) somam mais de 100%.
- **Analfabeto**, na PNAD, é quem declara não saber ler e escrever um bilhete simples. É autodeclaração.
- **Analfabetismo funcional não entra.** O IBGE não publica mais esse indicador; o mais citado com esse nome é o INAF,
  de instituto privado, e a regra do site é só usar o que órgão público publica (a mesma razão pela qual não usamos o
  Impostômetro). O número oficial mais próximo é a parcela de adultos que **não terminou o ensino fundamental** (30,7%
  em 2025, 43,2 milhões de pessoas), que a página mostra ao lado.
- **2020 e 2021 não existem**: a PNAD não foi a campo por causa da pandemia, e a linha do gráfico pula os dois anos.
- **Não medimos "desde o Plano Real".** A PNAD Contínua anual começa em 2016 para estes recortes; os anos 1990 estavam
  na PNAD antiga, com outra metodologia, e o IBGE não publica as duas numa série única. A página diz isso em vez de
  emendar séries. O que volta mais no tempo aqui é o IDEB, de 2005, e ele mede a escola, não a população adulta.

Resultado em 2025: 69,4% dos adultos terminaram o fundamental, 57,4% o médio e 21,4% o superior; 30,7% não terminaram o
fundamental; analfabetismo de 4,9%, contra 6,7% em 2016. Entre 2016 e 2025 o superior completo subiu 6,0 pontos e o
fundamental incompleto caiu 7,7 pontos.

## Analfabetismo desde 1991 (28/10/2026)

O dono pediu "desde 1988". **Não existe dado de 1988**: o Censo mais próximo depois da Constituição é o de 1991. E não
existe uma série única — o IBGE mediu analfabetismo em três pesquisas, com metodologias diferentes, e a página mostra as
três com cores próprias em vez de emendá-las:

| Trecho | Fonte | Tabela | Observação |
|---|---|---|---|
| 1991 e 2000 | Censo Demográfico | 204 | taxa de 15+ somada por nós das faixas de idade |
| 2001–2015 | PNAD antiga | 271 | idem; 2010 não tem ponto porque foi ano de Censo e a PNAD não foi a campo |
| 2016–2025 | PNAD Contínua anual | 7113 | taxa já publicada pelo IBGE |

Resultado: **20,1% em 1991 → 4,9% em 2025**, queda de 15,2 pontos em 34 anos; a taxa de hoje é cerca de um quarto da de
1991. As duas primeiras tabelas não publicam o agregado "15 anos ou mais", então somamos as faixas de 15 anos para cima
(não alfabetizadas ÷ total) — a conta é nossa, sobre dado oficial, e está declarada na página.

**Até quando vai cada fonte.** A PNAD Contínua anual mais recente é de 2025, divulgada em 2026; a de 2026 sai em 2027. O
IDEB mais recente é de 2023, porque o INEP divulga a cada dois anos e cerca de um ano depois da prova. Não existe dado de
educação de 2026 em nenhuma das duas, e a página diz isso em vez de estimar.
