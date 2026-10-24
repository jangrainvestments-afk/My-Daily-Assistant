[app]
title = My Daily Assistant
package.name = mydailyassistant
package.domain = org.test
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,atlas,db
source.exclude_dirs = .git,.venv,.venv-kivy,venv,.buildozer,__pycache__
version = 0.1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0

android.api = 35
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.numeric_version = 10242
android.add_src = src/android
android.extra_manifest_xml = ./src/android/extra_manifest.xml
android.extra_manifest_application_xml = ./src/android/extra_manifest_application.xml

# Keep p4a on develop; it supports --extra-manifest-application-xml.
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1
