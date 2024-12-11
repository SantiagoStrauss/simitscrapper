#!/usr/bin/env bash
# Exit on error
set -e

# Create necessary directories in writable location
mkdir -p ${HOME}/chrome
mkdir -p ${HOME}/chromedriver

# Install Chrome
echo "Installing Google Chrome..."
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -x google-chrome-stable_current_amd64.deb ${HOME}/chrome
rm google-chrome-stable_current_amd64.deb

# Install ChromeDriver
echo "Installing ChromeDriver..."
CHROME_BINARY="${HOME}/chrome/opt/google/chrome/google-chrome"
CHROME_VERSION=$(${CHROME_BINARY} --version | cut -d ' ' -f 3 | cut -d '.' -f 1)
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
wget -q "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
unzip -q chromedriver_linux64.zip -d ${HOME}/chromedriver
rm chromedriver_linux64.zip

# Make executables available in PATH
export PATH="${HOME}/chrome/opt/google/chrome:${HOME}/chromedriver:${PATH}"
echo "export PATH=${HOME}/chrome/opt/google/chrome:${HOME}/chromedriver:${PATH}" >> ~/.bashrc

# Verify installations
echo "Chrome version:"
${CHROME_BINARY} --version || echo "Chrome verification failed"
echo "ChromeDriver version:"
chromedriver --version || echo "ChromeDriver verification failed"

# Update Python script with new Chrome binary location
sed -i "s|options.binary_location = \".*\"|options.binary_location = \"${CHROME_BINARY}\"|" cemail.py