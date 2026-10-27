# Painel — Obras: o cadastro federal de investimentos

Última revisão: 2026-10-27. Código: `etl/obras/extract.py` → `data/public/obras.json`. Atualização mensal (dia 15). Página: `/obras/`.

## 1. Fonte

**Obrasgov/CIPI** (Cadastro Integrado de Projetos de Investimento), API pública do Ministério da Gestão e da Inovação, sem chave:

| Endpoint | O que traz |
|---|---|
| `api.obrasgov.gestao.gov.br/obrasgov/api/projeto-investimento` | uma linha por obra: nome, descrição, situação, UF, espécie, natureza, datas prevista e efetiva, eixo/tipo/subtipo, tomadores, executores, repassadores e `fontesDeRecurso` com o valor **previsto** |
| `…/obrasgov/api/execucao-financeira` | empenhos federais por obra (`idProjetoInvestimento`, `valorEmpenho`), somados por obra |

**O host mudou**: `api-publica.obrasgov.gestao.gov.br` devolve 404 desde (pelo menos) out/2026; o que responde é `api.obrasgov…`.
Era por isso que este painel estava parado na fila desde o início do projeto.

## 2. Limites da API (medidos em 27/10/2026)

- Página de **no máximo 50 registros**; 100 ou mais devolve HTTP 500.
- **~85 segundos por requisição**, com 500 e 524 ocasionais. São ~1.000 chamadas no total, daí o `timeout-minutes: 240` no workflow
  e 10 requisições em paralelo.
- `totalElements` do endpoint de obras é **falso**: repete o que já foi servido (pedindo 1 registro, diz que o total é 1). Por isso
  andamos as páginas até o fim em vez de confiar no total. O endpoint de empenhos, esse sim, traz o total real (20.752 em out/2026).
- Filtros por `uf` e `situacao` devolvem 500; a filtragem é nossa, depois de baixar.
- A coleta é **retomável**: grava um `.parcial.gz` a cada bloco e um `.pagina` com o ponto de retomada. Se o servidor derrubar,
  rodar de novo continua de onde parou.
- A coleta só termina após **dois blocos seguidos** respondendo 200 com lista vazia: sob carga, o Obrasgov devolve 200 com conteúdo
  vazio em vez de erro, e parar no primeiro bloco vazio truncaria a base silenciosamente. Além disso, o extrator falha se vierem
  menos de 15 mil obras (o cadastro tem ~25 mil; o TCU contou 22.621 em abr/2025).

## 3. Regras

- **Paradas** = situação "Paralisada" ou "Inacabada", como o órgão declarou. Não inventamos categoria.
- **Previsto ≠ gasto**: `valorInvestimentoPrevisto` é o planejado; `valorEmpenho` é o que a União comprometeu no orçamento. As duas
  colunas andam separadas na página, e nenhuma é "valor já gasto" (pago) — o cadastro não publica liquidação por obra.
- **Tempo parado**: `dataSituacao` é a data em que o órgão **atualizou o status**, não o dia em que a obra parou. A página mostra
  "sem atualizar a situação" e, à parte, "atraso do prazo" (data final prevista × hoje). Nunca escrevemos "parada há X anos".
- **Campos declarados**: `qdtEmpregosGerados` e `populacaoBeneficiada` são preenchidos pelo próprio órgão ao cadastrar a obra; são
  estimativas de projeto, não medição. Por isso não entram em número de destaque nem em conclusão.
- **Cobertura**: só obras com participação de recurso federal. Obra tocada apenas com dinheiro estadual ou municipal pode não estar
  no cadastro — dito no aviso da página.

## 4. Pendências

1. Valor **liquidado e pago** por obra (o cadastro só tem empenho); avaliar cruzamento com o Portal da Transparência.
2. Histórico de situação (há quanto tempo cada obra está parada de fato), que a API não expõe.
3. Obras de estados e municípios fora do CIPI.
4. Cruzar com o relatório de obras paralisadas do TCU para reconciliar as contagens.
