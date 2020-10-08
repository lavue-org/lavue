#!/usr/bin/env bash

if [ "$2" = "2" ]; then
    echo "run python-lavue tests"
    docker exec -it ndts python test/__main__.py $1
else
    echo "run python3-lavue tests"
    # workaround for pyfai docker problem, return I/O error status=74
    if [ "$3" = "ubuntu20.04" ]; then
	if [ "$1" = "basic" ]; then
	    docker exec -it ndts sh -c 'python3 test/__main__.py basic; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
	elif [ "$1" = "tangosource" ]; then
	    docker exec -it ndts sh -c 'python3 test/__main__.py tangosource; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
	elif [ "$1" = "all" ]; then
	    docker exec -it ndts sh -c 'python3 test/__main__.py all; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
	fi
    else
	docker exec -it ndts python3 test/__main__.py $1
    fi
fi
if [ "$?" -ne "0" ]
then
    exit -1
fi
