#!/usr/bin/env bash

if [ $1 = "2" ]; then
    echo "run python-lavue tests"
    docker exec -it ndts python test
else
    echo "run python3-lavue tests"
    docker exec -it ndts sh -c 'python3 test; status=$?; teststatus=$(cat "testresult.txt"); echo "Exit status: $status, Test Result: $teststatus"; exit $teststatus'
fi
if [ "$?" -ne "0" ]
then
    exit -1
fi
