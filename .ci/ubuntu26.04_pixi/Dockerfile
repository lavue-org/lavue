FROM ubuntu:26.04
RUN apt-get -qq update && export DEBIAN_FRONTEND=noninteractive && apt-get install -y  curl gpg-agent mariadb-client apt-utils debconf-utils net-tools  omniidl libomniorb4-dev libcos4-dev libzmq3-dev libterm-readline-gnu-perl software-properties-common coreutils procps  apt-transport-https gnupg2 ca-certificates wget  liblog4j1.2-java

RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
RUN curl --retry 20  -v -s http://repos.pni-hdri.de/debian_repo.pub.gpg  | gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/debian-hdri-repo.gpg --import
RUN chmod 644 /etc/apt/trusted.gpg.d/debian-hdri-repo.gpg

RUN cd /etc/apt/sources.list.d && wget https://repos.pni-hdri.de/resolute-pni-hdri.sources \
    && useradd -ms /bin/bash tango
RUN  /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "mariadb-server mysql-server/root_password password rootpw"' \
     && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "mariadb-server mysql-server/root_password_again password rootpw"' \
     && apt-get -qq update && apt-get -qq install -y mariadb-server dialog \
     &&  /bin/bash -c 'sleep 10'
RUN /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "tango-db tango-db/db/app-user string tango"'  \
     && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "tango-db tango-db/mysql/app-pass	password rootpw"' \
     && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "tango-db tango-db/mysql/admin-pass password rootpw"' \
     && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "tango-db tango-db/password-confirm password rootpw"' \
     && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "tango-db tango-db/app-password-confirm password rootpw"' \
     && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "nxsconfigserver-db nxsconfigserver-db/mysql/app-pass password rootpw"' \
     && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "nxsconfigserver-db nxsconfigserver-db/mysql/admin-pass password rootpw"' \
     && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "nxsconfigserver-db nxsconfigserver-db/app-password-confirm password rootpw"' \
     && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "nxsconfigserver-db nxsconfigserver-db/db/app-user string tango"' \
     && sed -i "s/\[mysql\]/\[mysqld\]\nsql_mode = NO_ZERO_IN_DATE,NO_ENGINE_SUBSTITUTION\ncharacter-set-collations = latin1=latin1_swedish_ci\ncharacter-set-server=latin1\n\[mysql\]/g" /etc/mysql/conf.d/mysql.cnf


ENV PKG_CONFIG_PATH=/home/tango/lib/pkgconfig

ENV MYSQL_HOST=localhost
USER tango
WORKDIR /home/tango
