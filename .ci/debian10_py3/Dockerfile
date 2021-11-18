FROM debian:buster

MAINTAINER DESY, Jan Kotanski <jankotan@gmail.com>

ENV DEBIAN_FRONTEND=noninteractive

# add the HDRI repository
RUN /bin/bash -c 'echo "deb http://ftp.de.debian.org/debian buster main" > /etc/apt/sources.list.d/debian_de.list'
RUN apt-get -qq update && apt-get -qq install apt-utils dialog -y
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
RUN apt-get -qq update && apt-get -qq install -y libterm-readline-gnu-perl software-properties-common coreutils gnupg2 procps curl apt-transport-https gnupg2 ca-certificates wget
RUN curl -s http://repos.pni-hdri.de/debian_repo.pub.gpg  | gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/debian-hdri-repo.gpg --import
RUN chmod 644 /etc/apt/trusted.gpg.d/debian-hdri-repo.gpg
RUN add-apt-repository "deb http://repos.pni-hdri.de/apt/debian buster main" -y

# install packages
RUN apt-get update  && apt-get  -y dist-upgrade
RUN apt-get -qq update && apt-get -qq install -y default-mysql-client  python3-h5py  python3-mysqldb python3-sphinx  apt-utils debconf-utils net-tools  omniidl libomniorb4-dev libcos4-dev libomnithread4-dev libzmq3-dev python3-pyqt5 python3-pyqt5.qtsvg python3-qtchecker python3-pyfai qt4-qtconfig libqt4-dev-bin python3-requests hdf5-plugin-bshuf hdf5-plugin-bz2 hdf5-plugin-lz4 python3-pninexus  xvfb  libxcb1 libx11-xcb1 libxcb-keysyms1 libxcb-image0 libxcb-icccm4 libxcb-render-util0 xkb-data liblog4j1.2-java pyqt5-dev-tools git python3-tz python3-pyqtgraph python3-setuptools python3-zmq python3-scipy

# set db configuration
RUN useradd -ms /bin/bash tango
RUN  /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "mysql-server mysql-server/root_password password rootpw"' \
     && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "mysql-server mysql-server/root_password_again password rootpw"' \
     && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "mariadb-server mysql-server/root_password password rootpw"' \
     && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "mariadb-server mysql-server/root_password_again password rootpw"' \
     && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-get-selections |grep mysql '

RUN apt-get -qq install -y default-mysql-server adduser && /bin/bash -c 'sleep 10'

RUN /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "tango-db tango-db/db/app-user string tango"' \
    && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "tango-db tango-db/mysql/app-pass password rootpw"' \
    && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "tango-db tango-db/mysql/admin-pass password rootpw"' \
    && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "tango-db tango-db/password-confirm password rootpw"' \
    && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "tango-db tango-db/app-password-confirm password rootpw"' \
    && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "nxsconfigserver-db nxsconfigserver-db/mysql/app-pass password rootpw"' \
    && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "nxsconfigserver-db nxsconfigserver-db/mysql/admin-pass password rootpw"' \
    && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "nxsconfigserver-db nxsconfigserver-db/app-password-confirm password rootpw"' \
    && /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; debconf-set-selections <<< "nxsconfigserver-db nxsconfigserver-db/db/app-user string tango"'

ENV PKG_CONFIG_PATH=/home/tango/lib/pkgconfig
ENV HDF5_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/hdf5/plugins
USER tango
WORKDIR /home/tango
