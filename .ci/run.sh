#!/usr/bin/env bash

if [ "$1" = "2" ]; then
    echo "run python-lavue tests"
    if [ "$2" = "basic" ]; then
	docker exec ndts sh -c 'export DISPLAY=":99.0"; python test/__main__.py basic'
    fi
    if [ "$?" -ne "0" ]; then exit -1; fi
    if [ "$2" = "controller" ]; then
	docker exec ndts sh -c 'export DISPLAY=":99.0"; python test/__main__.py controller'
    fi
    if [ "$?" -ne "0" ]; then exit -1; fi
    if [ "$2" = "controller2" ]; then
	docker exec ndts sh -c 'export DISPLAY=":99.0"; python test/__main__.py controller2'
    fi
    if [ "$?" -ne "0" ]; then exit -1; fi
    if [ "$2" = "tangosource" ]; then
	docker exec ndts sh -c 'export DISPLAY=":99.0"; python test/__main__.py tangosource'
    fi
    if [ "$?" -ne "0" ]; then exit -1; fi
    if [ "$2" = "httpsource" ]; then
	docker exec ndts sh -c 'export DISPLAY=":99.0"; python test/__main__.py httpsource'
    fi
    if [ "$?" -ne "0" ]; then exit -1; fi
    if [ "$2" = "all" ]; then
	docker exec ndts sh -c 'export DISPLAY=":99.0"; python test/__main__.py all'
    fi
    if [ "$?" -ne "0" ]; then exit -1; fi
else
    echo "run python3-lavue tests"
    if [ "$2" = "basic" ]; then
    # workaround for pyfai docker problem, return I/O error status=74
	docker exec ndts sh -c 'export DISPLAY=":99.0"; python3 test/__main__.py basic; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
    fi
    if [ "$?" -ne "0" ]; then exit -1; fi
    if [ "$2" = "controller" ]; then
	docker exec ndts sh -c 'export DISPLAY=":99.0"; python3 test/__main__.py controller; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
    fi
    if [ "$?" -ne "0" ]; then exit -1; fi
    if [ "$2" = "controller2" ]; then
	docker exec ndts sh -c 'export DISPLAY=":99.0"; python3 test/__main__.py controller2; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
    fi
    if [ "$?" -ne "0" ]; then exit -1; fi
    if [ "$2" = "tangosource" ]; then
	docker exec ndts sh -c 'export DISPLAY=":99.0"; python3 test/__main__.py tangosource; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
    fi
    if [ "$?" -ne "0" ]; then exit -1; fi
    if [ "$2" = "httpsource" ]; then
	docker exec ndts sh -c 'export DISPLAY=":99.0"; python3 test/__main__.py httpsource; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
    fi
    if [ "$?" -ne "0" ]; then exit -1; fi
    if [ "$2" = "all" ]; then
	docker exec ndts sh -c 'export DISPLAY=":99.0"; python3 test/__main__.py all; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
    fi
    if [ "$?" -ne "0" ]; then exit -1; fi
fi
