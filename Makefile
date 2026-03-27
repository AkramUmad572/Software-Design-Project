.PHONY: help install run clean

help:
	@echo "Targets:"
	@echo "  make install   - install Python deps"
	@echo "  make run       - run the Flask app"
	@echo "  make clean     - remove local sqlite db (dev only)"

install:
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt

run:
	python main.py

clean:
	@python -c "import os; p='database.db'; print('Removing',p) if os.path.exists(p) else print('No database.db found'); os.remove(p) if os.path.exists(p) else None"
