# Painel — Para onde vai o dinheiro das emendas

Última revisão: 2026-10-26.

## 1. Fonte

API de Dados do Portal da Transparência (CGU), `GET /api-de-dados/emendas?ano=AAAA&pagina=N` (chave gratuita,
300 req/min). Campos: codigoEmenda, ano, tipoEmenda, autor (código), nomeAutor, numeroEmenda, localidadeDoGasto,
funcao, subfuncao, valorEmpenhado, valorLiquidado, valorPago, valorRestoInscrito/Cancelado/Pago (strings pt-BR).
`nomeAutor` pode vir com sufixo "(EX-PARLAMENTAR …)", que cortamos. O endpoint `/emendas/documentos`
(favorecido e município) é restrito à chave comum (403); destino por município é pendência.
Código: `etl/portal_transparencia/extract_emendas.py`, `transform_emendas.py`, `nomes.py`.

## 2. O que é cada número

| Campo | Significado (Lei 4.320/1964) |
|---|---|
| empenhado | reservado no orçamento e comprometido — "quanto o autor conseguiu alocar" |
| liquidado | bem entregue / serviço prestado, pagamento autorizado |
| pago | saiu do caixa — "quanto efetivamente foi recebido" |
| rp_pago | restos a pagar de anos anteriores pagos neste ano (coluna separada) |

Tipos: individual (RP 6, autor único, execução obrigatória), bancada (RP 7, coletiva por estado), comissão
(RP 8, coletiva), relator (RP 9, extinta pelo STF em dez/2022). Só individuais entram no "por autor".

## 3. Autor → parlamentar

Cruzamento por nome normalizado (sem acento, maiúsculo, sem pontos) com:
deputados da legislatura 57 (API da Câmara, 648 nomes, com situação atual) e senadores em exercício + todos
os que passaram pela legislatura (Dados Abertos do Senado, 245 nomes, inclusive suplentes).
Se não há nome igual, tentamos casamento **aproximado**: tokens significativos (sem títulos como DR./PROFESSORA/
TENENTE e sem JR./NETO/FILHO/PAI; letras dobradas reduzidas) — aceito só quando um conjunto está contido no
outro e há um único candidato com a maior interseção. Cada aproximação é registrada no log (`match_tipo`).
2025: 590 de 592 autores individuais identificados (9 aproximados); ficaram de fora "DUARTE JR." (três
candidatos) e "YURY DO PAREDAO" (nome parlamentar diferente). A página mostra quantos autores estão em
exercício, quantos deixaram o mandato ou estão licenciados, e quantos não foram identificados.

## 4. Regras editoriais

- Emenda **não** é custo do parlamentar: é orçamento público que ele direciona. Nunca é somada aos painéis de custo.
- "Alocou" = empenhado; "recebeu" = pago. Sem juízo sobre mérito ou destino.
- Nada de CPF; o autor é identificado por nome parlamentar e código da LOA.

## 5. Pendências

1. Destino por município e favorecido (CSV "Emendas parlamentares" em download-de-dados ou TransfereGov).
2. Página por autor com as emendas individuais listadas (função, localidade, valores).
