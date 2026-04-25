SRC  = src
DATA = data/flight-schedules

run-simple:
	cd $(SRC) && python main.py ../$(DATA)/F01-simple.csv
	
run-normal:
	cd $(SRC) && python main.py ../$(DATA)/F02-normal.csv

run-real:
	cd $(SRC) && python main.py ../$(DATA)/F03-real.csv

run-file:
	cd $(SRC) && python main.py ../$(DATA)/$(F)

viz-simple:
	cd $(SRC) && python main.py ../$(DATA)/F01-simple.csv --viz

viz-normal:
	cd $(SRC) && python main.py ../$(DATA)/F02-normal.csv --viz

viz-real:
	cd $(SRC) && python main.py ../$(DATA)/F03-real.csv --viz

viz-file:
	cd $(SRC) && python main.py ../$(DATA)/$(F) --viz

save-file:
	cd $(SRC) && python main.py ../$(DATA)/$(F) --save

save-viz-file:
	cd $(SRC) && python main.py ../$(DATA)/$(F) --save --viz

generate:
	cd data && python dataRandom.py --flights "$(N)" --output "$(O)"

check:
	flake8 $(SRC)/sc_model.py $(SRC)/utils.py $(SRC)/main.py $(SRC)/config.py

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
 
.PHONY: run-simple run-normal run-real run-file
.PHONY: viz-simple viz-normal viz-real viz-file
.PHONY: save-simple save-normal save-real save-file save-viz-file
.PHONY: generate check clean
