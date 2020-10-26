#!/usr/bin/env bash

# workaround for incomatibility of default ubuntu 16.04 and tango configuration
if [ "$1" = "ubuntu16.04" ]; then
    docker exec -it --user root ndts sed -i "s/\[mysqld\]/\[mysqld\]\nsql_mode = NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION/g" /etc/mysql/mysql.conf.d/mysqld.cnf
fi
if [ "$1" = "ubuntu20.04" ] || [ "$1" = "ubuntu20.10" ]; then
    docker exec -it --user root ndts sed -i "s/\[mysql\]/\[mysqld\]\nsql_mode = NO_ZERO_IN_DATE,NO_ENGINE_SUBSTITUTION\ncharacter_set_server=latin1\ncollation_server=latin1_swedish_ci\n\[mysql\]/g" /etc/mysql/mysql.conf.d/mysql.cnf
fi

# workaround for a bug in debian9, i.e. starting mysql hangs
docker exec -it --user root ndts service mysql stop
if [ "$1" = "ubuntu20.04" ] || [ "$1" = "ubuntu20.10" ]; then
    docker exec -it --user root ndts /bin/bash -c 'sudo usermod -d /var/lib/mysql/ mysql'
fi
docker exec -it --user root ndts /bin/bash -c '$(service mysql start &) && sleep 30'

docker exec -it --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get -qq install -y   tango-db tango-common; sleep 10'
if [ "$?" -ne "0" ]
then
    exit -1
fi
echo "install tango servers"
docker exec -it --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive;  apt-get -qq update; apt-get -qq install -y  tango-starter tango-test liblog4j1.2-java pyqt5-dev-tools git'
if [ "$?" -ne "0" ]
then
    exit -1
fi

docker exec -it --user root ndts service tango-db restart
docker exec -it --user root ndts service tango-starter restart

if [ "$2" = "2" ]; then
    echo "install python packages"
	docker exec -it --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get -qq install -y  python-tz python-pyqtgraph python-setuptools python-zmq python-scipy python-pytango'
else
    echo "install python3 packages"
    if [ "$1" = "debian10" ] || [ "$1" = "ubuntu20.04" ] || [ "$1" = "ubuntu20.10" ] || [ "$1" = "debian11" ] ; then
	docker exec -it --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get -qq install -y  python3-tz python3-pyqtgraph python3-setuptools python3-zmq python3-scipy python3-tango'
    else
	docker exec -it --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get -qq install -y  python3-tz python3-pyqtgraph python3-setuptools python3-zmq python3-scipy python3-pytango'
    fi
fi
if [ "$?" -ne "0" ]
then
    exit -1
fi

if [ "$2" = "2" ]; then
    echo "install python-lavue"
    docker exec -it --user root ndts chown -R tango:tango .
    docker exec -it --user root ndts python setup.py build
    docker exec -it --user root ndts python setup.py install
else
    echo "install python3-lavue"
    docker exec -it --user root ndts chown -R tango:tango .
    docker exec -it --user root ndts python3 setup.py build
    docker exec -it --user root ndts python3 setup.py install
fi
if [ "$?" -ne "0" ]
then
    exit -1
fi
