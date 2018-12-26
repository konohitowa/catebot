#!/bin/bash

. ./venv/bin/activate

while [ 1 ]; do

	python catebot.py status.db $*
	sleep 60

done
