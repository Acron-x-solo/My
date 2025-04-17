@echo off

REM Создаем keystore, если его нет
if not exist app\dobraya_set.keystore (
    keytool -genkey -v -keystore app\dobraya_set.keystore -alias dobraya_set -keyalg RSA -keysize 2048 -validity 10000 -storepass dobraya_set123 -keypass dobraya_set123 -dname "CN=Dobraya Set,O=Example,L=City,S=State,C=US"
)

REM Очищаем предыдущую сборку
call gradlew clean

REM Собираем релизную версию
call gradlew assembleRelease

REM Копируем APK в корневую директорию
copy app\build\outputs\apk\release\app-release.apk dobraya_set.apk

echo APK создан: dobraya_set.apk
pause 