#!/usr/bin/env python3
"""Source-fixture tests for the pinned Engine AccountManager TokenCache user-scope fix."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREPARE_PATH = ROOT / "scripts" / "prepare_workspace.py"
SPEC = importlib.util.spec_from_file_location("veyravault_prepare_stage_837", PREPARE_PATH)
assert SPEC is not None and SPEC.loader is not None
prepare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare)

RELATIVE = (
    "Bcore/src/main/java/top/niunaijun/blackbox/core/system/accounts/"
    "BAccountManagerService.java"
)
FIXTURE = """package top.niunaijun.blackbox.core.system.accounts;

import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.Map;

public class BAccountManagerService {
    private final Map<Integer, BUserAccounts> mUserAccountsMap = new HashMap<>();

    private void loadAccounts() {
        HashMap<Integer, BUserAccounts> accountsMap = readPersistedAccounts();
        synchronized (mUserAccountsMap) {
            mUserAccountsMap.clear();
            for (Integer key : accountsMap.keySet()) {
                mUserAccountsMap.put(key, accountsMap.get(key));
            }
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
}
"""


class AccountManagerTokenUserScopePatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        path = self.root / RELATIVE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(FIXTURE, encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def source(self):
        return (self.root / RELATIVE).read_text(encoding="utf-8")

    def test_load_and_lookup_restore_user_id_from_authoritative_map_key(self):
        prepare.harden_account_manager_token_user_scope(str(self.root))
        source = self.source()

        self.assertIn("VEYRAVAULT_RESTORE_ACCOUNT_USER_ID_FROM_MAP_KEY", source)
        self.assertIn("userAccounts.userId = key.intValue();", source)
        self.assertIn("VEYRAVAULT_USE_REQUESTED_USER_ID_FOR_TOKEN_CACHE", source)
        self.assertIn("bUserAccounts.userId = userId;", source)
        self.assertIn("new TokenCache(accounts.userId,", source)
        self.assertIn("next.userId == accounts.userId", source)

        # Existing accounts map entries and token values are not cleared/recreated.
        self.assertIn("mUserAccountsMap.clear();", source)
        self.assertIn("mUserAccountsMap.put(key, userAccounts);", source)
        self.assertIn("mUserAccountsMap.put(userId, bUserAccounts);", source)
        self.assertNotIn("mTokenCaches.clear()", source)
        self.assertNotIn("accounts.clear()", source)
        self.assertNotIn("authTokens.clear()", source)
        self.assertNotIn("saveAllAccounts()", source)

    def test_patch_is_idempotent(self):
        prepare.harden_account_manager_token_user_scope(str(self.root))
        first = self.source()
        prepare.harden_account_manager_token_user_scope(str(self.root))
        self.assertEqual(first, self.source())

    def test_source_drift_fails_without_partially_writing_the_file(self):
        path = self.root / RELATIVE
        changed = FIXTURE.replace(
            "return mUserAccountsMap.get(userId);",
            "return null;",
        )
        path.write_text(changed, encoding="utf-8")
        before = path.read_text(encoding="utf-8")

        with self.assertRaisesRegex(RuntimeError, "no longer matches|verification failed"):
            prepare.harden_account_manager_token_user_scope(str(self.root))
        self.assertEqual(before, path.read_text(encoding="utf-8"))

    def test_wrong_persisted_user_id_is_not_used_as_the_token_cache_scope(self):
        prepare.harden_account_manager_token_user_scope(str(self.root))
        source = self.source()
        restore_position = source.index("userAccounts.userId = key.intValue();")
        map_insert_position = source.index("mUserAccountsMap.put(key, userAccounts);")
        lookup_position = source.index("bUserAccounts.userId = userId;")
        cache_position = source.index("new TokenCache(accounts.userId,")
        self.assertLess(restore_position, map_insert_position)
        self.assertLess(lookup_position, cache_position)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AccountManagerTokenUserScopePatchTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("Stage 8.37 AccountManager TokenCache user scope patch: PASS")
