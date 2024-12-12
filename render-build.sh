#!/usr/bin/env bash
# Instalación de Chrome
echo "Instalando Google Chrome"
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg-deb -x google-chrome-stable_current_amd64.deb $HOME/google-chrome
export PATH=$HOME/google-chrome/opt/google/chrome:$PATH

# Instalación de ChromeDriver
echo "Instalando ChromeDriver"
CHROME_DRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
wget https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
chmod +x chromedriver
mkdir -p $HOME/bin
mv chromedriver $HOME/bin/chromedriver || echo "No se pudo mover chromedriver a $HOME/bin"

# Agregar ChromeDriver al PATH
export PATH=$HOME/bin:$PATH

# Limpieza
rm google-chrome-stable_current_amd64.deb
rm chromedriver_linux64.zip

# Verificación de instalación
echo "Versión de Chrome instalada:"
$HOME/google-chrome/opt/google/chrome/google-chrome --version || echo "google-chrome no encontrado"
echo "Versión de ChromeDriver instalada:"
$HOME/bin/chromedriver --version || echo "chromedriver no encontrado"