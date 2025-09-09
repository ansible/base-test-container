FROM public.ecr.aws/docker/library/ubuntu:noble-20250805

# Prevent automatic apt cache cleanup, as caching is desired when running integration tests.
# Instead, when installing packages during container builds, explicit cache cleanup is required.
RUN rm /etc/apt/apt.conf.d/docker-clean

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
    python-is-python3 \
    python3.12-dev \
    python3.12-venv \
    shellcheck \
    sshpass \
    sudo \
    systemd-sysv \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Perform locale generation now that the locales package is installed.
RUN locale-gen en_US.UTF-8

# Enable the deadsnakes PPA to provide additional packages.
COPY files/deadsnakes.gpg /etc/apt/keyrings/deadsnakes.gpg
COPY files/deadsnakes.list /etc/apt/sources.list.d/deadsnakes.list

# Install Python versions available from the deadsnakes PPA.
# This is done separately to avoid conflicts with official Ubuntu packages.
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3.9-dev \
    python3.9-venv \
    python3.10-dev \
    python3.10-venv \
    python3.11-dev \
    python3.11-venv \
    python3.13-dev \
    python3.13-venv \
    python3.14-dev \
    python3.14-venv \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install PowerShell.
COPY files/powershell.sh /usr/share/container-setup/
RUN /usr/share/container-setup/powershell.sh 7.5.3

CMD ["/sbin/init"]

# Install pip last to speed up local container rebuilds.
COPY files/*.py /usr/share/container-setup/
RUN ln -s /usr/bin/python3.13 /usr/share/container-setup/python
RUN /usr/share/container-setup/python -B /usr/share/container-setup/setup.py
