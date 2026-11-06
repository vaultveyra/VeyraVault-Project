#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FILE = os.path.join(ROOT, "scripts", "upgrade_v3_part2.py")

with open(FILE, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Fix ambiguous Toast.makeText in AddAppActivity generator
text = text.replace(
    "Toast.makeText(AddAppActivity.this,",
    "Toast.makeText(AddAppActivity.this, (CharSequence)"
)

# 2. Fix MainActivity: getNewYorkGregorianDate called with wrong boolean arg
text = text.replace(
    "JalaliClockUtil.getNewYorkGregorianDate(fa)",
    "JalaliClockUtil.getNewYorkGregorianDate()"
)

# 3. Fix GlobalEnvironmentActivity: setGlobalDeviceIdentity missing device param
text = text.replace(
    "CloneMetadataStore.setGlobalDeviceIdentity(this, brand, model);",
    "CloneMetadataStore.setGlobalDeviceIdentity(this, brand, model, model);"
)

# 4. Fix GlobalEnvironmentActivity: setGlobalProxy wrong argument count/order
# Replace the incorrect line with correct boolean-first signature
old_proxy = "CloneMetadataStore.setGlobalProxy(this, etProxyHost.getText().toString().trim(), proxyPort);"
new_proxy = "CloneMetadataStore.setGlobalProxy(this, true, etProxyHost.getText().toString().trim(), proxyPort);"
text = text.replace(old_proxy, new_proxy)

# 5. Fix MainActivity: missing triggerQuickLock() method -> replace call with inline security lock launch
text = text.replace(
    "triggerQuickLock();",
    "SecurityManager.setSessionUnlocked(false); startActivity(new Intent(MainActivity.this, SecurityLockActivity.class));"
)

# 6. Fix MainActivity: missing switchLanguageInstant() -> replace with LocaleHelper toggle
text = text.replace(
    "switchLanguageInstant();",
    "LocaleHelper.toggleLanguage(MainActivity.this); recreate();"
)

# 7. Fix MainActivity: isPersian() missing -> replace with LocaleHelper.isPersian
text = text.replace(
    "isPersian() ?",
    "LocaleHelper.isPersian(MainActivity.this) ?"
)
text = text.replace(
    "isPersian()",
    "LocaleHelper.isPersian(MainActivity.this)"
)

with open(FILE, "w", encoding="utf-8") as f:
    f.write(text)

print("[Fix] scripts/upgrade_v3_part2.py patched successfully. Next CI run should compile.")
