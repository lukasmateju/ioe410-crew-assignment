SRC  = src
DATA = data/flight-schedules

run-simple:
	cd $(SRC) && python main.py ../$(DATA)/F01-simple.csv
	
run-normal:
	cd $(SRC) && python main.py ../$(DATA)/F02-normal.csv

run-edge:
	cd $(SRC) && python main.py ../$(DATA)/F03-edge.csv

run-stress:
	cd $(SRC) && python main.py ../$(DATA)/F04-stress.csv

run-real:
	cd $(SRC) && python main.py ../$(DATA)/F05-real.csv

run-file:
	cd $(SRC) && python main.py ../$(DATA)/$(F)

save-simple:
	cd $(SRC) && python main.py ../$(DATA)/F01-simple.csv --save

save-normal:
	cd $(SRC) && python main.py ../$(DATA)/F02-normal.csv --save

save-edge:
	cd $(SRC) && python main.py ../$(DATA)/F03-edge.csv --save

save-stress:
	cd $(SRC) && python main.py ../$(DATA)/F04-stress.csv --save

save-real:
	cd $(SRC) && python main.py ../$(DATA)/F05-real.csv --save

save-file:
	cd $(SRC) && python main.py ../$(DATA)/$(F) --save

generate:
	cd data && python dataRandom.py --flights "$(N)" --output "$(O)"

check:
	flake8 $(SRC)/sc_model.py $(SRC)/utils.py $(SRC)/main.py $(SRC)/config.py

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
 
.PHONY: run-simple run-normal run-edge run-stress run-real run-file
.PHONY: save-simple save-normal save-edge save-stress save-real save-file
.PHONY: generate check clean