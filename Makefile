SRC = src
DATA = data/flight-schedules

check:
	flake8 $(SRC)/sc_model.py $(SRC)/dp_model.py $(SRC)/utils.py $(SRC)/main.py $(SRC)/config.py

run:
	cd $(SRC) && python main.py

run-save:
	cd $(SRC) && python main.py --save

generate:
	cd data && python dataRandom.py --flights "$(F)" --output "$(O)"

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete