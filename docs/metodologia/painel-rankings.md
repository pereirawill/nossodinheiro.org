# Painel — Rankings: onde o Brasil está

Última revisão: 2026-10-26. Código: `etl/rankings/extract.py` → `data/public/rankings.json`. Atualização mensal (dia 1).

## 1. Regra e exceção

O site publica "só o que os órgãos públicos publicam". Nos rankings, "órgão público" vira "organismo oficial":
Banco Mundial, PNUD (ONU), UNODC (ONU). Índices de ONGs entram só quando são a referência usada por governos e
imprensa e vêm marcados como **ONG** no cartão (hoje: Transparência Internacional). Não há ranking de "bom ou ruim"
nosso: a posição é a que a fonte dá, ou a ordenação direta do valor publicado.

## 2. Fontes e índices

| Índice | Fonte (tipo) | Como obtemos | Posição |
|---|---|---|---|
| PIB (US$ correntes) | Banco Mundial, `NY.GDP.MKTP.CD` (oficial) | API v2, `mrv=6`, último ano com dado por país | calculada por nós (maior = 1º) |
| PIB per capita | Banco Mundial, `NY.GDP.PCAP.CD` | idem | calculada |
| Expectativa de vida | Banco Mundial, `SP.DYN.LE00.IN` | idem | calculada |
| Desigualdade (Gini) | Banco Mundial, `SI.POV.GINI` | idem; só países com pesquisa recente (~116) | calculada (menor = 1º) |
| Gasto público em educação (% PIB) | Banco Mundial, `SE.XPD.TOTL.GD.ZS` | idem | calculada |
| Homicídios por 100 mil | UNODC via Banco Mundial, `VC.IHR.PSRC.P5` | idem; anos variam por país | calculada (menor = 1º) |
| IDH 2023 | PNUD, RDH 2025, CSV `HDR25_Composite_indices_complete_time_series.csv` | `hdi_2023`, `hdi_rank_2023` | **oficial** do relatório |
| Percepção da corrupção 2025 | Transparência Internacional (ONG), `CPI2025_Results.xlsx` | planilha oficial (leitor xlsx próprio, sem dependências) | **oficial** do relatório |

Países = os 217 que o Banco Mundial classifica fora de "Aggregates"; nomes em português pelo IBGE (API de localidades,
ISO-3166-3), com o nome em inglês do Banco Mundial como reserva quando o IBGE não lista (territórios).

## 3. Leitura honesta da posição

- "Xº de N" é entre os países **com dado** naquele índice; N varia de 116 (Gini) a 217 (expectativa de vida).
- Em índices do Banco Mundial, o ano pode variar por país (último disponível); o cartão avisa e a tabela mostra o ano.
- PIB em dólares correntes muda com o câmbio; não é medida de bem-estar. PIB per capita e IDH são as comparações de nível de vida.

## 4. Pendentes (sem arquivo aberto legível por máquina na fonte, em 26/10/2026)

Liberdade econômica (Heritage Foundation, site só com visualização), Freedom in the World (Freedom House deixou de
publicar a planilha atual gratuitamente), PISA (OCDE, API SDMX a explorar), Global Peace Index (IEP, PDF). Entram quando
houver forma de atualizar automaticamente citando a fonte primária.
