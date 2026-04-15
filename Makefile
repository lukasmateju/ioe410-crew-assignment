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

save-file:
	cd $(SRC) && python main.py ../$(DATA)/$(F) --save

generate:
	cd data && python dataRandom.py --flights "$(N)" --output "$(O)"

check:
	flake8 $(SRC)/sc_model.py $(SRC)/utils.py $(SRC)/main.py $(SRC)/config.py

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
 
.PHONY: run-simple run-normal run-real run-file
.PHONY: save-simple save-normal save-real save-file
.PHONY: generate check clean