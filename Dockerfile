FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

# Pre-install
RUN apt-get update && apt-get -y install python3.6 git curl

# git lfs
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash

# kernel-build dependencies
RUN apt-get install -y \
    build-essential \
    kernel-package \
    fakeroot \
    libncurses5-dev \
    libssl-dev \
    ccache \
    libelf-dev \
    bsdmainutils \
    bison \
    flex \
    dh-systemd \
    kernel-wedge \
    makedumpfile \
    libnewt-dev \
    libiberty-dev \
    rsync \
    libdw-dev \
    libpci-dev \
    pkg-config \
    libunwind8-dev \
    liblzma-dev \
    libaudit-dev \
    python-dev \
    gawk \
    libudev-dev \
    autoconf \
    automake \
    libtool \
    uuid-dev \
    binutils-dev \
    transfig \
    sharutils \
    asciidoc \
    debhelper \
    docbook-utils \
    git-lfs

