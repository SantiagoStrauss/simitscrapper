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
CHROME_VERSION=$(${HOME}/chrome/usr/bin/google-chrome --version | cut -d ' ' -f 3 | cut -d '.' -f 1)
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
wget -q "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
unzip -q chromedriver_linux64.zip -d ${HOME}/chromedriver
rm chromedriver_linux64.zip

# Make executables available in PATH
export PATH="${HOME}/chrome/usr/bin:${HOME}/chromedriver:${PATH}"
echo "export PATH=${HOME}/chrome/usr/bin:${HOME}/chromedriver:${PATH}" >> ~/.bashrc

# Verify installations
echo "Chrome version:"
google-chrome --version || echo "Chrome verification failed"
echo "ChromeDriver version:"
chromedriver --version || echo "ChromeDriver verification failed"

# Update Python script with new Chrome binary location
sed -i "s|options.binary_location = \"/usr/bin/google-chrome\"|options.binary_location = \"${HOME}/chrome/opt/google/chrome/google-chrome\"|" cemail.py