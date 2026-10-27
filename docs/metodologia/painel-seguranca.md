# Painel — Segurança: ocorrências por estado e município

Última revisão: 2026-10-26. Código: `etl/seguranca/extract.py` → `data/public/seguranca.json`. Atualização mensal (dia 9); ano de referência = último ano fechado.

## 1. Fontes

- **MJSP, Sinesp VDE** (Validador de Dados Estatísticos), "Base de Dados dos Gestores Estaduais": `bancovde-<ano>.xlsx` (gov.br/mj), um por ano desde 2015. Colunas: uf, municipio, evento, data_referencia (mês), agente, arma, faixa_etaria, feminino, masculino, nao_informado, total_vitima, total, total_peso, abrangencia (Estadual / Polícia Federal / PRF). Download grande (~25 MB) que o servidor costuma cortar; 4 tentativas.
- **IBGE**, estimativas de população (SIDRA 6579) por UF e município, do mesmo ano dos eventos (ou a última publicada).

## 2. Regras

- Só **abrangência Estadual** (polícias civis e militares). PF e PRF são bases separadas; não somamos.
- **Vítimas** para mortes (homicídio doloso, feminicídio, latrocínio, lesão corporal seguida de morte, morte por intervenção de agente do Estado, trânsito, suicídio, tentativa de homicídio); **ocorrências** (`total`) para roubo/furto de veículo, roubo de carga e estupro.
- **Não criamos "mortes violentas intencionais"**: cada evento aparece separado, como o MJ publica. Feminicídio, latrocínio e intervenção policial são categorias próprias; somar sem a regra de cada estado dobraria contagens.
- **Município**: só o que o estado registrou por município. "NÃO INFORMADO" entra no total da UF, não no ranking. Roubo/furto de veículo, estupro e intervenção policial só vêm por UF. Casamento com o IBGE por (UF, nome normalizado); nomes sem casamento (grafias antigas, p. ex. "Açu"/"Assú") são contados no JSON (`municipios_sem_populacao`).
- **Taxa** = eventos no ano ÷ população × 100 mil. Ranking municipal só para **100 mil habitantes ou mais** e capitais.
- Série 2015 → ano: homicídio doloso, feminicídio e roubo de veículo por UF (absolutos), lidos de cada arquivo anual.
- `meses` = quantos meses do ano a UF informou homicídio doloso (cobertura).

## 3. Leitura honesta

Registro policial ≠ medição independente: depende de denúncia e da alimentação de cada estado; o MJ avisa que os números podem mudar após publicação. Taxa baixa pode ser pouca violência ou pouco registro. Comparações entre anos antigos sofrem de cobertura menor.

## 4. Pendências

1. DATASUS/SIM (óbitos por agressão, Ministério da Saúde): segunda fonte para mortes, independente do registro policial.
2. Dados mensais do ano corrente (parcial) e por sexo/idade da vítima (colunas já existem no VDE).
3. Efetivo policial e gasto com segurança por UF (SICONFI, função 06) ao lado das taxas.
