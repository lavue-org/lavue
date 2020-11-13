#!/usr/bin/env bash

if [ "$1" = "2" ]; then
    echo "run python-lavue tests"
    docker exec ndts sh -c 'export DISPLAY=":99.0"; python test/__main__.py all'
    if [ "$?" -ne "0" ]; then exit -1; fi
else
    echo "run python3-lavue tests"
    # workaround for pyfai docker problem, return I/O error status=74
    docker exec ndts sh -c 'export DISPLAY=":99.0"; python3 test/__main__.py basic; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
    if [ "$?" -ne "0" ]; then exit -1; fi
    docker exec ndts sh -c 'export DISPLAY=":99.0"; python3 test/__main__.py controller; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
    if [ "$?" -ne "0" ]; then exit -1; fi
    docker exec ndts sh -c 'export DISPLAY=":99.0"; python3 test/__main__.py controller2; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
    if [ "$?" -ne "0" ]; then exit -1; fi
    docker exec ndts sh -c 'export DISPLAY=":99.0"; python3 test/__main__.py tangosuite; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
    if [ "$?" -ne "0" ]; then exit -1; fi
fi

if [ "$?" -ne "0" ]
then
    exit -1
fi
