ACTIVATE_VENV = cd .venv/Scripts & activate.bat & cd ../.. &

.PHONY: main
main:
	$(ACTIVATE_VENV) cd src/ & python main.py