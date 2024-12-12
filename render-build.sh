#!/usr/bin/env bash
# Instalación de Chrome
echo "Instalando Google Chrome"
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get update || echo "apt-get update falló debido a permisos."
apt-get install -y ./google-chrome-stable_current_amd64.deb || echo "apt-get install falló debido a permisos."

# Instalación de ChromeDriver
echo "Instalando ChromeDriver"
CHROME_DRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
wget https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
chmod +x chromedriver
mkdir -p $HOME/bin
mv chromedriver $HOME/bin/chromedriver

# Agregar ChromeDriver al PATH
export PATH=$HOME/bin:$PATH

# Limpieza
rm google-chrome-stable_current_amd64.deb
rm chromedriver_linux64.zip

# Verificación de instalación
echo "Versión de Chrome instalada:"
$HOME/bin/google-chrome --version || echo "google-chrome no encontrado"
echo "Versión de ChromeDriver instalada:"
chromedriver --version || echo "chromedriver no encontrado"