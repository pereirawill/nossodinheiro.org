# Painel — Quanto custa um senador

Última revisão: 2026-10-26. Espelha o painel de deputados (`painel-1-custo-deputados.md`) no que é comparável
e diz explicitamente onde não é.

## 1. Fontes (todas sem chave)

| Dado | Fonte | Código |
|---|---|---|
| Senadores em exercício (id, nome parlamentar, partido, UF, foto) | `https://legis.senado.leg.br/dadosabertos/senador/lista/atual` | `etl/senado/extract.py senadores` |
| Senadores da legislatura, inclusive quem saiu (p/ emendas) | `…/senador/lista/legislatura/57` | `extract.py legislatura` |
| Recursos utilizados por senador no ano: CEAPS por categoria, gastos não inclusos na cota, benefícios, pessoal | `https://adm.senado.gov.br/adm-dadosabertos/api/v1/senadores/{id}/recursos-utilizados?ano=AAAA&formato=json` (é o JSON da página Transparência → Senadores → Recursos utilizados) | `extract.py recursos --ano` |
| Subsídio | Decreto Legislativo 172/2022 (mesmo valor e escalonamento dos deputados), `etl/camara/config.py` | `etl/senado/transform.py` |

Alternativa para detalhe por nota: CSV anual da CEAPS `https://www.senado.leg.br/transparencia/LAI/verba/despesa_ceaps_<ano>.csv`
(latin-1, `;`), com fornecedor, documento e valor reembolsado. Ainda não usado (o JSON já traz os totais por categoria).

## 2. Fórmula

```
custo_total_estimado = subsídio (13 + 1/3 por ano, proporcional aos meses)
                     + CEAPS reembolsada (gasto real, por categoria)
                     + gastos não inclusos na cota (gasto real: diárias, passagens aéreas compradas pelo
                       Senado — ATC 2/2023 —, ressarcimento de passagens, correios, material, mídias sociais)
custo_mensal_medio   = custo_total_estimado / meses_considerados
custo_anual_projetado = subsídio de 12 meses + (CEAPS + não inclusos) × 12 / meses   (ano corrente = projeção)
```

## 3. O que NÃO entra, e por quê

- **Pessoal do gabinete.** O Senado publica a quantidade de pessoas por gabinete e por escritório de apoio e o
  vínculo (comissionado, efetivo, estagiário, terceirizado), mas não o custo por gabinete. Diferente da Câmara,
  não há um "teto de verba de gabinete" único e publicado que possamos usar como estimativa superior; o custo
  real está na folha de servidores (remuneração por servidor, com lotação), que é o próximo passo. **Por isso o
  custo do senador aqui é menor que o do deputado, e a página avisa.** Compare só subsídio + cota.
- **Auxílio-moradia e imóvel funcional.** Publicados só como "utilizou / não utilizou" por senador; o valor
  mensal do auxílio não consta na mesma fonte. Mostramos as contagens.
- Emendas (outro painel), passagens de familiares, plano de saúde: não publicados nesse JSON.

## 4. Mapeamento das categorias (rótulos do Senado → chaves do JSON)

CEAPS: aluguel de imóveis para escritório político → `aluguel_escritorio`; aquisição de material de consumo →
`material`; locomoção, hospedagem, alimentação e combustíveis → `locomocao_hospedagem`; contratação de serviços
de apoio ao parlamentar → `servicos_apoio`; divulgação da atividade parlamentar → `divulgacao`; passagens aéreas,
aquáticas e terrestres nacionais → `passagens_cota`; serviços de segurança privada → `seguranca`.
Não inclusos: diárias → `diarias`; ressarcimento de passagens → `ressarcimento_passagens`; outros materiais →
`material_outros`; correios → `correios`; impulsionamento em mídias sociais → `midias_sociais`; aquisição de
passagens aéreas (ATC 2/2023) → `passagens_aereas`. Categoria nova na fonte gera aviso no log e entra com o rótulo original.

## 5. Resultado 2026 (10 meses, 81 senadores, lido em 2026-10-26)

CEAPS R$ 23,95 mi; fora da cota R$ 8,04 mi; total estimado R$ 73,5 mi; média R$ 90,8 mil por senador por mês
(sem gabinete). 2025 (12 meses): CEAPS R$ 34,06 mi; fora da cota R$ 14,25 mi; total R$ 95,6 mi.

## 6. Pendências

1. Custo do gabinete por senador a partir da folha de remuneração do Senado (servidor × lotação).
2. Teto da CEAPS por UF (Ato da Comissão Diretora) para "% do teto".
3. Valor do auxílio-moradia do Senado com fonte primária.
