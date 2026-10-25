[app]

# (str) Title of your application
title = AutoGameLoader

# (str) Package name
package.name = autogameloader

# (str) Package domain (needed for android packaging)
package.domain = org.autogen

# (str) Source file where the main entry point is located
source.dir = .

# (list) Source files to include (let it local)
source.include_exts = py,png,jpg,kv

# (str) Application version
version = 1.0

# (list) Application requirements
requirements = python3,kivy,requests,opencv-python,numpy

# (str) Supported orientations
orientation = portrait

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (bool) Automatically accept Android SDK license
android.accept_sdk_license = True
