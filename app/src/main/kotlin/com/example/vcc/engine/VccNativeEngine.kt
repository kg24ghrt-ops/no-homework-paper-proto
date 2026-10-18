package com.example.vcc.engine

/**
 * JNI bindings to the native C++ rendering engine.
 *
 * All native methods are declared here and implemented in:
 * - app/src/main/cpp/native-engine.cpp
 * - app/src/main/cpp/engine_geometry.cpp
 * - app/src/main/cpp/engine_render.cpp
 * - app/src/main/cpp/engine_text.cpp
 */
class VccNativeEngine {

    companion object {
        init {
            System.loadLibrary("vcc-engine")
        }
    }

    /**
     * Creates a new engine instance.
     * @return Native pointer handle (0 if creation failed).
     */
    external fun createInstance(): Long

    /**
     * Destroys an engine instance and releases all native resources.
     * @param instance Native pointer handle from createInstance().
     */
    external fun destroyInstance(instance: Long)

    /**
     * Computes page metrics in pixels for a given paper size and density.
     *
     * @param pageWidth Paper width in mm (e.g., 176.0 for B5).
     * @param pageHeight Paper height in mm (e.g., 250.0 for B5).
     * @param density Screen density in DPI.
     * @return Array of [pageWidthPx, pageHeightPx, contentWidthPx, contentHeightPx].
     */
    external fun computePageMetrics(
        pageWidth: Double,
        pageHeight: Double,
        density: Double
    ): DoubleArray

    /**
     * Shapes text using the native HarfBuzz-based shaper.
     *
     * @param input Raw UTF-8 text to shape.
     * @return Shaped text result as a JSON-like string.
     */
    external fun shapeText(input: String): String

    /**
     * Renders a page to the current graphics context.
     *
     * @param instance Native engine instance.
     * @param pageIndex Zero-based page index.
     * @param width Page width in pixels.
     * @param height Page height in pixels.
     */
    external fun renderPage(
        instance: Long,
        pageIndex: Int,
        width: Float,
        height: Float
    ): Boolean

    /**
     * Returns the number of draw commands generated for the last render.
     */
    external fun getDrawCommandCount(instance: Long): Int

    /**
     * Checks if GPU rendering is available on this device.
     */
    external fun isGpuAvailable(): Boolean

    /**
     * Gets the current rendering backend name.
     */
    external fun getBackendName(): String
}