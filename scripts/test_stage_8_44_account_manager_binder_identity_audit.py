#!/usr/bin/env python3
"""Read-only audit of trusted Binder identity propagation in pinned AccountManager source."""
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


base = "Bcore/src/main/java/top/niunaijun/blackbox/"
service = read(base + "core/system/accounts/BAccountManagerService.java")
process_record = read(base + "core/system/ProcessRecord.java")
process_manager = read(base + "core/system/BProcessManagerService.java")
user_accounts = read(base + "core/system/accounts/BUserAccounts.java")
account_record = read(base + "core/system/accounts/BAccount.java")
token_cache = read(base + "core/system/accounts/TokenCache.java")
aidl = read("Bcore/src/main/aidl/top/niunaijun/blackbox/core/system/accounts/IBAccountManagerService.aidl")

# A trusted PID -> virtual ProcessRecord -> package identity path exists.
caller_identity = section(
    service,
    "private String getCallingPackageName()",
    "\n}",
    "Binder caller package helper",
)
assert "Binder.getCallingPid()" in caller_identity
assert "BProcessManagerService.get().findProcessByPid(callingPid)" in caller_identity
assert "processByPid.getPackageName()" in caller_identity
assert "public String getPackageName()" in process_record
assert "return info.packageName;" in process_record
assert "public ProcessRecord findProcessByPid(int pid)" in process_manager
assert "public int userId;" in process_record

# The helper currently does not bind/validate the requested virtual userId.
assert "processByPid.userId" not in caller_identity
assert "userId" not in caller_identity

# Direct APIs still select the numeric-only bucket without trusted package scope.
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
    assert "getUserAccounts(userId)" in body, f"{name} bucket lookup changed; re-audit"
    assert "getCallingPackageName()" not in body, f"{name} requires a fresh scope audit"

# Account records and user buckets contain no authoritative package owner.
assert "Map<Integer, BUserAccounts> mUserAccountsMap" in service
assert "public int userId;" in user_accounts
assert "packageName" not in user_accounts
assert "Map<String, String> authTokens" in account_record
assert "packageName" not in account_record
assert "String packageName;" in token_cache

# getAuthToken currently trusts a package string from request options.
auth = section(
    service,
    "public void getAuthToken(IAccountManagerResponse response, Account account, String authTokenType",
    "\n    @Override\n    public void addAccount(",
    "getAuthToken",
)
assert "loginOptions.getString(AccountManager.KEY_ANDROID_PACKAGE_NAME)" in auth
assert "getCallingPackageName()" not in auth

# Async Session retains the numeric bucket but no immutable Clone scope.
session = section(
    service,
    "private abstract class Session extends IAccountAuthenticatorResponse.Stub",
    "\n    private String getCallingPackageName()",
    "AccountManager Session",
)
assert "protected final BUserAccounts mAccounts;" in session
assert "mAccounts = accounts;" in session
assert "AccountScope" not in session
assert "mPackageName" not in session

# Listener APIs exist but are empty in the pinned service.
for method in ("registerAccountListener", "unregisterAccountListener"):
    body = section(
        service,
        f"public void {method}(String[] accountTypes, String opPackageName, int userId)",
        "\n    @Override",
        method,
    )
    assert body.rstrip().endswith("{\n\n    }"), f"{method} changed; re-audit listener behavior"

# The AIDL currently passes numeric userId. Trusted package identity must be captured server-side.
assert "String getPassword(in Account account, int userId);" in aidl
assert "String getUserData(in Account account, String key, int userId);" in aidl

print("PASS: pinned Engine has a Binder PID -> ProcessRecord -> package identity lookup.")
print("KNOWN GAP: caller identity helper does not validate ProcessRecord.userId against requested userId.")
print("KNOWN GAP: direct credential/token methods still use numeric userId buckets.")
print("KNOWN GAP: getAuthToken takes caller package from Bundle options, not trusted Binder identity.")
print("KNOWN GAP: asynchronous Session retains BUserAccounts but no immutable package/user scope.")
print("KNOWN GAP: account listener registration/unregistration methods are empty.")
print("PASS: legacy account/user records have no authoritative package owner; migration must remain unresolved.")
print("AUDIT ONLY: no account, credential, token, session, Clone or persistent runtime data was accessed or changed.")
