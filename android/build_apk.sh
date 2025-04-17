#!/bin/bash

# Создаем keystore, если его нет
if [ ! -f app/dobraya_set.keystore ]; then
    keytool -genkey -v -keystore app/dobraya_set.keystore -alias dobraya_set -keyalg RSA -keysize 2048 -validity 10000 -storepass dobraya_set123 -keypass dobraya_set123 -dname "CN=Dobraya Set,O=Example,L=City,S=State,C=US"
fi

# Очищаем предыдущую сборку
./gradlew clean

# Собираем релизную версию
./gradlew assembleRelease

# Копируем APK в корневую директорию
cp app/build/outputs/apk/release/app-release.apk dobraya_set.apk

echo "APK создан: dobraya_set.apk" 