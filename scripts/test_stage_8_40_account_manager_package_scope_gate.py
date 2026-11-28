#!/usr/bin/env python3
"""Read-only source gate for AccountManager's package/user scope.

A PASS documents the audited scope boundary; it does NOT certify runtime
cross-package account or session isolation.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "build_workspace"


def read(relative: str) -> str:
    path = WORKSPACE / relative
    assert path.is_file(), f"Expected prepared pinned source missing: {path}"
    return path.read_text(encoding="utf-8")


def section(source: str, start: str, end: str, label: str) -> str:
    start_at = source.index(start)
    end_at = source.index(end, start_at)
    assert end_at > start_at, f"Invalid source range for {label}"
    return source[start_at:end_at]


service = read(
    "Bcore/src/main/java/top/niunaijun/blackbox/core/system/accounts/"
    "BAccountManagerService.java"
)
facade = read(
    "Bcore/src/main/java/top/niunaijun/blackbox/fake/frameworks/BAccountManager.java"
)
binder_proxy = read(
    "Bcore/src/main/java/top/niunaijun/blackbox/fake/service/IAccountManagerProxy.java"
)
hook_manager = read(
    "Bcore/src/main/java/top/niunaijun/blackbox/fake/hook/HookManager.java"
)
class_stub = read(
    "Bcore/src/main/java/top/niunaijun/blackbox/fake/hook/ClassInvocationStub.java"
)
google_proxy = read(
    "Bcore/src/main/java/top/niunaijun/blackbox/fake/service/GoogleAccountManagerProxy.java"
)
token_cache = read(
    "Bcore/src/main/java/top/niunaijun/blackbox/core/system/accounts/TokenCache.java"
)
user_accounts = read(
    "Bcore/src/main/java/top/niunaijun/blackbox/core/system/accounts/BUserAccounts.java"
)
account_record = read(
    "Bcore/src/main/java/top/niunaijun/blackbox/core/system/accounts/BAccount.java"
)
registry = read("app/src/main/java/com/veyravault/space/core/ProfileFieldRegistry.java")

# 1. Persistent account collection and lookup are keyed by numeric userId.
assert "Map<Integer, BUserAccounts> mUserAccountsMap" in service
lookup = section(
    service,
    "public BUserAccounts getUserAccounts(int userId)",
    "\n    private boolean isAccountPresentForCaller",
    "numeric AccountManager bucket lookup",
)
assert "mUserAccountsMap.get(userId)" in lookup
assert "mUserAccountsMap.put(userId, bUserAccounts)" in lookup
assert "packageName" not in lookup

# 2. Direct credential and persistent-token APIs use that bucket and do not add
# a packageName or trusted Binder-derived package identity to the lookup.
direct_methods = {
    "getPassword": section(
        service,
        "public String getPassword(Account account, int userId)",
        "\n    @Override\n    public String getUserData",
        "getPassword",
    ),
    "getUserData": section(
        service,
        "public String getUserData(Account account, String key, int userId)",
        "\n    @Override\n    public AuthenticatorDescription",
        "getUserData",
    ),
    "peekAuthToken": section(
        service,
        "public String peekAuthToken(Account account, String authTokenType, int userId)",
        "\n    @Override\n    public void setAuthToken",
        "peekAuthToken",
    ),
    "setAuthToken": section(
        service,
        "public void setAuthToken(Account account, String authTokenType, String authToken, int userId)",
        "\n    @Override\n    public void setPassword",
        "setAuthToken",
    ),
    "setPassword": section(
        service,
        "public void setPassword(Account account, String password, int userId)",
        "\n    @Override\n    public void clearPassword",
        "setPassword",
    ),
    "setUserData": section(
        service,
        "public void setUserData(Account account, String key, String value, int userId)",
        "\n    @Override\n    public void updateAppPermission",
        "setUserData",
    ),
}
for name, body in direct_methods.items():
    assert "getUserAccounts(userId)" in body, f"{name} bucket lookup changed"
    assert "packageName" not in body, f"{name} requires package-scope review"
    assert "getCallingPackageName()" not in body, f"{name} requires trusted-caller review"

# 3. Package-aware listing applies visibility. That boundary is not equivalent
# to credential/token API isolation.
listing = section(
    service,
    "public Account[] getAccountsForPackage(String packageName, int uid, int userId)",
    "\n    @Override\n    public Account[] getAccountsByTypeForPackage",
    "package-scoped account listing",
)
assert "getUserAccounts(userId)" in listing
assert "account.visibility.get(packageName)" in listing
assert "AccountManager.VISIBILITY_VISIBLE" in listing

listing_by_type = section(
    service,
    "public Account[] getAccountsByTypeForPackage(String type, String packageName, int userId)",
    "\n    @Override\n    public Account[] getAccountsAsUser",
    "package and type account listing",
)
assert "account.visibility.get(packageName)" in listing_by_type
assert "AccountManager.VISIBILITY_VISIBLE" in listing_by_type

# 4. Persistent token data is keyed under BAccount by account/token type.
# The custom in-memory TokenCache additionally compares packageName.
persistent_read = section(
    service,
    "protected String readAuthTokenInternal(BUserAccounts accounts, Account account,",
    "\n    private void completeCloningAccount",
    "persistent auth-token lookup",
)
persistent_write = section(
    service,
    "protected void saveAuthTokenToDatabase(BUserAccounts accounts, Account account, String",
    "\n    protected String readCachedTokenInternal",
    "persistent auth-token write",
)
custom_cache = section(
    service,
    "protected String readCachedTokenInternal(",
    "\n    protected String readAuthTokenInternal",
    "custom in-memory TokenCache lookup",
)
assert "accounts.getAuthToken(account)" in persistent_read
assert "authToken.get(authTokenType)" in persistent_read
assert "accounts.getAuthToken(account).put(authTokenType, authToken)" in persistent_write
assert "packageName" not in persistent_read
assert "packageName" not in persistent_write
assert "next.packageName.equals(callingPackage)" in custom_cache
assert "next.userId == accounts.userId" in custom_cache
assert "String packageName;" in token_cache
assert "Objects.equals(packageName, that.packageName)" in token_cache
assert "Map<String, String> authTokens" in account_record
assert "packageName" not in account_record
assert "userId" in user_accounts and "packageName" not in user_accounts

auth_method = section(
    service,
    "public void getAuthToken(IAccountManagerResponse response, Account account, String authTokenType",
    "\n    @Override\n    public void addAccount(",
    "getAuthToken",
)
assert "loginOptions.getString(AccountManager.KEY_ANDROID_PACKAGE_NAME)" in auth_method
assert "readAuthTokenInternal(accounts, account, authTokenType)" in auth_method
assert "readCachedTokenInternal(" in auth_method

# 5. The active Binder AccountManager proxy replaces ACCOUNT_SERVICE and routes
# calls to the BAccountManager facade, which supplies the current virtual userId.
assert "addInjector(new IAccountManagerProxy())" in hook_manager
assert "replaceSystemService(Context.ACCOUNT_SERVICE);" in binder_proxy
for annotation in (
    '@ProxyMethod("getPassword")',
    '@ProxyMethod("getUserData")',
    '@ProxyMethod("peekAuthToken")',
    '@ProxyMethod("setAuthToken")',
    '@ProxyMethod("getAuthToken")',
):
    assert annotation in binder_proxy
for call in (
    "BAccountManager.get().getPassword((Account) args[0])",
    "BAccountManager.get().getUserData((Account) args[0], (String) args[1])",
    "BAccountManager.get().peekAuthToken((Account) args[0], (String) args[1])",
    "BAccountManager.get().setAuthToken((Account) args[0], (String) args[1], (String) args[2])",
):
    assert call in binder_proxy
for call in (
    "getService().getPassword(account, BActivityThread.getUserId())",
    "getService().getUserData(account, key, BActivityThread.getUserId())",
    "getService().peekAuthToken(account, authTokenType, BActivityThread.getUserId())",
    "getService().setAuthToken(account, authTokenType, authToken, BActivityThread.getUserId())",
):
    assert call in facade

# 6. GoogleAccountManagerProxy contains mock fallback code, but its inject()
# body is empty in this pin. ClassInvocationStub builds a proxy then calls inject();
# this implementation does not publish/replace the proxy. Do not describe those
# mock fallback hooks as active under this pinned wiring.
assert "addInjector(new GoogleAccountManagerProxy())" in hook_manager
google_inject = section(
    google_proxy,
    "protected void inject(Object baseInvocation, Object proxyInvocation)",
    "\n    @Override\n    public boolean isBadEnv",
    "GoogleAccountManagerProxy injection",
)
assert "replaceSystemService" not in google_inject
assert "getProxyInvocation" not in google_inject
assert "createMockGoogleAccounts()" in google_proxy
assert '"mock_google_password"' in google_proxy
assert '"mock_google_auth_token_"' in google_proxy
class_inject = section(
    class_stub,
    "public void injectHook()",
    "\n    protected void initAnnotation",
    "ClassInvocationStub injection lifecycle",
)
assert "mProxyInvocation = Proxy.newProxyInstance" in class_inject
assert "inject(mBase, mProxyInvocation);" in class_inject
assert "return mProxyInvocation;" in class_stub

# 7. Keep unverified isolation fields explicitly NOT_IMPLEMENTED.
for field in (
    '"sessionDataIsolation", ValueType.BOOLEAN, Capability.NOT_IMPLEMENTED',
    '"cookieStorageIsolation", ValueType.BOOLEAN, Capability.NOT_IMPLEMENTED',
    '"databaseIsolation", ValueType.BOOLEAN, Capability.NOT_IMPLEMENTED',
    '"sharedPreferencesIsolation", ValueType.BOOLEAN, Capability.NOT_IMPLEMENTED',
):
    assert field in registry, "Unverified isolation field was promoted or removed: " + field

print("PASS: AccountManager persistent buckets are identified by numeric userId.")
print("PASS: direct password, user-data and auth-token APIs remain userId/account scoped.")
print("PASS: package visibility is separately applied to package-aware account listing.")
print("PASS: custom TokenCache compares packageName; persistent authTokens do not.")
print("PASS: active Binder AccountManager proxy and virtual-user facade route are identified.")
print("AUDIT: GoogleAccountManagerProxy is registered but inject() is empty in this pinned source; mock fallbacks are not wired by this injector path.")
print("KNOWN BLOCKER: different Clone packages sharing one numeric userId can resolve to the same persistent AccountManager bucket.")
print("PASS: unverified Clone data/session isolation capabilities remain NOT_IMPLEMENTED.")
print("AUDIT ONLY: no account, credential, token, Clone, session or runtime state was read or changed.")
