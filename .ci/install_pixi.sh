#!/usr/bin/env bash

echo "install pixi"
docker exec  ndts /bin/bash -c 'curl -fsSL https://pixi.sh/install.sh | sh ; export PATH=/var/lib/tango/.pixi/bin:$PATH ; cp .github/workflows/pixi/pixi.toml . ; pixi shell-hook  > .sh.sh ; source .sh.sh ; pixi add   numpy "pytango=10.1.4" setuptools pip wheel argcomplete lxml pytz pyyaml  python-dateutil pninexus fabio h5py matplotlib-base blissdata pytest docutils nxsconfigserver nxswriter pymysql nxstools pymysql sardana nxsrecselector taurus'

echo "run nxselector tests"
docker exec  ndts /bin/bash -c 'source .sh.sh ;  echo "export MYTANGO_PREFIX=$CONDA_PREFIX/bin" > /home/tango/.env ;   python -m pip install . -vv --no-deps --no-build-isolation '

ERROR=$?
if [ $ERROR -ne "0" ]
then
    echo "ERROR "$ERROR
    exit 255
fi
