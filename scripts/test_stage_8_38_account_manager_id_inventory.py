#!/usr/bin/env python3
"""Source-fixture tests for the fail-closed, ID-only AccountManager inventory patch."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREPARE_PATH = ROOT / "scripts" / "prepare_workspace.py"
SPEC = importlib.util.spec_from_file_location("veyravault_prepare_stage_838", PREPARE_PATH)
assert SPEC is not None and SPEC.loader is not None
prepare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare)

SERVICE_RELATIVE = (
    "Bcore/src/main/java/top/niunaijun/blackbox/core/system/accounts/"
    "BAccountManagerService.java"
)
AIDL_RELATIVE = (
    "Bcore/src/main/aidl/top/niunaijun/blackbox/core/system/accounts/"
    "IBAccountManagerService.aidl"
)

SERVICE_FIXTURE = """package top.niunaijun.blackbox.core.system.accounts;

import android.os.Parcel;
import android.os.RemoteException;
import java.io.InputStream;
import java.io.File;
import java.io.FileInputStream;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.LinkedList;
import java.util.Map;

public class BAccountManagerService {
    private final Map<Integer, BUserAccounts> mUserAccountsMap = new HashMap<>();

    private void loadAccounts() {
        Parcel parcel = Parcel.obtain();
        InputStream is = null;
        try {
            File userInfoConf = BEnvironment.getAccountsConf();
            if (!userInfoConf.exists()) {
                return;
            }
            is = new FileInputStream(BEnvironment.getAccountsConf());
            byte[] bytes = FileUtils.toByteArray(is);
            parcel.unmarshall(bytes, 0, bytes.length);
            parcel.setDataPosition(0);

            HashMap<Integer, BUserAccounts> accountsMap = parcel.readHashMap(BUserAccounts.class.getClassLoader());
            if (accountsMap == null)
                return;
            synchronized (mUserAccountsMap) {
                mUserAccountsMap.clear();
                for (Integer key : accountsMap.keySet()) {
                    mUserAccountsMap.put(key, accountsMap.get(key));
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            parcel.recycle();
            CloseUtils.close(is);
        }
    }

    public BUserAccounts getUserAccounts(int userId) {
        synchronized (mUserAccountsMap) {
            BUserAccounts bUserAccounts = mUserAccountsMap.get(userId);
            if (bUserAccounts == null) {
                bUserAccounts = new BUserAccounts();
                mUserAccountsMap.put(userId, bUserAccounts);
            }
            return mUserAccountsMap.get(userId);
        }
    }

    protected void saveCachedToken(BUserAccounts accounts, Account account,
                                   String callerPkg, String tokenType, String token) {
        TokenCache cache = new TokenCache(accounts.userId, account, callerPkg, tokenType, token);
        mTokenCaches.add(cache);
    }

    protected String readCachedTokenInternal(BUserAccounts accounts, Account account,
                                             String tokenType, String callingPackage) {
        Iterator<TokenCache> iterator = mTokenCaches.iterator();
        while (iterator.hasNext()) {
            TokenCache next = iterator.next();
            if (next.userId == accounts.userId
                    && next.account.equals(account)
                    && next.authTokenType.equals(tokenType)
                    && next.packageName.equals(callingPackage)) {
                return next.authToken;
            }
        }
        return null;
    }

    private HashMap<Integer, BUserAccounts> readPersistedAccounts() {
        return new HashMap<>();
    }
    private final LinkedList<TokenCache> mTokenCaches = new LinkedList<>();

    private void saveAllAccounts() {
        // Fixture only. The inventory operation must never invoke this method.
    }
}
"""

AIDL_FIXTURE = """package top.niunaijun.blackbox.core.system.accounts;
interface IBAccountManagerService {
    void registerAccountListener(in String[] accountTypes, String opPackageName, int userId);
    void unregisterAccountListener(in String[] accountTypes, String opPackageName, int userId);
}
"""


class AccountManagerIdInventoryPatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        service_path = self.root / SERVICE_RELATIVE
        aidl_path = self.root / AIDL_RELATIVE
        service_path.parent.mkdir(parents=True, exist_ok=True)
        aidl_path.parent.mkdir(parents=True, exist_ok=True)
        service_path.write_text(SERVICE_FIXTURE, encoding="utf-8")
        aidl_path.write_text(AIDL_FIXTURE, encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def service(self):
        return (self.root / SERVICE_RELATIVE).read_text(encoding="utf-8")

    def aidl(self):
        return (self.root / AIDL_RELATIVE).read_text(encoding="utf-8")

    def apply(self):
        # The real build applies Stage 8.37 first, then adds the inventory API.
        prepare.harden_account_manager_token_user_scope(str(self.root))
        prepare.harden_account_manager_id_inventory(str(self.root))

    def test_inventory_is_sorted_id_only_and_fails_closed(self):
        self.apply()
        service = self.service()
        aidl = self.aidl()
        start = service.index("public int[] getKnownAccountUserIds()")
        end = service.index("\n    private void saveAllAccounts()", start)
        body = service[start:end]

        self.assertIn("int[] getKnownAccountUserIds();", aidl)
        self.assertIn("if (!mAccountsLoadSucceeded)", body)
        self.assertIn("throw new RemoteException(", body)
        self.assertIn("new int[mUserAccountsMap.size()]", body)
        self.assertIn("Arrays.sort(ids);", body)
        self.assertIn("entry.getValue() == null", body)
        self.assertNotIn("getPassword(", body)
        self.assertNotIn("getUserData(", body)
        self.assertNotIn("authTokens", body)
        self.assertNotIn("saveAllAccounts()", body)

    def test_load_status_is_success_only_after_full_map_validation(self):
        self.apply()
        service = self.service()
        start = service.index("private void loadAccounts()")
        end = service.index("\n    @Override\n    public int[] getKnownAccountUserIds()", start)
        body = service[start:end]

        self.assertLess(body.index("mAccountsLoadSucceeded = false;"),
                        body.index("File userInfoConf"))
        self.assertIn("if (!userInfoConf.exists())", body)
        self.assertIn("mAccountsLoadSucceeded = true;", body)
        self.assertIn("if (!userInfoConf.isFile() || !userInfoConf.canRead())", body)
        self.assertIn("HashMap<?, ?> accountsMap", body)
        self.assertIn("HashMap<Integer, BUserAccounts> verifiedAccountsMap", body)
        self.assertIn("rawKey instanceof Integer", body)
        self.assertIn("rawValue instanceof BUserAccounts", body)
        self.assertIn("mUserAccountsMap.putAll(verifiedAccountsMap);", body)
        self.assertLess(body.index("mUserAccountsMap.putAll(verifiedAccountsMap);"),
                        body.rindex("mAccountsLoadSucceeded = true;"))
        self.assertNotIn("saveAllAccounts()", body)

    def test_inventory_does_not_clear_or_persist_account_data(self):
        self.apply()
        service = self.service()
        start = service.index("public int[] getKnownAccountUserIds()")
        end = service.index("\n    private void saveAllAccounts()", start)
        body = service[start:end]
        for forbidden in (
            "mUserAccountsMap.clear()",
            "mTokenCaches.clear()",
            "removeAccount",
            "setPassword",
            "setUserData",
            "setAuthToken",
            "saveAllAccounts",
        ):
            self.assertNotIn(forbidden, body)

    def test_patch_is_idempotent(self):
        self.apply()
        first_service, first_aidl = self.service(), self.aidl()
        self.apply()
        self.assertEqual(first_service, self.service())
        self.assertEqual(first_aidl, self.aidl())

    def test_source_drift_fails_before_either_engine_file_is_written(self):
        prepare.harden_account_manager_token_user_scope(str(self.root))
        service_path = self.root / SERVICE_RELATIVE
        aidl_path = self.root / AIDL_RELATIVE
        drifted = self.service().replace(
            "mUserAccountsMap.put(key, userAccounts);",
            "mUserAccountsMap.put(key, null);",
            1,
        )
        service_path.write_text(drifted, encoding="utf-8")
        service_before = service_path.read_text(encoding="utf-8")
        aidl_before = aidl_path.read_text(encoding="utf-8")

        with self.assertRaisesRegex(RuntimeError, "no longer matches|verification failed|no longer matches the audited"):
            prepare.harden_account_manager_id_inventory(str(self.root))

        self.assertEqual(service_before, service_path.read_text(encoding="utf-8"))
        self.assertEqual(aidl_before, aidl_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AccountManagerIdInventoryPatchTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("Stage 8.38 AccountManager ID-only inventory patch: PASS")
