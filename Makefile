ANO ?= 2026
FONTE ?= bulk

etl: ## extrai + transforma + gráfico
	python -m etl.camara.extract deputados
	@if [ "$(FONTE)" = "bulk" ]; then python -m etl.camara.extract ceap-bulk --ano $(ANO); \
	else python -m etl.camara.extract despesas --ano $(ANO); fi
	python -m etl.camara.transform --ano $(ANO) --fonte $(FONTE)
	python -m etl.camara.chart --ano $(ANO) --top 20 --por deputado
	python -m etl.camara.chart --ano $(ANO) --top 20 --por partido
	cp data/public/*.json site/public/data/

test:
	python -m pytest tests/ -q

site:
	cd site && npm install && npm run build
.PHONY: etl test site
