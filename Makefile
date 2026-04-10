SRC = src
DATA = data/flight-schedules

check:
	flake8 $(SRC)/sc_model.py $(SRC)/dp_model.py $(SRC)/utils.py $(SRC)/main.py $(SRC)/config.py

run:
	cd $(SRC) && python main.py

run-save:
	cd $(SRC) && python main.py --save

run-file:
	cd $(SRC) && python main.py ../$(DATA)/$(F)

run-file-save:
	cd $(SRC) && python main.py ../$(DATA)/$(F) --save

simple:
	cd $(SRC) && python main.py ../$(DATA)/F01-simple.csv

normal:
	cd $(SRC) && python main.py ../$(DATA)/F02-normal.csv

edge:
	cd $(SRC) && python main.py ../$(DATA)/F03-edge.csv

stress:
	cd $(SRC) && python main.py ../$(DATA)/F04-stress.csv

real:
	cd $(SRC) && python main.py ../$(DATA)/F05-real.csv

all: simple normal edge stress real

generate:
	cd data && python dataRandom.py --flights "$(F)" --output "$(O)"

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete