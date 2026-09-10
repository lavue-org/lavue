#!/usr/bin/env bash

echo "install pixi"
command='source .sh.sh ;  QT_QPA_PLATFORM=offscreen python3 test/__main__.py $1; status=$?; teststatus=$(cat "testresult.txt") && echo "Exit status: $status, Test Result: $teststatus" && exit $teststatus'
echo "$command"
docker exec ndts bash -c "$command"
if [ "$?" != "0" ]; then exit 255; fi
