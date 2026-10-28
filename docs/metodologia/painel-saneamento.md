# Painel — Saneamento: água, esgoto e lixo

Última revisão: 2026-10-28. Código: `etl/saneamento/extract.py` → `data/public/saneamento.json`. Atualização mensal
(dia 8; os dados só mudam quando o IBGE publica). Página: `/saneamento/`.

## 1. Fonte

**IBGE, pela API do SIDRA, sem chave.** Duas pesquisas, que medem a mesma coisa por caminhos diferentes:

| Pesquisa | O que é | Anos | Tabelas usadas |
|---|---|---|---|
| Censo Demográfico | recenseia **todos** os domicílios | 1991, 2000, 2010, 2022 | água 179 / 1442 / 3391 / 6804 · esgoto 180 / 1444 / 1394 / 6805 · lixo 182 / 1447 / — / 6892 |
| PNAD Contínua anual | **amostra**, com margem de erro publicada | 2016→ (esgoto, 2019→) | água 9468 (e 6731 para o total de domicílios) · esgoto 7192 |

A PNAD Contínua publica em **mil unidades** e o Censo em unidades — a conversão está no código (`_em_unidades`).
Valores negativos no SIDRA são marcadores de ausência, não números.

## 2. O que conta como "ligado à rede" — e por que as séries não são emendadas

A categoria somada muda de um Censo para o outro, e está escrita no código e no JSON
(`censo.<ano>.<tema>.categoria`):

| Ano | Água | Esgoto |
|---|---|---|
| 1991 | rede geral, com e sem canalização interna (cat. 1033 + 1035) | instalação sanitária com rede geral, exclusiva ou compartilhada (120451 + 120460) |
| 2000 | rede geral (92853) | rede geral de esgoto ou pluvial (92855) |
| 2010 | água canalizada vinda da rede geral (12214 + 12217) | rede geral de esgoto ou pluvial (92855) |
| 2022 | rede geral de distribuição (31471) | rede geral ou rede pluvial (72110) |

Em 1991 o IBGE perguntava pela "instalação sanitária" e pelo escoadouro; em 2022 separa "rede geral" de "fossa ligada
à rede" (a categoria 46290, que soma as duas, daria 64,7% em vez de 60,4% — usamos a mais estrita e dizemos qual é).
Por isso **o gráfico mostra uma barra por Censo e uma linha separada para a PNAD**, e não uma série única desde 1991.
É a mesma regra do painel de Educação com o analfabetismo.

**Não existe 1988.** O Censo mais próximo é o de 1991, e o eixo do gráfico começa em 1988 justamente para mostrar o
vazio. A PNAD antiga (até 2015) perguntava de outro jeito e não entra.

**2020 e 2021 não existem** na PNAD Contínua: a pesquisa domiciliar foi interrompida na pandemia. A linha do gráfico é
quebrada em dois blocos, sem interpolar.

**O Censo de 2010 não tem o destino do lixo** no mesmo recorte das outras três edições; a barra cinza falta nele, e a
página diz isso.

Em tabelas com mais de uma classificação (tipo do domicílio, situação, existência de canalização), só é somada a linha
em que **as outras classificações estão no Total** — senão o mesmo domicílio entraria duas vezes. Tem teste.

## 3. O dinheiro

Função **17 (Saneamento)** da classificação funcional, em três lugares: SICONFI/DCA para municípios
(`municipios_<ano>.json`, campo `pago_saneamento`) e estados (`estados_<ano>.json`), e SIOP para a União
(`poderes_funcao_<ano>.json`). 2025: prefeituras R$ 25,4 bi, estados R$ 4,1 bi, União R$ 0,2 bi.

**As três linhas não se somam como "o investimento do país em saneamento"**: a maior parte da obra é feita pelas
companhias estaduais com tarifa e financiamento, fora do orçamento público. O resultado dessas companhias está em
`/estatais/` (Sabesp, Copasa, Sanepar, Casan, Saneago, Cagece, Cedae, Corsan, Sanasa). A União aparece pequena porque
financia (FGTS, BNDES) em vez de executar, e financiamento não é despesa da função.

## 4. "E se o dado for maquiado?" — o que dá para conferir

A página responde com três verificações, não com uma declaração de confiança:

1. **Dois instrumentos, o mesmo ano.** Censo 2022 (universo) × PNAD Contínua 2022 (amostra): esgoto na rede 60,4% ×
   62,7% (+2,3 p.p.); água 83,9% × 85,5% (+1,6 p.p.). O coeficiente de variação que o IBGE publica para a amostra é de
   0,2% — **a diferença é maior que o erro amostral**, então vem de método e definição, não de sorteio. O total de
   domicílios também bate: 72,46 milhões no Censo contra 72,7 milhões na PNAD (0,3%).
2. **As definições estão publicadas por número.** Cada valor carrega a tabela do SIDRA e a categoria somada; qualquer
   pessoa refaz a conta com outro critério.
3. **Quem pergunta a quem.** O IBGE pergunta ao morador; o SNIS recebe declaração do prestador, que é parte
   interessada (a meta de universalização é dele). Os dois nunca batem, e a diferença é um dado em si.

O que **não** dá para conferir com esta fonte, e está escrito na página: se o esgoto coletado é tratado (o IBGE não
pergunta), a qualidade da água, e quantas horas por dia há água na torneira.

## 5. Pendências

- **SNIS** (Ministério das Cidades): esgoto tratado, perdas na distribuição, investimento realizado por prestador. A
  Série Histórica é um aplicativo com formulário POST e sem rota documentada — tentamos e paramos, para não construir
  o painel sobre uma raspagem frágil. O caminho tratável são os arquivos estáticos do Diagnóstico anual.
- Atendimento por município (o Censo publica, e caberia no molde de `/municipios/`).
- Mortes e internações por doença de veiculação hídrica (DATASUS).
