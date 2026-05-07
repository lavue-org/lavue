#!/usr/bin/env bash

echo "restart mysql"
# workaround for a bug in debian9, i.e. starting mysql hangs
if [ "$1" = "debian11" ]  || [ "$1" = "debian12" ] || [ "$1" = "debian12tg10" ] || [ "$1" = "debian13" ]   || [ "$1" = "ubuntu24.04" ]  || [ "$1" = "ubuntu24.10" ] || [ "$1" = "ubuntu25.04" ] || [ "$1" = "ubuntu26.04" ] || [ "$1" = "debian11pg013" ]; then
    docker exec --user root ndts service mariadb restart
else
    docker exec --user root ndts service mysql stop
    if [ "$1" = "ubuntu20.04" ] || [ "$1" = "ubuntu20.10" ] || [ "$1" = "ubuntu21.04" ] || [ "$1" = "ubuntu21.10" ] || [ "$1" = "ubuntu22.04" ] || [ "$1" = "ubuntu22.10" ] || [ "$1" = "ubuntu23.10" ]; then
       docker exec --user root ndts /bin/bash -c 'usermod -d /var/lib/mysql/ mysql'
    fi
    docker exec --user root ndts service mysql start
    # docker exec  --user root ndts /bin/bash -c '$(service mysql start &) && sleep 30'
fi


echo "install tango-common"
docker exec  --user root ndts /bin/bash -c 'apt-get -qq update; export DEBIAN_FRONTEND=noninteractive; apt-get -qq install -y tango-common; sleep 10'
if  [ "$1" = "ubuntu24.04" ] || [ "$1" = "ubuntu24.10" ] || [ "$1" = "ubuntu25.04" ] || [ "$1" = "ubuntu26.04" ]; then
    # docker exec  --user tango ndts /bin/bash -c '/usr/lib/tango/DataBaseds 2 -ORBendPoint giop:tcp::10000  &'
    docker exec  --user root ndts /bin/bash -c 'echo -e "[client]\nuser=root\npassword=rootpw" > /root/.my.cnf'
    docker exec  --user root ndts /bin/bash -c 'echo -e "[client]\nuser=tango\nhost=localhost\npassword=rootpw" > /var/lib/tango/.my.cnf'
    docker exec  --user root ndts /usr/bin/mysql -e 'GRANT ALL PRIVILEGES ON tango.* TO "tango"@"%" identified by "rootpw"'
    docker exec  --user root ndts /usr/bin/mysql -e 'GRANT ALL PRIVILEGES ON tango.* TO "tango"@"localhost" identified by "rootpw"'
    docker exec  --user root ndts /usr/bin/mysql -e 'FLUSH PRIVILEGES'
fi
if [ "$1" = "ubuntu20.04" ] || [ "$1" = "ubuntu20.10" ] || [ "$1" = "ubuntu21.04" ] || [ "$1" = "ubuntu21.10" ] || [ "$1" = "ubuntu22.04" ]; then
    # docker exec  --user tango ndts /bin/bash -c '/usr/lib/tango/DataBaseds 2 -ORBendPoint giop:tcp::10000  &'
    docker exec  --user root ndts /bin/bash -c 'echo -e "[client]\nuser=root\npassword=rootpw" > /root/.my.cnf'
    docker exec  --user root ndts /bin/bash -c 'echo -e "[client]\nuser=tango\nhost=127.0.0.1\npassword=rootpw" > /var/lib/tango/.my.cnf'
fi
echo "install tango-db"
docker exec  --user root ndts /bin/bash -c 'apt-get -qq update; export DEBIAN_FRONTEND=noninteractive; apt-get -qq install -y tango-db; sleep 10'
if [ "$?" -ne "0" ]; then exit 255; fi
if  [ "$1" = "ubuntu24.04" ] || [ "$1" = "ubuntu24.10" ] || [ "$1" = "ubuntu25.04" ] || [ "$1" = "ubuntu26.04" ]; then
    docker exec  --user tango ndts /usr/bin/mysql -e 'create database tango'
    docker exec  --user tango ndts /bin/bash -c '/usr/bin/mysql tango < /usr/share/dbconfig-common/data/tango-db/install/mysql'
fi

docker exec  --user root ndts service tango-db restart
docker exec  --user root ndts mkdir -p /tmp/runtime-tango
docker exec  --user root ndts chown -R tango:tango /tmp/runtime-tango
docker exec  --user root ndts chmod 700 /tmp/runtime-tango


echo "install tango servers"
docker exec  --user root ndts /bin/bash -c 'apt-get -qq update; export DEBIAN_FRONTEND=noninteractive;  apt-get -qq install -y  tango-starter tango-test liblog4j1.2-java'
if [ "$?" -ne "0" ]; then exit 255; fi

docker exec --user root ndts service tango-starter restart

docker exec  --user root ndts chown -R tango:tango .


echo "start Xvfb :99 -screen 0 1024x768x24 &"
docker exec  --user root ndts /bin/bash -c 'export DISPLAY=":99.0"; Xvfb :99 -screen 0 1024x768x24 &'
if [ "$?" != "0" ]; then exit 255; fi

echo "install tango-starter tango-test and pytango"
if [ "$2" = "2" ]; then
    
    docker exec  --user root ndts /bin/bash -c 'apt-get -qq update; apt-get -qq install -y  python-pytango   tango-starter'
else
    if [ "$1" = "debian10" ] || [ "$1" = "ubuntu20.04" ] || [ "$1" = "ubuntu20.10" ] || [ "$1" = "ubuntu21.04" ] || [ "$1" = "ubuntu21.10" ] || [ "$1" = "ubuntu22.04" ]  || [ "$1" = "ubuntu22.10" ] || [ "$1" = "ubuntu23.10" ] || [ "$1" = "debian11" ] || [ "$1" = "debian12" ] || [ "$1" = "debian12tg10" ] || [ "$1" = "debian13" ] || [ "$1" = "ubuntu24.04" ] || [ "$1" = "ubuntu24.10" ] || [ "$1" = "ubuntu25.04" ] || [ "$1" = "ubuntu26.04" ] ; then
	docker exec  --user root ndts /bin/bash -c 'apt-get -qq update; apt-get -qq install -y  python3-tango tango-starter'
    elif  [ "$1" = "debian11pg013" ] ; then
	docker exec  --user root ndts /bin/bash -c 'apt-get -qq update --allow-unauthenticated --allow-insecure-repositories  ; apt-get -qq install -y   --allow-unauthenticated  python3-tango tango-starter'
    else
	docker exec  --user root ndts /bin/bash -c 'apt-get -qq update; apt-get -qq install -y  python3-pytango tango-starter'
    fi
fi
if [ "$?" != "0" ]; then exit 255; fi

docker exec  --user root ndts service tango-starter restart
if [ "$?" != "0" ]; then exit 255; fi

docker exec  --user root ndts chown -R tango:tango .

if [ "$1" = "debian11pg013" ]; then
    docker exec  --user root ndts /bin/bash -c 'apt-get -qq update  --allow-unauthenticated --allow-insecure-repositories  ; apt-get -qq install -y  --allow-unauthenticated  tango-test'
else
    docker exec  --user root ndts /bin/bash -c 'apt-get -qq update ; apt-get -qq install -y  tango-test'
fi


if [ "$2" = "2" ]; then
    echo "install python-lavue"
    docker exec ndts python setup.py build
    docker exec  --user root ndts python setup.py install
    echo "build python-lavue docs"
    docker exec ndts python setup.py  build_sphinx

else
    echo "install python3-lavue"
    docker exec ndts python3 setup.py build
    docker exec  --user root ndts python3 setup.py install
    echo "build python3-lavue docs"
    docker exec ndts sphinx-build  doc build/sphinx/html

fi
if [ "$?" != "0" ]; then exit 255; fi
