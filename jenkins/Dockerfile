FROM jenkins/jenkins:lts

USER root

# Install Docker CLI
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    wget \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Install Docker Compose v2
RUN curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose \
    && ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Install Trivy (binary installation compatible with amd64/arm64)
RUN set -eux; \
    ARCH="$(uname -m)"; \
    if [ "$ARCH" = "x86_64" ]; then TRIVY_ASSET="Linux-64bit"; \
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then TRIVY_ASSET="Linux-ARM64"; \
    else echo "Unsupported architecture: $ARCH"; exit 1; fi; \
    TRIVY_URL="$(curl -fsSL https://api.github.com/repos/aquasecurity/trivy/releases/latest | grep 'browser_download_url' | grep "trivy_.*_${TRIVY_ASSET}\\.tar\\.gz\"" | head -n 1 | cut -d '"' -f 4)"; \
    test -n "$TRIVY_URL"; \
    curl -fsSL "$TRIVY_URL" -o /tmp/trivy.tar.gz; \
    tar -xzf /tmp/trivy.tar.gz -C /usr/local/bin trivy; \
    chmod +x /usr/local/bin/trivy; \
    rm /tmp/trivy.tar.gz

# Verify installations
RUN docker --version && docker-compose --version && trivy --version

# Switch back to jenkins user
USER jenkins
