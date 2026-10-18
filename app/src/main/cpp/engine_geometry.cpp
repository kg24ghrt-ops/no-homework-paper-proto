#include <jni.h>
#include <cmath>
#include <vector>
#include <algorithm>

// Geometry engine - platform-independent math for page layout and rendering.
// All functions operate on double precision for deterministic cross-platform results.

namespace vcc {
namespace engine {

struct Point {
    double x;
    double y;
};

struct Rect {
    double left;
    double top;
    double right;
    double bottom;
};

struct PageConfig {
    double pageWidth;    // B5 width in mm
    double pageHeight;   // B5 height in mm
    double leftMargin;
    double topMargin;
    double rightMargin;
    double bottomMargin;
    double lineSpacing;
    int lineCount;
    double lineWidth;
    double watermarkAlpha;
};

// B5 paper dimensions in mm
constexpr double B5_WIDTH_MM = 176.0;
constexpr double B5_HEIGHT_MM = 250.0;

// Default margins in mm
constexpr double DEFAULT_MARGIN_MM = 20.0;

// Default line spacing
constexpr double DEFAULT_LINE_SPACING_MM = 8.0;

// Default line width (ruled line)
constexpr double DEFAULT_LINE_WIDTH_PX = 1.0;

inline Rect computeContentRect(const PageConfig& config) {
    return Rect{
        config.leftMargin,
        config.topMargin,
        config.pageWidth - config.rightMargin,
        config.pageHeight - config.bottomMargin
    };
}

inline int computeLineCount(const PageConfig& config) {
    const Rect content = computeContentRect(config);
    const double availableHeight = content.bottom - content.top;
    return std::max(1, static_cast<int>(availableHeight / config.lineSpacing));
}

inline double computeLineY(const PageConfig& config, int lineIndex) {
    return config.topMargin + (lineIndex + 0.5) * config.lineSpacing;
}

inline double mmToPx(double mm, double densityDPI) {
    return mm * densityDPI / 25.4;
}

inline double pxToMM(double px, double densityDPI) {
    return px * 25.4 / densityDPI;
}

inline bool rectContains(const Rect& r, const Point& p) {
    return p.x >= r.left && p.x <= r.right && p.y >= r.top && p.y <= r.bottom;
}

inline double clamp(double value, double min, double max) {
    return std::max(min, std::min(max, value));
}

}  // namespace engine
}  // namespace vcc