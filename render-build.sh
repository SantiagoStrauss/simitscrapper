#!/usr/bin/env bash

# Create Chrome directory
mkdir -p /opt/render/project/chrome-linux

# Download and install Chrome
echo "Installing Google Chrome"
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg-deb -x google-chrome-stable_current_amd64.deb /opt/render/project/chrome-linux

# Get Chrome version and matching ChromeDriver
CHROME_VERSION=$(/opt/render/project/chrome-linux/opt/google/chrome/chrome --version | cut -d " " -f3)
CHROME_MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d "." -f1)
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR_VERSION}")

# Install ChromeDriver
echo "Installing ChromeDriver ${CHROMEDRIVER_VERSION}"
wget "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
unzip chromedriver_linux64.zip
chmod +x chromedriver
mkdir -p $HOME/bin
mv chromedriver $HOME/bin/chromedriver

# Add ChromeDriver to PATH
export PATH=$HOME/bin:$PATH

# Cleanup
rm google-chrome-stable_current_amd64.deb chromedriver_linux64.zip

# Verify installation
echo "Chrome version:"
/opt/render/project/chrome-linux/opt/google/chrome/chrome --version
echo "ChromeDriver version:"
chromedriver --version