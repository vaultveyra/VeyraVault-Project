#!/usr/bin/env python3
import os, re, shutil, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE = os.path.join(ROOT, "build_workspace")
BUNDLED_ENGINE = os.path.join(ROOT, "engine_source")

def run(cmd, cwd=None):
    print(f"[+] Executing: {cmd}")
    subprocess.check_call(cmd, shell=True, cwd=cwd)

def main():
    if os.path.exists(WORKSPACE):
        shutil.rmtree(WORKSPACE)

    if os.path.exists(os.path.join(BUNDLED_ENGINE, "Bcore")):
        print("[+] Found locally bundled Bcore C++/Java engine! Copying to build_workspace...")
        shutil.copytree(BUNDLED_ENGINE, WORKSPACE)
    else:
        print("[*] Cloning upstream BlackBox engine into build_workspace...")
        run(f'git clone --depth 1 https://github.com/ALEX5402/NewBlackbox.git "{WORKSPACE}"')

    bcore_gradle = os.path.join(WORKSPACE, "Bcore", "build.gradle")
    orig_app_gradle = os.path.join(WORKSPACE, "app", "build.gradle")
    root_gradle = os.path.join(WORKSPACE, "build.gradle")
    toml_path = os.path.join(WORKSPACE, "gradle", "libs.versions.toml")

    compile_sdk = "34"
    min_sdk = "21"
    java_ver = "VERSION_1_8"

    for gpath in [orig_app_gradle, bcore_gradle, root_gradle, toml_path]:
        if os.path.exists(gpath):
            with open(gpath, "r", encoding="utf-8", errors="ignore") as f:
                txt = f.read()
            m_comp = re.search(r'compileSdk(?:Version)?\s*[=:]?\s*["\']?(\d+)["\']?', txt)
            if m_comp:
                compile_sdk = m_comp.group(1)
            m_min = re.search(r'minSdk(?:Version)?\s*[=:]?\s*["\']?(\d+)["\']?', txt)
            if m_min:
                min_sdk = m_min.group(1)
            m_java = re.search(r'JavaVersion\.(VERSION_[0-9_]+)', txt)
            if m_java:
                java_ver = m_java.group(1)

    print(f"[+] Detected Engine Config -> compileSdk: {compile_sdk}, minSdk: {min_sdk}, Java: {java_ver}")

    # Prevent any Manifest Merger attribute conflicts in Bcore's AndroidManifest.xml
    bcore_manifest = os.path.join(WORKSPACE, "Bcore", "src", "main", "AndroidManifest.xml")
    if os.path.exists(bcore_manifest):
        with open(bcore_manifest, "r", encoding="utf-8", errors="ignore") as f:
            bm = f.read()
        for attr in ["android:label", "android:icon", "android:roundIcon", "android:allowBackup", "android:supportsRtl", "android:theme"]:
            bm = re.sub(rf'\s+{attr}="[^"]*"', '', bm)
        with open(bcore_manifest, "w", encoding="utf-8") as f:
            f.write(bm)

    # Replace sample app with VeyraVault app module
    ws_app = os.path.join(WORKSPACE, "app")
    if os.path.exists(ws_app):
        shutil.rmtree(ws_app)
    shutil.copytree(os.path.join(ROOT, "app"), ws_app)

    # Remove deprecated package attribute from AndroidManifest.xml for AGP 8+ compatibility
    manifest_path = os.path.join(ws_app, "src", "main", "AndroidManifest.xml")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            m_txt = f.read()
        m_txt = re.sub(r'\s+package="com\.veyravault\.space"', '', m_txt)
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(m_txt)

    # Write AGP 8+ and Gradle 8+ compatible app/build.gradle
    app_gradle_content = f"""plugins {{
    id 'com.android.application'
}}

android {{
    namespace "com.veyravault.space"
    compileSdk {compile_sdk}

    defaultConfig {{
        applicationId "com.veyravault.space"
        minSdk {min_sdk}
        targetSdk 28
        versionCode 200
        versionName "2.0.0-Enterprise"

        ndk {{
            abiFilters "armeabi-v7a", "arm64-v8a"
        }}
    }}

    signingConfigs {{
        release {{
            storeFile file("release.keystore")
            storePassword "VeyraVaultPass2025"
            keyAlias "veyravault_key"
            keyPassword "VeyraVaultPass2025"
            v1SigningEnabled true
            v2SigningEnabled true
        }}
    }}

    buildTypes {{
        release {{
            minifyEnabled false
            shrinkResources false
            signingConfig signingConfigs.release
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }}
        debug {{
            signingConfig signingConfigs.release
        }}
    }}

    compileOptions {{
        sourceCompatibility JavaVersion.{java_ver}
        targetCompatibility JavaVersion.{java_ver}
    }}

    buildFeatures {{
        buildConfig true
    }}

    lint {{
        checkReleaseBuilds false
        abortOnError false
    }}

    packagingOptions {{
        pickFirst 'lib/armeabi-v7a/*.so'
        pickFirst 'lib/arm64-v8a/*.so'
        exclude 'META-INF/DEPENDENCIES'
        exclude 'META-INF/LICENSE'
        exclude 'META-INF/NOTICE'
    }}
}}

dependencies {{
    implementation project(':Bcore')
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.9.0'
    implementation 'androidx.recyclerview:recyclerview:1.3.1'
    implementation 'androidx.cardview:cardview:1.0.0'
    implementation 'org.osmdroid:osmdroid-android:6.1.14'
}}
"""
    with open(os.path.join(ws_app, "build.gradle"), "w", encoding="utf-8") as f:
        f.write(app_gradle_content)

    # Extract only valid module includes (e.g., ':app', ':Bcore') ignoring includeGroupByRegex
    settings_gradle = os.path.join(WORKSPACE, "settings.gradle")
    modules = ["':app'", "':Bcore'"]
    if os.path.exists(settings_gradle):
        with open(settings_gradle, "r", encoding="utf-8", errors="ignore") as f:
            stxt = f.read()
        found_mods = re.findall(r"['\"](:[a-zA-Z0-9_\-:]+)['\"]", stxt)
        for m in found_mods:
            q = f"'{m}'"
            if q not in modules:
                modules.append(q)

    inc_block = "\n".join([f"include {m}" for m in modules])

    new_settings = f"""pluginManagement {{
    repositories {{
        google()
        mavenCentral()
        gradlePluginPortal()
        maven {{ url 'https://jitpack.io' }}
    }}
}}
dependencyResolutionManagement {{
    repositoriesMode.set(RepositoriesMode.PREFER_SETTINGS)
    repositories {{
        google()
        mavenCentral()
        maven {{ url 'https://jitpack.io' }}
    }}
}}
rootProject.name = "VeyraVault"
{inc_block}
"""
    with open(settings_gradle, "w", encoding="utf-8") as f:
        f.write(new_settings)

    # Preserve existing gradle.properties and append required flags
    gradle_props = os.path.join(WORKSPACE, "gradle.properties")
    existing_props = ""
    if os.path.exists(gradle_props):
        with open(gradle_props, "r", encoding="utf-8", errors="ignore") as f:
            existing_props = f.read()

    extra_props = """
org.gradle.jvmargs=-Xmx4096m -Dfile.encoding=UTF-8
android.useAndroidX=true
android.enableJetifier=true
android.nonTransitiveRClass=false
android.defaults.buildfeatures.buildconfig=true
"""
    with open(gradle_props, "w", encoding="utf-8") as f:
        f.write(existing_props + "\n" + extra_props)

    print(f"[+] Workspace prepared! Modules included: {modules}")

if __name__ == "__main__":
    main()
