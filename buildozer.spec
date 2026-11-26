[app]
title = lataM
package.name = latam
package.domain = org.latino
source.dir = .
source.include_exts = py,png,jpg,wav,ogg,mp3,ttf,lat,json,txt,lataM,latam
source.exclude_dirs = juego,bin,.buildozer,.github
version = 1.0
requirements = python3,pygame
p4a.branch = release-2024.01.21
orientation = landscape
fullscreen = 1
android.archs = arm64-v8a
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

[buildozer]
log_level = 2
