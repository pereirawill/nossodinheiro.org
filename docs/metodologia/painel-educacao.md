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
