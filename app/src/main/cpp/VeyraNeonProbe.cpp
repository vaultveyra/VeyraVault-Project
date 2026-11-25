#include <jni.h>

#if defined(__arm__) && !defined(__aarch64__)
#include "cpuinfo_arm.h"
#endif

extern "C" JNIEXPORT jint JNICALL
Java_com_veyravault_space_core_NativeNeonProbe_nativeProbe(JNIEnv *, jclass) {
#if defined(__aarch64__)
    // Advanced SIMD/NEON is mandatory in the Android arm64 ABI.
    return 1;
#elif defined(__arm__)
    const cpu_features::ArmInfo info = cpu_features::GetArmInfo();
    bool hasEvidence = info.architecture > 0
            || info.implementer > 0
            || info.variant > 0
            || info.part > 0
            || info.revision > 0;
    for (int feature = 0; feature < cpu_features::ARM_LAST_; ++feature) {
        if (cpu_features::GetArmFeaturesEnumValue(
                &info.features, static_cast<cpu_features::ArmFeaturesEnum>(feature)) != 0) {
            hasEvidence = true;
            break;
        }
    }
    if (!hasEvidence) return -1;
    return info.features.neon ? 1 : 0;
#else
    return -1;
#endif
}
