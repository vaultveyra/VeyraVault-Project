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

    compile_sdk = "34"
    min_sdk = "21"
    java_ver = "VERSION_1_8"

    for gpath in [orig_app_gradle, bcore_gradle]:
        if os.path.exists(gpath):
            with open(gpath, "r", encoding="utf-8", errors="ignore") as f:
                txt = f.read()
            m_comp = re.search(r'compileSdk(?:Version)?\s*[=:]?\s*(\d+)', txt)
            if m_comp:
                compile_sdk = m_comp.group(1)
            m_min = re.search(r'minSdk(?:Version)?\s*[=:]?\s*(\d+)', txt)
            if m_min:
                min_sdk = m_min.group(1)
            m_java = re.search(r'JavaVersion\.(VERSION_[0-9_]+)', txt)
            if m_java:
                java_ver = m_java.group(1)

    print(f"[+] Detected Engine Config -> compileSdk: {compile_sdk}, minSdk: {min_sdk}, Java: {java_ver}")

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

    # Configure settings.gradle with pluginManagement & dependencyResolutionManagement for Gradle 8+
    settings_gradle = os.path.join(WORKSPACE, "settings.gradle")
    existing_includes = "include ':app', ':Bcore'"
    if os.path.exists(settings_gradle):
        with open(settings_gradle, "r", encoding="utf-8", errors="ignore") as f:
            stxt = f.read()
        inc_lines = [line.strip() for line in stxt.splitlines() if line.strip().startswith("include")]
        if inc_lines:
            existing_includes = "\n".join(inc_lines)

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
{existing_includes}
"""
    with open(settings_gradle, "w", encoding="utf-8") as f:
        f.write(new_settings)

    # Configure gradle.properties for JDK 17 + AGP 8+ compatibility
    gradle_props = os.path.join(WORKSPACE, "gradle.properties")
    props_content = """org.gradle.jvmargs=-Xmx4096m -Dfile.encoding=UTF-8 --add-opens=jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.code=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.comp=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.file=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.jvm=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.main=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.model=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.parser=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.processing=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.tree=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.util=ALL-UNNAMED
android.useAndroidX=true
android.enableJetifier=true
android.nonTransitiveRClass=false
android.defaults.buildfeatures.buildconfig=true
"""
    with open(gradle_props, "w", encoding="utf-8") as f:
        f.write(props_content)

    print("[+] Workspace prepared and aligned successfully for Gradle 8 / AGP 8!")

if __name__ == "__main__":
    main()
