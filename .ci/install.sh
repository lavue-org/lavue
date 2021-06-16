#!/usr/bin/env bash

# workaround for incomatibility of default ubuntu 16.04 and tango configuration
if [ "$1" = "ubuntu16.04" ]; then
    docker exec  --user root ndts sed -i "s/\[mysqld\]/\[mysqld\]\nsql_mode = NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION/g" /etc/mysql/mysql.conf.d/mysqld.cnf
fi
if [ "$1" = "ubuntu20.04" ] || [ "$1" = "ubuntu20.10" ]|| [ "$1" = "ubuntu21.04" ]; then
    docker exec  --user root ndts sed -i "s/\[mysql\]/\[mysqld\]\nsql_mode = NO_ZERO_IN_DATE,NO_ENGINE_SUBSTITUTION\ncharacter_set_server=latin1\ncollation_server=latin1_swedish_ci\n\[mysql\]/g" /etc/mysql/mysql.conf.d/mysql.cnf
fi

# workaround for a bug in debian9, i.e. starting mysql hangs
if [ "$1" = "debian11" ]; then
    docker exec --user root ndts service mariadb restart
else
    docker exec --user root ndts service mysql stop
    if [ "$1" = "ubuntu20.04" ] || [ "$1" = "ubuntu20.10" ] || [ "$1" = "ubuntu21.04" ]; then
	# docker exec --user root ndts /bin/bash -c 'mkdir -p /var/lib/mysql'
	# docker exec --user root ndts /bin/bash -c 'chown mysql:mysql /var/lib/mysql'
	docker exec --user root ndts /bin/bash -c 'usermod -d /var/lib/mysql/ mysql'
    fi
    docker exec  --user root ndts /bin/bash -c '$(service mysql start &) && sleep 30'
fi

docker exec  --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get -qq install -y tango-db tango-common; sleep 10'
if [ "$?" -ne "0" ]; then exit -1; fi

docker exec  --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get -qq install -y xvfb  libxcb1 libx11-xcb1 libxcb-keysyms1 libxcb-image0 libxcb-icccm4 libxcb-render-util0 xkb-data'
if [ "$?" -ne "0" ]; then exit -1; fi

docker exec  --user root ndts mkdir -p /tmp/runtime-tango
docker exec  --user root ndts chown -R tango:tango /tmp/runtime-tango

if [ "$?" -ne "0" ]; then exit -1; fi
echo "start Xvfb :99 -screen 0 1024x768x24 &"
docker exec  --user root ndts /bin/bash -c 'export DISPLAY=":99.0"; Xvfb :99 -screen 0 1024x768x24 &'
if [ "$?" -ne "0" ]; then exit -1; fi

echo "install tango servers"
docker exec --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive;  apt-get -qq update; apt-get -qq install -y  tango-starter tango-test liblog4j1.2-java pyqt5-dev-tools git'
if [ "$?" -ne "0" ]; then exit -1; fi

docker exec  --user root ndts service tango-db restart
docker exec  --user root ndts service tango-starter restart

if [ "$2" = "2" ]; then
    echo "install python packages"
	docker exec  --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get -qq install -y  python-tz python-pyqtgraph python-setuptools python-zmq python-scipy python-pytango'
else
    echo "install python3 packages"
    if [ "$1" = "debian10" ] || [ "$1" = "ubuntu20.04" ] || [ "$1" = "ubuntu20.10" ]|| [ "$1" = "ubuntu21.04" ] || [ "$1" = "debian11" ] ; then
	docker exec  --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get -qq install -y  python3-tz python3-pyqtgraph python3-setuptools python3-zmq python3-scipy python3-tango'
    else
	docker exec  --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get -qq install -y  python3-tz python3-pyqtgraph python3-setuptools python3-zmq python3-scipy python3-pytango'
    fi
fi
if [ "$?" -ne "0" ]; then exit -1; fi

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
if [ "$?" -ne "0" ]; then exit -1; fi
