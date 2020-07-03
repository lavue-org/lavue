#!/usr/bin/env bash

if [ $1 = "2" ]; then
    echo "run python-lavue tests"
    docker exec -it ndts python test
else
    echo "run python3-lavue tests"
    docker exec -it ndts sh -c 'python3 test; status=$?; echo "Status: $status"; exit $status'
fi
if [ "$?" -ne "0" ]
then
    exit -1
fi
