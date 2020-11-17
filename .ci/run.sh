#!/usr/bin/env bash

if [ "$1" = "2" ]; then
    echo "run python-lavue tests"
    command='export DISPLAY=":99.0"; python test/__main__.py '$2
else
    echo "run python3-lavue tests"
    # workaround for pyfai docker problem, return I/O error status=74
    command='export DISPLAY=":99.0"; python3 test/__main__.py '$2'; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
fi
echo "$command"
docker exec ndts bash -c "$command"
if [ "$?" -ne "0" ]; then exit -1; fi
