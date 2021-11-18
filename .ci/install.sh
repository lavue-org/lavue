#!/usr/bin/env bash

echo "restart mysql"
# workaround for a bug in debian9, i.e. starting mysql hangs
if [ "$1" = "debian11" ]; then
    docker exec --user root ndts service mariadb restart
else
    docker exec --user root ndts service mysql stop
    if [ "$1" = "ubuntu20.04" ] || [ "$1" = "ubuntu20.10" ] || [ "$1" = "ubuntu21.04" ] || [ "$1" = "ubuntu21.10" ]; then
       # docker exec --user root ndts /bin/bash -c 'mkdir -p /var/lib/mysql'
       # docker exec --user root ndts /bin/bash -c 'chown mysql:mysql /var/lib/mysql'
       docker exec --user root ndts /bin/bash -c 'usermod -d /var/lib/mysql/ mysql'
    fi
    docker exec  --user root ndts /bin/bash -c '$(service mysql start &) && sleep 30'
fi


echo "install tango-db tango-common"
docker exec  --user root ndts /bin/bash -c 'apt-get -qq update; apt-get -qq install -y tango-db tango-common; sleep 10'
if [ "$?" != "0" ]; then exit -1; fi


docker exec  --user root ndts mkdir -p /tmp/runtime-tango
docker exec  --user root ndts chown -R tango:tango /tmp/runtime-tango

echo "start Xvfb :99 -screen 0 1024x768x24 &"
docker exec  --user root ndts /bin/bash -c 'export DISPLAY=":99.0"; Xvfb :99 -screen 0 1024x768x24 &'
if [ "$?" != "0" ]; then exit -1; fi

echo "install tango-starter tango-test and pytango"
if [ "$2" = "2" ]; then
	docker exec  --user root ndts /bin/bash -c 'apt-get -qq update; apt-get -qq install -y   python-pytango   tango-starter tango-test'
else
    if [ "$1" = "debian10" ] || [ "$1" = "ubuntu20.04" ] || [ "$1" = "ubuntu20.10" ] || [ "$1" = "ubuntu21.04" ] || [ "$1" = "ubuntu21.10" ] || [ "$1" = "debian11" ] ; then
	docker exec  --user root ndts /bin/bash -c 'apt-get -qq update; apt-get -qq install -y  python3-tango tango-starter tango-test'
    else
	docker exec  --user root ndts /bin/bash -c 'apt-get -qq update; apt-get -qq install -y  python3-pytango tango-starter tango-test'
    fi
fi
if [ "$?" != "0" ]; then exit -1; fi

# restart services
docker exec  --user root ndts service tango-db restart
docker exec  --user root ndts service tango-starter restart

docker exec  --user root ndts chown -R tango:tango .

if [ "$2" = "2" ]; then
    echo "install python-lavue"
    docker exec  --user root ndts python setup.py build
    docker exec  --user root ndts python setup.py install
else
    echo "install python3-lavue"
    docker exec  --user root ndts python3 setup.py build
    docker exec  --user root ndts python3 setup.py install
fi
if [ "$?" != "0" ]; then exit -1; fi
