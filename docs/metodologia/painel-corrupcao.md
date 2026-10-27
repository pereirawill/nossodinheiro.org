# Painel — Corrupção: punições e sanções registradas

Última revisão: 2026-10-27. Código: `etl/corrupcao/extract.py` → `data/public/corrupcao.json`. Atualização mensal (dia 13). Página: `/corrupcao/`.

## 1. Fontes

Portal da Transparência, dados abertos, ZIP com CSV em latin-1, publicado com data no caminho
(`portaldatransparencia.gov.br/download-de-dados/<cadastro>/AAAAMMDD`; o extrator tenta até 8 dias para trás):

| Cadastro | O que é | Registros em 26/10/2026 |
|---|---|---|
| CEIS | Cadastro de Empresas Inidôneas e Suspensas: impedidos de contratar com o poder público (Leis 8.666/14.133, 10.520 e 8.429) | 23.811 |
| CNEP | Cadastro Nacional de Empresas Punidas pela Lei Anticorrupção (12.846/2013), com valor da multa | 1.858 |
| CEAF | Cadastro de Expulsões da Administração Federal: demissão, cassação de aposentadoria, destituição | 4.044 |
| Acordos de leniência | Acordos da CGU com empresas (Lei 12.846/2013) | 152 |

O Índice de Percepção da Corrupção (Transparência Internacional) aparece no fim da página, reaproveitado de `rankings.json`,
e está rotulado como ONG e como medida de **percepção**.

## 2. Privacidade

O CEIS e o CNEP trazem **CPF de pessoas físicas em claro**. Nada disso é persistido: o extrator publica apenas contagens e somas.
De nomes próprios saem só os de **órgãos públicos** e, nos acordos de leniência, a **razão social das empresas** — que é o objeto
do acordo e é publicada pela CGU. Os nomes de servidores expulsos, embora públicos no CEAF, ficam de fora.

## 3. Regras e limites

- **Não é medida de corrupção.** É o que foi punido e registrado. Mais sanções num estado pode significar mais fiscalização.
- O recorte por estado usa a coluna **"UF ÓRGÃO SANCIONADOR"** — onde fica o órgão que puniu, não a sede da empresa punida.
  857 registros do CEIS vêm sem UF e ficam fora do mapa (declarado na página).
- **Vigente × encerrada**: a sanção vale até a "DATA FINAL SANÇÃO"; sem data, é por prazo indeterminado (caso da inidoneidade) ou
  o órgão não informou. Em out/2026: 23.242 das 23.811 do CEIS ainda valiam, 2.029 delas sem prazo informado. O número do topo da
  página é o de **vigentes**; o mapa e as barras por ano contam todo o histórico, porque o cadastro é histórico.
- O ano é o de **início da sanção**, não o do fato. A alta recente reflete também a digitalização do cadastro e a adesão de
  órgãos estaduais e municipais.
- O CEIS reúne sanções das três esferas (estadual 9.863, federal 8.509, municipal 5.289 em out/2026); o CEAF é **só federal** —
  não existe cadastro nacional de expulsões de servidores estaduais e municipais.
- **Artigos citados**: uma decisão do CEAF cita vários artigos do Estatuto do Servidor na mesma linha
  ("ART. 132, XI - CORRUPÇÃO;ART. 132, IV - IMPROBIDADE ADMINISTRATIVA"), então as contagens por fundamento se sobrepõem e somam
  mais que o total de casos. A página diz isso.
- Decisões podem ser revertidas na Justiça; o cadastro reflete a situação informada pelo órgão.

## 4. Pendências

1. Valor devolvido nos acordos de leniência: está em texto livre no campo "TERMOS DO ACORDO", sem campo numérico.
2. CEPIM (entidades sem fins lucrativos impedidas): o download devolveu 403 no teste de 27/10/2026.
3. TCU: lista de responsáveis com contas julgadas irregulares (fonte própria do tribunal, formato a avaliar).
4. Improbidade na Justiça estadual (CNJ) e processos criminais: não há base nacional aberta com desfecho.
