# Painel — Câmbio: o real frente a outras moedas (dentro de Inflação)

Última revisão: 2026-10-27. Código: `etl/cambio/extract.py` → `data/public/cambio.json`. Atualização em dias úteis (14:40 BRT, depois
do fechamento do PTAX). Aparece como seção da página `/inflacao/`.

## 1. Fontes (Banco Central, sem chave)

| Série | O que é | Desde |
|---|---|---|
| SGS 3698 | dólar (venda), **média mensal** | julho de 1994, quando o real entrou em circulação |
| SGS 11752 | índice da **taxa de câmbio efetiva real**, deflacionado pelo IPCA | julho de 1994 |
| PTAX (Olinda) | cotação de **fechamento** de cada moeda, em reais | consultamos hoje, 1, 5 e 10 anos atrás |

## 2. Regras e limites

- **Câmbio não é inflação.** A página diz isso em destaque: o dólar subir não significa que o real perdeu aquele tanto de poder de
  compra dentro do país, e o próprio dólar perde valor lá fora. Comparar a cotação de 1994 com a de hoje mistura a inflação
  brasileira com a americana do período.
- Por isso a seção traz **dois gráficos**: a cotação nominal (SGS 3698) e o índice de câmbio efetivo real (SGS 11752), que corrige a
  inflação dos dois lados e compara o real com uma cesta de moedas dos principais parceiros. **Quanto maior o índice, mais barato o
  real.** Não afirmamos o ano-base do índice porque o Banco Central não o devolve na API; usamos os extremos da própria série como
  referência (máximo 171 em out/2002, mínimo 67 em abr/1997).
- **O PTAX só cobre dez moedas** (AUD, CAD, CHF, DKK, EUR, GBP, JPY, NOK, SEK, USD). **Yuan chinês e peso argentino não estão lá**,
  embora China e Argentina sejam parceiros comerciais grandes; a ausência está declarada na página.
- Cotações em dias sem pregão: o extrator procura até 12 dias para trás a partir da data pedida.
- Usamos sempre a **cotação de venda**; a diferença para a de compra é de centavos e não muda nada na leitura.

## 3. Pendências

1. Yuan e peso argentino por outra fonte oficial (o próprio BCB publica paridades em outro serviço, a avaliar).
2. Comparar a desvalorização nominal com a inflação americana (índice de preços do BLS) para a mesma janela.
3. Série longa de reservas internacionais e de juros, que ajudam a explicar a trajetória.
