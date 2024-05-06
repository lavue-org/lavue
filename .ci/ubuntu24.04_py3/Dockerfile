FROM ubuntu:24.04

MAINTAINER DESY, Jan Kotanski <jankotan@gmail.com>

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -qq update && export DEBIAN_FRONTEND=noninteractive && apt-get install -y  curl gpg-agent mariadb-client python3-h5py python3-sphinx apt-utils debconf-utils net-tools  omniidl libomniorb4-dev libcos4-dev libzmq3-dev python3-setuptools python3-setuptools libterm-readline-gnu-perl software-properties-common coreutils procps  apt-transport-https gnupg2 ca-certificates wget python3-h5py python3-sphinx apt-utils debconf-utils net-tools  omniidl libomniorb4-dev libcos4-dev libzmq3-dev python3-setuptools python3-lxml  liblog4j1.2-java python3-setuptools python3-pytest

RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
RUN curl -s http://repos.pni-hdri.de/debian_repo.pub.gpg  | gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/debian-hdri-repo.gpg --import
RUN chmod 644 /etc/apt/trusted.gpg.d/debian-hdri-repo.gpg

RUN cd /etc/apt/sources.list.d && wget http://repos.pni-hdri.de/noble-pni-hdri.list \
    && useradd -ms /bin/bash tango

# switch to the german archive mirror
# RUN sed -i 's|http://archive|http://de.archive|g' /etc/apt/sources.list

# install packages
RUN apt-get -qq update && export DEBIAN_FRONTEND=noninteractive && apt-get -qq dist-upgrade
RUN apt-get -qq update && export DEBIAN_FRONTEND=noninteractive && apt-get install -y mariadb-client python3-h5py python3-sphinx apt-utils debconf-utils net-tools  omniidl python3-pninexus python3-pyqt5 python3-pyqt5.qtsvg python3-qtchecker  python3-pyfai qt5-qmake  qtchooser python3-requests xvfb  libxcb1 libx11-xcb1 libxcb-keysyms1 libxcb-image0 libxcb-icccm4 libxcb-render-util0 xkb-data liblog4j1.2-java python3-pyqt5  git python3-tz python3-pyqtgraph python3-setuptools python3-zmq python3-scipy python3-pyqt5.qtwebkit hdf5-filter-plugin

# set db configuration
RUN  /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "mariadb-server mysql-server/root_password password rootpw"' \
     && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "mariadb-server mysql-server/root_password_again password rootpw"' \
     && apt-get -qq update && apt-get -qq install -y mariadb-server python3-mysqldb  dialog \
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
     && sed -i "s/\[mysql\]/\[mysqld\]\nsql_mode = NO_ZERO_IN_DATE,NO_ENGINE_SUBSTITUTION\ncharacter_set_server=latin1\ncollation_server=latin1_swedish_ci\n\[mysql\]/g" /etc/mysql/conf.d/mysql.cnf

ENV PKG_CONFIG_PATH=/home/tango/lib/pkgconfig
ENV HDF5_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/hdf5/plugins
ENV XDG_RUNTIME_DIR=/tmp/runtime-tango
ENV MYSQL_HOST=localhost
USER tango
WORKDIR /home/tango

