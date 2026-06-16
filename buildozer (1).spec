# (str) Title of your application
title = Gestion de Patrimoine

# (str) Package name
package.name = gestionpatrimoine

# (str) Package domain (needed for android packaging)
package.domain = org.robert

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,jpeg,kv,csv

# (list) List of inclusions using pattern matching
source.include_patterns = image/*, patrimoine.csv

# (str) Application versioning (method 1)
version = 1.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,pandas,openpyxl,plyer

# (str) Supported orientations
orientation = portrait

# =============================================================================
# Android specific
# =============================================================================

# (list) Permissions
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (bool) If True, then skip applying AndroidX backward compatibility patches.
android.enable_androidx = true

# (str) Format used to package the app for the Google Play Store (aab) or old APK (apk)
android.archs = arm64-v8a, armeabi-v7a

# (bool) copy library instead of making a symbolic link
p4a.hook =
