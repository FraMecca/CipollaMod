PID :=  $(shell ps aux | grep 'main.py' | awk '{print $2}' | head -n 1)

all:
	rm ./src/spyd/utils/tracing.pickle tracing.log -f
	PYTHONPATH=$(PWD)/src python3 main.py --servdir ./src/spyd/data/
