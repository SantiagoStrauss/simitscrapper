#!/usr/bin/env bash
# Instalación de Chrome
echo "Instalando Google Chrome"
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get update
apt-get install -y ./google-chrome-stable_current_amd64.deb

# Instalación de ChromeDriver
echo "Instalando ChromeDriver"
CHROME_DRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
wget https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
chmod +x chromedriver
mv chromedriver /usr/local/bin/

# Limpieza
rm google-chrome-stable_current_amd64.deb
rm chromedriver_linux64.zip

# Verificación de instalación
echo "Versión de Chrome instalada:"
google-chrome --version
echo "Versión de ChromeDriver instalada:"
chromedriver --version