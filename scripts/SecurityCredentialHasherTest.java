import com.veyravault.space.security.SecurityCredentialHasher;
import java.security.MessageDigest;
import java.nio.charset.Charset;

public final class SecurityCredentialHasherTest {
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    private static String legacyHash(String secret) throws Exception {
        byte[] bytes = MessageDigest.getInstance("SHA-256")
                .digest(("VeyraSalt_" + secret).getBytes(Charset.forName("UTF-8")));
        StringBuilder out = new StringBuilder();
        for (byte b : bytes) out.append(String.format("%02x", b & 0xff));
        return out.toString();
    }

    public static void main(String[] args) throws Exception {
        String secret = "5831";
        String sha256 = SecurityCredentialHasher.createHash(secret, true);
        check(sha256.startsWith("v2$pbkdf2-sha256$"), "new SHA-256 format must be versioned");
        check(SecurityCredentialHasher.verify(secret, sha256, true).valid, "correct v2 secret");
        check(!SecurityCredentialHasher.verify("5832", sha256, true).valid, "wrong v2 secret");
        check(!SecurityCredentialHasher.verify(null, sha256, true).valid, "null secret rejected");
        check(!SecurityCredentialHasher.verify(secret, "v2$broken", true).valid, "malformed hash rejected");

        String sha1 = SecurityCredentialHasher.createHash(secret, false);
        check(sha1.startsWith("v2$pbkdf2-sha1$"), "API 21-25 compatible algorithm is versioned");
        check(SecurityCredentialHasher.verify(secret, sha1, true).valid, "sha1 variant remains verifiable");

        String legacy = legacyHash(secret);
        SecurityCredentialHasher.Verification migration =
                SecurityCredentialHasher.verify(secret, legacy, true);
        check(migration.valid, "legacy credentials must continue to verify");
        check(migration.upgradedHash != null && migration.upgradedHash.startsWith("v2$"),
                "valid legacy credential must produce upgraded hash");
        check(SecurityCredentialHasher.verify(secret, migration.upgradedHash, true).valid,
                "upgraded legacy credential must verify");
        check(!SecurityCredentialHasher.verify("wrong", legacy, true).valid,
                "wrong legacy secret must fail");
        System.out.println("SecurityCredentialHasher tests: PASS");
    }
}
