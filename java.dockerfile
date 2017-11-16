FROM starcraft:bwapi

USER root

# Install Java.
RUN sudo dpkg --add-architecture i386 \
    && sudo apt update \
    && sudo apt install -y openjdk-8-jre-headless:i386 \
    && rm -rf /var/lib/apt/lists/*

# Define commonly used JAVA_HOME variable
ENV JAVA_HOME /usr/lib/jvm/java-1.8.0-openjdk-i386


USER starcraft
