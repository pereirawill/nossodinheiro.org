# Painel — Mortes no trânsito

Última revisão: 2026-10-29. Código: `etl/transito/extract.py` → `data/public/transito.json`. Atualização mensal
(dia 9; o dado muda uma vez por ano). Página: `/transito/`.

## 1. Por que não está dentro de Segurança

O painel de Segurança conta **mortes violentas intencionais** — alguém quis matar. A morte no trânsito é, na
definição legal, **não intencional**: somá-la ao total da violência inflaria o número. São painéis separados, e a
página de trânsito traz os dois lado a lado para quem quiser comparar a ordem de grandeza: 37.150 mortes no trânsito
em 2024 contra 39.555 mortes violentas intencionais em 2025.

## 2. Fonte principal: o atestado de óbito

**IBGE, indicador ODS 3.6.1** (SIDRA, tabela **4408**), que vem do **Sistema de Informações sobre Mortalidade (SIM)**
do Ministério da Saúde. Traz óbitos (variável 11728) e taxa por 100 mil (9734), por ano (**2000→2024**), sexo
(classificação 2), faixa de idade (58) e unidade da federação.

É a contagem mais completa: alcança quem morre dias depois, no hospital, e não depende de registro policial.

## 3. A segunda contagem, e a diferença

O **Sinesp VDE** (Ministério da Justiça), que já alimenta `/seguranca/`, conta as mortes **registradas pelas
polícias**: 25.074 em 2025, contra 37.150 do atestado de óbito em 2024 — o registro policial fica **32% abaixo**.
Parte da diferença é conhecida (a vítima que morre depois no hospital não volta ao registro); o resto não sabemos
medir. A página publica as duas, com os anos de referência diferentes declarados, e a diferença entrou em
`/conferir/` como conferência **sem explicação completa**.

## 4. Comparação internacional

Usa a **estimativa da OMS** publicada pelo Banco Mundial (`SH.STA.TRAF.P5`), já coletada em `etl/rankings`. A OMS
corrige o sub-registro de cada país para torná-los comparáveis — por isso o valor do Brasil ali (16,0 por 100 mil,
2019) **não é** o do atestado de óbito (17,5 em 2024), e a página diz isso em vez de apresentar os dois como a mesma
medida. A série da OMS é republicada de tempos em tempos; o ano de referência fica visível em cada linha.

## 5. O que a página não faz

- **Não atribui a queda desde o pico de 2012 a nenhuma causa.** Lei Seca (2008), endurecimento do teste do bafômetro
  (2012) e crescimento da frota acontecem juntos; separar o efeito de cada um exige estudo, não é um dado público.
- **Não explica por que a taxa é maior em Tocantins e Piauí** do que no Rio de Janeiro. A relação com rodovia,
  velocidade e tempo de socorro é plausível e não está no dado.
- **Não traz tipo de veículo nem de vítima** (motociclista, pedestre) — o indicador ODS publicado não abre por isso;
  o SIM bruto (microdados do DATASUS) abre, e fica como pendência.
