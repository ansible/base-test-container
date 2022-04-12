FROM quay.io/bedrock/ubuntu:focal-20220404

# increment the number in this file to force a full container rebuild
COPY files/update.txt /dev/null

VOLUME /sys/fs/cgroup /run/lock /run /tmp

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    g++ \
    gcc \
    git \
    gnupg2 \
    libbz2-dev \
    libffi-dev \
    libreadline-dev \
    libsqlite3-dev \
    libxml2-dev \
    libxslt1-dev \
    libyaml-dev \
    locales \
    make \
    openssh-client \
    openssh-server \
    openssl \
    python2.7-dev \
    python3.8-dev \
    python3.8-distutils \
    python3.8-venv \
    python3.9-dev \
    python3.9-distutils \
    python3.9-venv \
    shellcheck \
    systemd-sysv \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# podman build fails with 'apt-key adv ...' but this works for both
RUN curl -sL "http://keyserver.ubuntu.com/pks/lookup?op=get&search=0xF23C5A6CF475977595C89F51BA6932366A755776" | apt-key add

COPY files/deadsnakes.list /etc/apt/sources.list.d/deadsnakes.list

# Install Python versions available from the deadsnakes PPA.
# This is done separately to avoid conflicts with official Ubuntu packages.
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3.5-dev \
    python3.5-venv \
    python3.6-dev \
    python3.6-venv \
    python3.7-dev \
    python3.7-distutils \
    python3.7-venv \
    python3.10-dev \
    python3.10-distutils \
    python3.10-venv \
    && \
    apt-get clean

RUN rm /etc/apt/apt.conf.d/docker-clean && \
    ln -s python2.7 /usr/bin/python2 && \
    ln -s python3   /usr/bin/python && \
    locale-gen en_US.UTF-8

# Install pwsh, and other PS/.NET sanity test tools.
RUN apt-get update -y && \
    curl --silent --location https://github.com/PowerShell/PowerShell/releases/download/v7.2.0/powershell_7.2.0-1.deb_amd64.deb -o /tmp/pwsh.deb && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends /tmp/pwsh.deb && \
    rm /tmp/pwsh.deb && \
    apt-get clean && \
    pwsh --version

ENV container=docker
CMD ["/sbin/init"]

# Install pip last to speed up local container rebuilds.
COPY files/*.py /usr/share/container-setup/
RUN python3.10 /usr/share/container-setup/setup.py && rm /usr/share/container-setup/setup.py

# Make sure the pip entry points in /usr/bin are correct.
RUN rm -f /usr/bin/pip2 && cp -av /usr/local/bin/pip2 /usr/bin/pip2 && /usr/bin/pip2 -V && \
    rm -f /usr/bin/pip3 && cp -av /usr/local/bin/pip3 /usr/bin/pip3 && /usr/bin/pip3 -V && \
    rm -f /usr/bin/pip  && cp -av /usr/local/bin/pip  /usr/bin/pip  && /usr/bin/pip  -V
