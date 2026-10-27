#!/usr/bin/env bash

echo "restart mysql"
docker exec --user root ndts service mariadb restart

echo "install tango-db "
docker exec  --user root ndts /bin/bash -c 'apt-get -qq update; export DEBIAN_FRONTEND=noninteractive; apt-get -qq install -y tango-common; sleep 10'


docker exec  --user root ndts chown -R tango:tango .

docker exec  --user root ndts /bin/bash -c 'echo -e "[client]\nuser=root\npassword=rootpw" > /root/.my.cnf'
docker exec  --user root ndts /bin/bash -c 'echo -e "[client]\nuser=tango\nhost=localhost\npassword=rootpw" > /var/lib/tango/.my.cnf'
docker exec  --user root ndts /usr/bin/mysql -e 'GRANT ALL PRIVILEGES ON tango.* TO "tango"@"%" identified by "rootpw"'
docker exec  --user root ndts /usr/bin/mysql -e 'GRANT ALL PRIVILEGES ON tango.* TO "tango"@"localhost" identified by "rootpw"'
docker exec  --user root ndts /usr/bin/mysql -e 'FLUSH PRIVILEGES'

docker exec  --user root ndts /bin/bash -c 'apt-get -qq update; export DEBIAN_FRONTEND=noninteractive; apt-get -qq install -y tango-db; sleep 10'

if [ "$1" = "ubuntu26.04" ]; then
    docker exec  --user tango ndts /usr/bin/mysql -e 'create database tango'
    docker exec  --user tango ndts /bin/bash -c '/usr/bin/mysql tango < /usr/share/dbconfig-common/data/tango-db/install/mysql'
fi

docker exec  --user root ndts service tango-db restart

echo "install tango-starter"
docker exec  --user root ndts /bin/bash -c 'apt-get -qq update; export DEBIAN_FRONTEND=noninteractive;  apt-get -qq install -y  tango-starter tango-test liblog4j1.2-java'
if [ "$?" -ne "0" ]; then exit 255; fi

docker exec --user root ndts service tango-starter restart

docker exec --user root ndts chown -R tango:tango .
