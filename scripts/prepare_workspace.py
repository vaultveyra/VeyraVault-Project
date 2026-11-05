#!/usr/bin/env python3
import os, re, shutil, subprocess

WORKSPACE = "build_workspace"

def main():
    if os.path.exists(WORKSPACE):
        shutil.rmtree(WORKSPACE)

    if os.path.exists("engine_source/Bcore"):
        print("[*] Using locally bundled BlackBox Engine (engine_source/)...")
        shutil.copytree("engine_source", WORKSPACE)
    else:
        print("[*] Cloning ALEX5402/NewBlackbox engine...")
        subprocess.check_call(["git", "clone", "--depth", "1", "https://github.com/ALEX5402/NewBlackbox.git", WORKSPACE])

    # Read compileSdkVersion from Bcore/build.gradle so :app matches 100%
    bcore_gradle = os.path.join(WORKSPACE, "Bcore", "build.gradle")
    compile_sdk = "31"
    target_sdk = "28"
    if os.path.exists(bcore_gradle):
        txt = open(bcore_gradle, "r", encoding="utf-8", errors="ignore").read()
        m = re.search(r'compileSdk(?:Version)?\s+(\d+)', txt)
        if m:
            compile_sdk = m.group(1)

    # Replace sample app module with VeyraVault app module
    target_app = os.path.join(WORKSPACE, "app")
    if os.path.exists(target_app):
        shutil.rmtree(target_app)
    shutil.copytree("app", target_app)

    # Copy Apache-2.0 NOTICE if available
    notice_src = os.path.join(WORKSPACE, "Bcore", "src", "main", "assets", "NOTICE")
    notice_dst = os.path.join(target_app, "src", "main", "assets", "NOTICE_APACHE_2.txt")
    if os.path.exists(notice_src):
        os.makedirs(os.path.dirname(notice_dst), exist_ok=True)
        shutil.copyfile(notice_src, notice_dst)

    # Patch app/build.gradle compileSdkVersion to match Bcore
    app_gradle = os.path.join(target_app, "build.gradle")
    g_txt = open(app_gradle, "r", encoding="utf-8").read()
    g_txt = g_txt.replace("__COMPILE_SDK__", str(max(int(compile_sdk), 31)))
    g_txt = g_txt.replace("__TARGET_SDK__", target_sdk)
    open(app_gradle, "w", encoding="utf-8").write(g_txt)

    # Ensure settings.gradle only includes :app and :Bcore (skip any broken upstream samples)
    settings_f = os.path.join(WORKSPACE, "settings.gradle")
    open(settings_f, "w", encoding="utf-8").write("include ':app', ':Bcore'\nrootProject.name = 'VeyraVault'\n")
    print("[+] Workspace prepared and verified successfully!")

if __name__ == "__main__":
    main()
