#!/usr/bin/env python3
"""Read-only source audit for Stage 8.35 Clone session/account isolation.

This test intentionally detects and documents the current scope mismatch. A PASS
means the audit recognized the known blocker; it does NOT mean session isolation
has been implemented or certified.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "build_workspace"

def read(relative: str) -> str:
    path = WORKSPACE / relative
    assert path.is_file(), f"Expected prepared pinned source missing: {path}"
    return path.read_text(encoding="utf-8")

# VeyraVault identity and allocation.
clone_store = read("app/src/main/java/com/veyravault/space/core/CloneStore.java")
engine_wrapper = read("app/src/main/java/com/veyravault/space/core/Engine.java")
registry = read("app/src/main/java/com/veyravault/space/core/ProfileFieldRegistry.java")

# Exact pinned BlackBox sources after prepare_workspace has verified the immutable
# upstream checkout and applied only the already-audited cleanup hardening patch.
environment = read("Bcore/src/main/java/top/niunaijun/blackbox/core/env/BEnvironment.java")
account_service = read("Bcore/src/main/java/top/niunaijun/blackbox/core/system/accounts/BAccountManagerService.java")
user_accounts = read("Bcore/src/main/java/top/niunaijun/blackbox/core/system/accounts/BUserAccounts.java")
user_manager = read("Bcore/src/main/java/top/niunaijun/blackbox/core/system/user/BUserManagerService.java")
hook_manager = read("Bcore/src/main/java/top/niunaijun/blackbox/fake/hook/HookManager.java")
webview_proxy = read("Bcore/src/main/java/top/niunaijun/blackbox/fake/service/WebViewProxy.java")

# 1. The ordinary virtual app data tree is keyed by both package and user.
assert 'String.format(Locale.CHINA, "data/user/%d/%s", userId, packageName)' in environment
assert 'String.format(Locale.CHINA, "data/user_de/%d/%s", userId, packageName)' in environment
assert 'String.format(Locale.CHINA, "Android/data/%s", packageName)' in environment
assert 'String.format(Locale.CHINA, "Android/obb/%s", packageName)' in environment
assert 'new File(getSystemDir(), "accounts.conf")' in environment

# 2. CloneStore identity is composite, and the allocator deliberately reuses the
# numeric user-ID sequence independently for each package.
assert 'return packageName + "\\\\u0000" + userId;' in clone_store
reserve_start = clone_store.index("static synchronized CloneReservation reserveNextUserId")
reserve_end = clone_store.index("static synchronized List<CloneReservation>", reserve_start)
reserve_body = clone_store[reserve_start:reserve_end]
assert "packageName.equals(entry.packageName)" in reserve_body
assert "packageName.equals(reservation.packageName)" in reserve_body
assert "int candidate = 0;" in reserve_body
assert "while (used.contains(candidate))" in reserve_body

next_start = clone_store.index("public static synchronized int nextFreeUserIdForPackage")
next_end = clone_store.index("\n        public static", next_start)
next_body = clone_store[next_start:next_end]
assert "packageName.equals(entry.packageName)" in next_body
assert "packageName.equals(reservation.packageName)" in next_body
assert "int uid = 0;" in next_body

# 3. AccountManager persistence is keyed only by virtual userId, not packageName.
assert "private final Map<Integer, BUserAccounts> mUserAccountsMap = new HashMap<>();" in account_service
assert "BEnvironment.getAccountsConf()" in account_service
assert "HashMap<Integer, BUserAccounts> accountsMap" in account_service
get_accounts_start = account_service.index("public BUserAccounts getUserAccounts(int userId)")
get_accounts_end = account_service.index("\n    private boolean isAccountPresentForCaller", get_accounts_start)
get_accounts_body = account_service[get_accounts_start:get_accounts_end]
assert "mUserAccountsMap.get(userId)" in get_accounts_body
assert "mUserAccountsMap.put(userId, bUserAccounts)" in get_accounts_body
assert "getAccountUserData" in user_accounts
assert "getAuthToken" in user_accounts

# Account records are retained by the package-uninstall callback; it only reloads
# authenticator metadata. This must be reviewed before claiming account cleanup.
uninstall_callback_start = account_service.index("public void onPackageUninstalled(")
uninstall_callback_end = account_service.index("\n    @Override", uninstall_callback_start)
uninstall_callback = account_service[uninstall_callback_start:uninstall_callback_end]
assert "loadAuthenticatorCache(null)" in uninstall_callback
assert "removeAccount" not in uninstall_callback
assert "mUserAccountsMap.remove" not in uninstall_callback

# 4. Deleting an Engine virtual user is a wider operation than uninstalling one
# package Clone: it loops package states and removes the whole user's data roots.
delete_user_start = user_manager.index("public void deleteUser(int userId)")
delete_user_end = user_manager.index("\n    private BUserInfo createUserLocked", delete_user_start)
delete_user_body = user_manager[delete_user_start:delete_user_end]
assert "BPackageManagerService.get().deleteUser(userId)" in delete_user_body
assert "BEnvironment.getUserDir(userId)" in delete_user_body
assert "BEnvironment.getExternalUserDir(userId)" in delete_user_body

# The current VeyraVault per-Clone uninstall path remains package-scoped. It must
# not be silently replaced with the user-wide deletion API.
uninstall_start = engine_wrapper.index("public static boolean uninstallClone(")
uninstall_end = engine_wrapper.index("\n    public static boolean isGmsInstalled", uninstall_start)
uninstall_body = engine_wrapper[uninstall_start:uninstall_end]
assert '"uninstallPackageAsUser", String.class, int.class' in uninstall_body
assert "deleteUser" not in uninstall_body

# 5. WebViewProxy exists in the pinned source but is not installed as an active
# HookManager injector. Its source presence is not proof of effective isolation.
assert "class WebViewProxy" in webview_proxy
assert "WebViewProxy" not in hook_manager
assert "new WebViewProxy()" not in hook_manager

# 6. Keep the UI/profile registry honest: storage/session features remain
# NOT_IMPLEMENTED until a real package/user adapter and isolation tests exist.
for field in (
    '"sessionDataIsolation", ValueType.BOOLEAN, Capability.NOT_IMPLEMENTED',
    '"cookieStorageIsolation", ValueType.BOOLEAN, Capability.NOT_IMPLEMENTED',
    '"databaseIsolation", ValueType.BOOLEAN, Capability.NOT_IMPLEMENTED',
    '"sharedPreferencesIsolation", ValueType.BOOLEAN, Capability.NOT_IMPLEMENTED',
):
    assert field in registry, "Unverified isolation field was promoted or removed: " + field

print("PASS: ordinary Clone app-data paths use packageName + userId.")
print("PASS: VeyraVault package-scoped ID allocation was identified.")
print("PASS: pinned Engine AccountManager persistence is keyed by userId only.")
print("PASS: per-package uninstall does not purge the virtual-user account collection.")
print("PASS: user-wide deletion is distinguished from package-scoped Clone uninstall.")
print("PASS: WebViewProxy is not mistaken for an active registered isolation hook.")
print("PASS: unverified storage/session fields remain NOT_IMPLEMENTED.")
print("KNOWN BLOCKER: AccountManager scope can cross package Clones sharing a numeric userId.")
print("AUDIT ONLY: no Clone data, account, token, session or runtime state was accessed or changed.")
