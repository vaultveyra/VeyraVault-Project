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
clone_id_instrumentation = read("app/src/androidTest/java/com/veyravault/space/core/CloneUserIdScopeInstrumentationTest.java")
engine_wrapper = read("app/src/main/java/com/veyravault/space/core/Engine.java")
registry = read("app/src/main/java/com/veyravault/space/core/ProfileFieldRegistry.java")

# Exact pinned BlackBox sources after prepare_workspace has verified the immutable
# upstream checkout and applied only the already-audited cleanup hardening patch.
environment = read("Bcore/src/main/java/top/niunaijun/blackbox/core/env/BEnvironment.java")
account_service = read("Bcore/src/main/java/top/niunaijun/blackbox/core/system/accounts/BAccountManagerService.java")
account_facade = read("Bcore/src/main/java/top/niunaijun/blackbox/fake/frameworks/BAccountManager.java")
user_accounts = read("Bcore/src/main/java/top/niunaijun/blackbox/core/system/accounts/BUserAccounts.java")
user_manager = read("Bcore/src/main/java/top/niunaijun/blackbox/core/system/user/BUserManagerService.java")
hook_manager = read("Bcore/src/main/java/top/niunaijun/blackbox/fake/hook/HookManager.java")
webview_proxy = read("Bcore/src/main/java/top/niunaijun/blackbox/fake/service/WebViewProxy.java")
activity_thread = read("Bcore/src/main/java/top/niunaijun/blackbox/app/BActivityThread.java")

# 1. The ordinary virtual app data tree is keyed by both package and user.
assert 'String.format(Locale.CHINA, "data/user/%d/%s", userId, packageName)' in environment
assert 'String.format(Locale.CHINA, "data/user_de/%d/%s", userId, packageName)' in environment
assert 'String.format(Locale.CHINA, "Android/data/%s", packageName)' in environment
assert 'String.format(Locale.CHINA, "Android/obb/%s", packageName)' in environment
assert 'new File(getSystemDir(), "accounts.conf")' in environment

# 2. CloneStore identity remains composite, but active reservations are global and
# monotonic. Both independent Engine ID-only inventories are mandatory.
assert 'return packageName + "\\\\u0000" + userId;' in clone_store
reserve_start = clone_store.index("static synchronized CloneReservation reserveNextUserId")
reserve_end = clone_store.index("static synchronized List<CloneReservation>", reserve_start)
reserve_body = clone_store[reserve_start:reserve_end]
assert "List<Integer> engineUserIds" in reserve_body
assert "List<Integer> accountUserIds" in reserve_body
assert "maxKnownId + 1" in reserve_body
assert "KEY_GLOBAL_HIGH_WATER_MARK" in reserve_body
assert "putInt(KEY_GLOBAL_HIGH_WATER_MARK, candidate)" in reserve_body
assert "editor.commit()" in reserve_body
assert "validateIdInventory" in reserve_body

# The old package-scoped helper is retained only as a deprecated preview API.
next_start = clone_store.index("public static synchronized int nextFreeUserIdForPackage")
next_end = clone_store.index("\n        public static", next_start)
next_body = clone_store[next_start:next_end]
assert "entry.packageName.equals(pkg)" in next_body
assert "reservation.packageName.equals(pkg)" in next_body
assert "@Deprecated" in clone_store[max(0, next_start - 250):next_start]
provision = read("app/src/main/java/com/veyravault/space/core/AsyncCloneProvisionRepository.java")
assert "Engine.getKnownVirtualUserIds()" in provision
assert "Engine.getKnownAccountUserIds()" in provision
assert "EngineOperationQueue.submit(" in provision
assert provision.index("Engine.getKnownAccountUserIds()") < provision.index("persistence.reserveNextUserId(packageName")
assert provision.index("persistence.reserveNextUserId(packageName") < provision.index("Engine.installPackageAsUser(")

# Removal never lowers the ledger; synthetic tests exercise only disposable registry data.
remove_start = clone_store.index("public static synchronized boolean removeClone")
remove_end = clone_store.index("\n        public static", remove_start)
remove_body = clone_store[remove_start:remove_end]
assert "return saveAll(c, kept);" in remove_body
assert "globalAllocatorNeverReservesSameNumericUserIdForDifferentPackages" in clone_id_instrumentation
assert "removedCloneRegistryEntryDoesNotLowerGlobalHighWaterMark" in clone_id_instrumentation

# 3. AccountManager persistence is keyed only by virtual userId, not packageName.
assert "private final Map<Integer, BUserAccounts> mUserAccountsMap = new HashMap<>();" in account_service
assert "BEnvironment.getAccountsConf()" in account_service
assert "HashMap<?, ?> accountsMap" in account_service
get_accounts_start = account_service.index("public BUserAccounts getUserAccounts(int userId)")
get_accounts_end = account_service.index("\n    private boolean isAccountPresentForCaller", get_accounts_start)
get_accounts_body = account_service[get_accounts_start:get_accounts_end]
assert "mUserAccountsMap.get(userId)" in get_accounts_body
assert "mUserAccountsMap.put(userId, bUserAccounts)" in get_accounts_body
assert "getAccountUserData" in user_accounts
assert "getAuthToken" in user_accounts

# TokenCache relies on the value's internal userId, which must be restored from the
# authoritative outer Map key both on load and on every user-bucket lookup.
assert "userAccounts.userId = key.intValue();" in account_service
assert "bUserAccounts.userId = userId;" in account_service
assert "new TokenCache(accounts.userId," in account_service
assert "next.userId == accounts.userId" in account_service

# Stage 8.38 adds a fail-closed, numeric-key-only AccountManager inventory. It must
# not return an empty array when accounts.conf failed to load or contains invalid data.
inventory_start = account_service.index("public int[] getKnownAccountUserIds()")
inventory_end = account_service.index("\n    private void saveAllAccounts()", inventory_start)
inventory_body = account_service[inventory_start:inventory_end]
assert "mAccountsLoadSucceeded" in inventory_body
assert "throw new RemoteException(" in inventory_body
assert "Arrays.sort(ids);" in inventory_body
assert "new int[mUserAccountsMap.size()]" in inventory_body
assert "entry.getValue() == null" in inventory_body
assert "getPassword(" not in inventory_body
assert "getUserData(" not in inventory_body
assert "authTokens" not in inventory_body
assert "saveAllAccounts()" not in inventory_body

load_start = account_service.index("private void loadAccounts()")
load_end = account_service.index("\n    @Override\n    public int[] getKnownAccountUserIds()", load_start)
load_body = account_service[load_start:load_end]
assert "mAccountsLoadSucceeded = false;" in load_body
assert "if (!userInfoConf.exists())" in load_body
assert "mAccountsLoadSucceeded = true;" in load_body
assert "if (!userInfoConf.isFile() || !userInfoConf.canRead())" in load_body
assert "HashMap<?, ?> accountsMap" in load_body
assert "VEYRAVAULT_RESTORE_ACCOUNT_USER_ID_FROM_MAP_KEY" in load_body
assert "userAccounts.userId = key.intValue();" in load_body
assert "verifiedAccountsMap.put(key, userAccounts);" in load_body
assert "mUserAccountsMap.putAll(verifiedAccountsMap);" in load_body
assert "mAccountsLoadSucceeded = true;" in load_body[load_body.index("mUserAccountsMap.putAll(verifiedAccountsMap);"):]

account_aidl = read(
    "Bcore/src/main/aidl/top/niunaijun/blackbox/core/system/accounts/IBAccountManagerService.aidl"
)
assert "int[] getKnownAccountUserIds();" in account_aidl
assert "public static List<Integer> getKnownAccountUserIds() throws Exception" in engine_wrapper
assert "top.niunaijun.blackbox.fake.frameworks.BAccountManager" in engine_wrapper
assert "IBAccountManagerService" in engine_wrapper

# Listing APIs do have package visibility filtering, but direct credential,
# user-data and token operations are routed by virtual userId + account handle.
assert "account.visibility.get(packageName)" in account_service
assert "filterAccounts(userAccounts" in account_service
for call in (
    "getService().getPassword(account, BActivityThread.getUserId())",
    "getService().getUserData(account, key, BActivityThread.getUserId())",
    "getService().peekAuthToken(account, authTokenType, BActivityThread.getUserId())",
    "getService().setAuthToken(account, authTokenType, authToken, BActivityThread.getUserId())",
    "getService().getAuthToken(response, account, authTokenType, notifyOnAuthFailure, expectActivityLaunch, options, BActivityThread.getUserId())",
):
    assert call in account_facade, "Expected virtual-user-scoped AccountManager call missing: " + call

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

# 5. The active WebView path is in BActivityThread, not the unused WebViewProxy.
# It is gated to API 28+ and called before VirtualRuntime binds the target app.
suffix_call = 'WebView.setDataDirectorySuffix(getUserId() + ":" + packageName + ":" + processName);'
suffix_position = activity_thread.index(suffix_call)
assert "if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P)" in activity_thread[suffix_position - 160:suffix_position]
assert activity_thread.index("Context packageContext = createPackageContext(applicationInfo);") < suffix_position
assert suffix_position < activity_thread.index("VirtualRuntime.setupRuntime(processName, applicationInfo);")
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
print("PASS: global monotonic Clone ID allocation uses validated Engine and AccountManager inventories.")
print("PASS: pinned Engine AccountManager persistence is keyed by userId only.")
print("PASS: TokenCache userId is reconstructed from the authoritative AccountManager map key.")
print("PASS: per-package uninstall does not purge the virtual-user account collection.")
print("PASS: user-wide deletion is distinguished from package-scoped Clone uninstall.")
print("PASS: WebView uses the pinned package/user/process suffix before target Application binding.")
print("PASS: the unused WebViewProxy class is not mistaken for the active mechanism.")
print("PASS: unverified storage/session fields remain NOT_IMPLEMENTED.")
print("KNOWN BLOCKER: AccountManager scope can cross package Clones sharing a numeric userId; ID inventory reports collisions but does not fix storage scope.")
print("PASS: AccountManager map-key inventory is read-only, ID-only and fails closed on unverified load state.")
print("AUDIT ONLY: no Clone data, account, token, session or runtime state was accessed or changed.")
