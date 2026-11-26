#include <jni.h>
#include <errno.h>
#include <sys/auxv.h>

#if defined(__arm__) && !defined(__aarch64__)
#ifndef HWCAP_NEON
#define HWCAP_NEON (1UL << 12)
#endif
#endif

extern "C" JNIEXPORT jint JNICALL
Java_com_veyravault_space_core_NativeNeonProbe_nativeProbe(JNIEnv *, jclass) {
#if defined(__aarch64__)
    // Advanced SIMD/NEON is mandatory for Android's arm64-v8a ABI.
    return 1;
#elif defined(__arm__)
    // A missing/empty auxiliary-vector value is unknown, not proof of no NEON.
    errno = 0;
    const unsigned long hwcap = getauxval(AT_HWCAP);
    if (errno == ENOENT || hwcap == 0) return -1;
    return (hwcap & HWCAP_NEON) != 0 ? 1 : 0;
#else
    return -1;
#endif
}
