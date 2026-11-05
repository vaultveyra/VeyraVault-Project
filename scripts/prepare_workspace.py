#!/usr/bin/env python3
import os, re, sys, glob, shutil, stat, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE = os.path.join(ROOT, "build_workspace")
BUNDLED_ENGINE = os.path.join(ROOT, "engine_source")
OUTPUT_DIR = os.path.join(ROOT, "output_artifacts")

def run(cmd, cwd=None, check=True):
    print(f"[+] Executing: {cmd}")
    subprocess.run(cmd, shell=True, cwd=cwd, check=check)

def accept_android_sdk_licenses():
    print("[*] Accepting all Android SDK & NDK licenses...")
    sdk_dirs = [
        os.environ.get("ANDROID_HOME"),
        os.environ.get("ANDROID_SDK_ROOT"),
        "/usr/local/lib/android/sdk"
    ]
    for sdk in sdk_dirs:
        if sdk and os.path.exists(sdk):
            lic_dir = os.path.join(sdk, "licenses")
            os.makedirs(lic_dir, exist_ok=True)
            hashes = [
                "8933bad161af4178b1185d1a37fbf41ea5269c55",
                "d56f5187479451eabf01fb78af6dfcb131a6481e",
                "24333f8a63b6825ea9c5514f83c2829b004d1fee",
                "859f317696f67ef3d7f30a50a5560e7834b43903"
            ]
            with open(os.path.join(lic_dir, "android-sdk-license"), "w", encoding="utf-8") as f:
                f.write("\n" + "\n".join(hashes) + "\n")
            preview_hashes = [
                "84831b9409646a918e30573bab4c9c91346d8abd",
                "504667f4c0de7af1a06de9f4b1727b84351f2910"
            ]
            with open(os.path.join(lic_dir, "android-sdk-preview-license"), "w", encoding="utf-8") as f:
                f.write("\n" + "\n".join(preview_hashes) + "\n")

            sdkmgr = os.path.join(sdk, "cmdline-tools", "latest", "bin", "sdkmanager")
            if os.path.exists(sdkmgr):
                run(f"yes | {sdkmgr} --licenses", check=False)

def post_build():
    print("[*] Collecting Signed APK and running Stage-2 Binary Audit...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    apks = glob.glob(os.path.join(WORKSPACE, "app", "build", "outputs", "apk", "release", "*.apk"))
    if not apks:
        print("[-] ERROR: No release APK found!")
        sys.exit(1)
    apk_out = os.path.join(OUTPUT_DIR, "VeyraVault-release.apk")
    shutil.copy2(apks[0], apk_out)

    ks_path = os.path.join(WORKSPACE, "app", "release.keystore")
    if os.path.exists(ks_path):
        shutil.copy2(ks_path, os.path.join(OUTPUT_DIR, "release.keystore"))

    src_rep = os.path.join(ROOT, "source_audit_report.txt")
    if os.path.exists(src_rep):
        shutil.copy2(src_rep, os.path.join(OUTPUT_DIR, "source_audit_report.txt"))

    run(f'python3 "{os.path.join(ROOT, "scripts", "audit_apk.py")}" "{apk_out}"')
    apk_rep = os.path.join(ROOT, "apk_audit_report.txt")
    if os.path.exists(apk_rep):
        shutil.copy2(apk_rep, os.path.join(OUTPUT_DIR, "apk_audit_report.txt"))
    print("[+] All release artifacts collected in output_artifacts/!")

def main():
    if "--post-build" in sys.argv:
        post_build()
        return

    accept_android_sdk_licenses()

    if os.path.exists(WORKSPACE):
        shutil.rmtree(WORKSPACE)

    if os.path.exists(os.path.join(BUNDLED_ENGINE, "Bcore")):
        print("[+] Copying bundled Bcore engine to build_workspace...")
        shutil.copytree(BUNDLED_ENGINE, WORKSPACE)
    else:
        print("[*] Cloning upstream BlackBox engine into build_workspace...")
        run(f'git clone --depth 1 https://github.com/ALEX5402/NewBlackbox.git "{WORKSPACE}"')

    gradlew_path = os.path.join(WORKSPACE, "gradlew")
    if os.path.exists(gradlew_path):
        st = os.stat(gradlew_path)
        os.chmod(gradlew_path, st.st_mode | stat.S_IEXEC)

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

    bcore_manifest = os.path.join(WORKSPACE, "Bcore", "src", "main", "AndroidManifest.xml")
    if os.path.exists(bcore_manifest):
        with open(bcore_manifest, "r", encoding="utf-8", errors="ignore") as f:
            bm = f.read()
        for attr in ["android:label", "android:icon", "android:roundIcon", "android:allowBackup", "android:supportsRtl", "android:theme"]:
            bm = re.sub(rf'\s+{attr}="[^"]*"', '', bm)
        with open(bcore_manifest, "w", encoding="utf-8") as f:
            f.write(bm)

    ws_app = os.path.join(WORKSPACE, "app")
    if os.path.exists(ws_app):
        shutil.rmtree(ws_app)
    shutil.copytree(os.path.join(ROOT, "app"), ws_app)

    manifest_path = os.path.join(ws_app, "src", "main", "AndroidManifest.xml")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            m_txt = f.read()
        m_txt = re.sub(r'\s+package="com\.veyravault\.space"', '', m_txt)
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(m_txt)

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

    gradle_props = os.path.join(WORKSPACE, "gradle.properties")
    props_content = """org.gradle.jvmargs=-Xmx4096m -Dfile.encoding=UTF-8 --add-opens=jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.code=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.comp=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.file=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.jvm=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.main=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.model=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.parser=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.processing=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.tree=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.util=ALL-UNNAMED
android.useAndroidX=true
android.enableJetifier=true
android.nonTransitiveRClass=false
"""
    with open(gradle_props, "w", encoding="utf-8") as f:
        f.write(props_content)

    # Generate Dedicated Release Keystore directly inside Python
    ks_file = os.path.join(ws_app, "release.keystore")
    if not os.path.exists(ks_file):
        print("[*] Generating dedicated RSA-2048 Release Keystore...")
        ks_cmd = (
            f'keytool -genkeypair -v -keystore "{ks_file}" '
            f'-alias veyravault_key -keyalg RSA -keysize 2048 -validity 10000 '
            f'-storepass VeyraVaultPass2025 -keypass VeyraVaultPass2025 '
            f'-dname "CN=VeyraVault, OU=Security, O=VeyraVault, L=Global, S=Global, C=US"'
        )
        run(ks_cmd)

    print("[+] Workspace, NDK licenses, and Release Keystore prepared successfully!")

if __name__ == "__main__":
    main()
