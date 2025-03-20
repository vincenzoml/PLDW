FROM ubuntu:24.10

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install Python, LaTeX, Pandoc and other tools
RUN apt-get update && apt-get install -y \
    python3.13 \
    python3.13-venv \
    python3-pip \
    git \
    curl \
    pandoc \
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-latex-extra \
    fonts-dejavu 

# Install any additional dependencies
RUN apt-get update && apt-get install -y \
    # ... your dependencies here ...

    # Set up the user
    ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# ... any other configuration ...

# Set the default user
USER $USERNAME
