#!/usr/bin/env bash

if [ "$2" = "2" ]; then
    echo "run python-lavue tests"
    docker exec ndts python test/__main__.py $1
else
    echo "run python3-lavue tests"
    # workaround for pyfai docker problem, return I/O error status=74
    if [ "$3" = "ubuntu20.04" ] || [ "$3" = "debian11" ]  || [ "$3" = "ubuntu20.10" ] ; then
	if [ "$1" = "basic" ]; then
	    docker exec ndts sh -c 'export DISPLAY=":99.0"; python3 test/__main__.py basic; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
	elif [ "$1" = "controller" ]; then
	    docker exec ndts sh -c 'export DISPLAY=":99.0"; python3 test/__main__.py controller; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
	elif [ "$1" = "controller2" ]; then
	    docker exec ndts sh -c 'export DISPLAY=":99.0"; python3 test/__main__.py controller2; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
	elif [ "$1" = "tangosource" ]; then
	    docker exec ndts sh -c 'export DISPLAY=":99.0"; python3 test/__main__.py tangosource; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
	elif [ "$1" = "all" ]; then
	    docker exec ndts sh -c 'export DISPLAY=":99.0"; python3 test/__main__.py all; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
	elif [ "$1" = "all_splitted" ]; then
	    docker exec ndts sh -c 'export DISPLAY=":99.0"; python3 test/__main__.py basic; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
	    if [ "$?" -ne "0" ]; then exit -1; fi
	    docker exec ndts sh -c 'export DISPLAY=":99.0"; python3 test/__main__.py controller; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
	    if [ "$?" -ne "0" ]; then exit -1; fi
	    docker exec ndts sh -c 'export DISPLAY=":99.0"; python3 test/__main__.py controller2; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
	    if [ "$?" -ne "0" ]; then exit -1; fi
	    docker exec ndts sh -c 'export DISPLAY=":99.0"; python3 test/__main__.py tangosource; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
	fi
    else
	docker exec ndts python3 test/__main__.py $1
    fi
fi
if [ "$?" -ne "0" ]
then
    exit -1
fi
