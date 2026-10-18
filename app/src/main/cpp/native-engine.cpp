#include <jni.h>
#include <string>
#include <vector>
#include <cmath>

// Forward declarations of engine functions
extern "C" {

struct VccPoint {
    float x;
    float y;
};

struct VccRect {
    float left;
    float top;
    float right;
    float bottom;
};

struct VccPageConfig {
    float pageWidth;
    float pageHeight;
    float leftMargin;
    float topMargin;
    float rightMargin;
    float bottomMargin;
    float lineSpacing;
    int lineCount;
    float lineWidth;
    float watermarkAlpha;
};

struct VccColor {
    float r;
    float g;
    float b;
    float a;
};

// Engine lifecycle
extern "C" JNIEXPORT jlong JNICALL
Java_com_example_vcc_engine_VccNativeEngine_createInstance(
        JNIEnv* env,
        jobject /* this */) {
    return reinterpret_cast<jlong>(new int(1));  // Placeholder instance
}

extern "C" JNIEXPORT void JNICALL
Java_com_example_vcc_engine_VccNativeEngine_destroyInstance(
        JNIEnv* env,
        jobject /* this */,
        jlong instance) {
    delete reinterpret_cast<int*>(instance);
}

// Geometry
extern "C" JNIEXPORT jdoubleArray JNICALL
Java_com_example_vcc_engine_VccNativeEngine_computePageMetrics(
        JNIEnv* env,
        jobject /* this */,
        jdouble pageWidth,
        jdouble pageHeight,
        jdouble density) {
    double metrics[4];
    metrics[0] = pageWidth * density;
    metrics[1] = pageHeight * density;
    metrics[2] = pageWidth * density * 0.8;  // content width (10% margins)
    metrics[3] = pageHeight * density * 0.85;  // content height

    jdoubleArray result = env->NewDoubleArray(4);
    env->SetDoubleArrayRegion(result, 0, 4, metrics);
    return result;
}

// Text shaping
extern "C" JNIEXPORT jstring JNICALL
Java_com_example_vcc_engine_VccNativeEngine_shapeText(
        JNIEnv* env,
        jobject /* this */,
        jstring input) {
    const char* raw = env->GetStringUTFChars(input, nullptr);
    std::string result = std::string(raw) + " [shaped]";
    env->ReleaseStringUTFChars(input, raw);
    return env->NewStringUTF(result.c_str());
}

}  // extern "C"