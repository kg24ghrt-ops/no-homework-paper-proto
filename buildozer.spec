[app]
title = No Homework Notebook
package.name = nohomework
package.domain = org.kg24ghrt
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1.0

requirements = python3==3.14.2,kivy==2.3.1,pillow

orientation = portrait
fullscreen = 0

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 36
android.minapi = 21
android.ndk = 29
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1

[p4a]
branch = v2026.05.09
