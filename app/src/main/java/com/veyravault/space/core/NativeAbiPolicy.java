package com.veyravault.space.core;

import java.util.Locale;
import java.util.Set;

/**
 * Pure-Java policy for the ABI selection behavior of the pinned virtualization Engine.
 *
 * This class does not read packages, install applications, or mutate Clone state.
 */
public final class NativeAbiPolicy {
    public enum HostBitness {
        BIT_32,
        BIT_64,
        UNKNOWN
    }

    public enum Decision {
        ALLOW_PURE_JAVA,
        ALLOW_ARM32,
        ALLOW_ARM64,
        REJECT_SPLIT_APK,
        REJECT_UNSUPPORTED_HOST_ABI,
        REJECT_HOST_BITNESS_MISMATCH,
        REJECT_EXTRACTOR_ABI_MISSING,
        REJECT_UNSUPPORTED_NATIVE_ABI,
        UNKNOWN_HOST_BITNESS,
        UNKNOWN_APK_METADATA
    }

    public static final class Result {
        private final Decision decision;

        private Result(Decision decision) {
            this.decision = decision;
        }

        public Decision getDecision() {
            return decision;
        }

        public String getDiagnosticCode() {
            return "NATIVE_ABI_PREFLIGHT_" + decision.name();
        }

        public boolean isAllowed() {
            return decision == Decision.ALLOW_PURE_JAVA
                    || decision == Decision.ALLOW_ARM32
                    || decision == Decision.ALLOW_ARM64;
        }

        public String getUserMessage(boolean persian) {
            switch (decision) {
                case ALLOW_PURE_JAVA:
                case ALLOW_ARM32:
                case ALLOW_ARM64:
                    return "";
                case REJECT_SPLIT_APK:
                    return persian
                            ? "این برنامه با چند APK (Split APK) نصب شده است. موتور فعلی فقط APK پایه را دریافت می‌کند؛ برای جلوگیری از نصب ناقص، ساخت Clone متوقف شد."
                            : "This app is installed as split APKs. The current Engine receives only the base APK, so cloning was blocked to prevent an incomplete installation.";
                case REJECT_UNSUPPORTED_HOST_ABI:
                    return persian
                            ? "معماری پردازنده این دستگاه با ABIهای پشتیبانی‌شده موتور مجازی‌سازی سازگار نیست."
                            : "The device's primary ABI is not supported by the pinned virtualization Engine.";
                case REJECT_HOST_BITNESS_MISMATCH:
                    return persian
                            ? "نوع پردازش ۳۲/۶۴ بیتی موتور با ABI اصلی انتخاب‌شده برای استخراج کتابخانه‌ها سازگار نیست."
                            : "The Engine process bitness does not match the primary ABI used by the Engine's native-library extractor.";
                case REJECT_EXTRACTOR_ABI_MISSING:
                    return persian
                            ? "APK برنامه کتابخانه‌ای برای مسیر استخراج انتخاب‌شده توسط موتور ندارد؛ نصب متوقف شد تا از Clone ناقص جلوگیری شود."
                            : "The APK has no native library for the ABI paths selected by the current Engine extractor.";
                case REJECT_UNSUPPORTED_NATIVE_ABI:
                    return persian
                            ? "این برنامه فقط کتابخانه‌های Native با معماری پشتیبانی‌نشده دارد."
                            : "This app contains native libraries only for architectures unsupported by the pinned Engine.";
                case UNKNOWN_HOST_BITNESS:
                    return persian
                            ? "نوع پردازش موتور با اطمینان قابل تشخیص نیست؛ نصب امن انجام نشد."
                            : "The Engine process bitness could not be determined safely; installation was blocked.";
                case UNKNOWN_APK_METADATA:
                default:
                    return persian
                            ? "اطلاعات APK برای بررسی سازگاری کامل یا قابل‌خواندن نیست؛ نصب متوقف شد."
                            : "The APK metadata could not be read completely; installation was blocked.";
            }
        }
    }

    private NativeAbiPolicy() { }

    public static HostBitness bitnessForAbi(String abi) {
        if (abi == null) return HostBitness.UNKNOWN;
        String value = abi.trim().toLowerCase(Locale.US);
        if ("arm64-v8a".equals(value) || "x86_64".equals(value)) return HostBitness.BIT_64;
        if ("armeabi-v7a".equals(value) || "armeabi".equals(value) || "x86".equals(value))
            return HostBitness.BIT_32;
        return HostBitness.UNKNOWN;
    }

    /**
     * Evaluate an already-read base APK. splitCount is from PackageManager's
     * ApplicationInfo.splitSourceDirs; any split is rejected because the pinned
     * Engine's package-name installation path passes only sourceDir.
     */
    public static Result evaluate(
            Set<String> nativeAbiDirectories,
            int splitCount,
            HostBitness hostBitness,
            String primaryDeviceAbi,
            boolean baseArchiveReadable) {

        if (splitCount < 0) return new Result(Decision.UNKNOWN_APK_METADATA);
        if (splitCount > 0) return new Result(Decision.REJECT_SPLIT_APK);
        if (!baseArchiveReadable || nativeAbiDirectories == null)
            return new Result(Decision.UNKNOWN_APK_METADATA);

        if (nativeAbiDirectories.isEmpty())
            return new Result(Decision.ALLOW_PURE_JAVA);

        if (hostBitness == null || hostBitness == HostBitness.UNKNOWN)
            return new Result(Decision.UNKNOWN_HOST_BITNESS);

        if (primaryDeviceAbi == null || primaryDeviceAbi.trim().isEmpty())
            return new Result(Decision.UNKNOWN_HOST_BITNESS);

        String primaryAbi = primaryDeviceAbi.trim().toLowerCase(Locale.US);
        if (!"arm64-v8a".equals(primaryAbi)
                && !"armeabi-v7a".equals(primaryAbi)
                && !"armeabi".equals(primaryAbi)) {
            return new Result(Decision.REJECT_UNSUPPORTED_HOST_ABI);
        }

        HostBitness primaryBitness = bitnessForAbi(primaryAbi);
        if (primaryBitness != hostBitness)
            return new Result(Decision.REJECT_HOST_BITNESS_MISMATCH);

        boolean hasArm64 = nativeAbiDirectories.contains("arm64-v8a");
        boolean hasArmV7 = nativeAbiDirectories.contains("armeabi-v7a");
        boolean hasArmeabi = nativeAbiDirectories.contains("armeabi");

        if (HostBitness.BIT_64 == hostBitness) {
            return hasArm64
                    ? new Result(Decision.ALLOW_ARM64)
                    : new Result(Decision.REJECT_HOST_BITNESS_MISMATCH);
        }

        // NativeUtils in the pinned Engine tries Build.CPU_ABI first, then only
        // "armeabi". When the primary ABI is armeabi-v7a, the exact v7a path is
        // selected first; generic armeabi is the only fallback.
        if ("armeabi-v7a".equals(primaryAbi)) {
            if (hasArmV7 || hasArmeabi) return new Result(Decision.ALLOW_ARM32);
            return hasArm64
                    ? new Result(Decision.REJECT_HOST_BITNESS_MISMATCH)
                    : new Result(Decision.REJECT_EXTRACTOR_ABI_MISSING);
        }

        if ("armeabi".equals(primaryAbi)) {
            if (hasArmeabi) return new Result(Decision.ALLOW_ARM32);
            return hasArm64 || hasArmV7
                    ? new Result(Decision.REJECT_EXTRACTOR_ABI_MISSING)
                    : new Result(Decision.REJECT_UNSUPPORTED_NATIVE_ABI);
        }

        return new Result(Decision.REJECT_UNSUPPORTED_NATIVE_ABI);
    }
}
