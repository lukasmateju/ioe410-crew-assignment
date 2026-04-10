SRC  = src
DATA = data/flight-schedules

# Main Dataset Aliases
SCHEDULES = simple normal edge stress real
simple  := F01-simple.csv
normal  := F02-normal.csv
edge    := F03-edge.csv
stress  := F04-stress.csv
real    := F05-real.csv

resolve = $(if $($(F)),$($(F)),$(F))

run:
	@cd $(SRC) && python main.py ../$(DATA)/$(call resolve)

run-save:
	@cd $(SRC) && python main.py ../$(DATA)/$(call resolve) --save

generate:
	cd data && python dataRandom.py --flights "$(N)" --output "$(O)"

check:
	flake8 $(SRC)/sc_model.py $(SRC)/utils.py $(SRC)/main.py $(SRC)/config.py

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

.PHONY: run run-save generate check clean