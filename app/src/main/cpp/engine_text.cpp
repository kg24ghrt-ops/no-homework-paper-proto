#include <jni.h>
#include <vector>
#include <string>
#include <cstring>
#include <algorithm>

// Text shaping engine - Myanmar/Burmese text shaping via HarfBuzz.
// This is a minimal implementation; full HarfBuzz integration will be added in Stage 7.

namespace vcc {
namespace engine {

struct GlyphInfo {
    uint32_t glyphId;
    float xAdvance;
    float yAdvance;
    float xOffset;
    float yOffset;
};

struct ShapedText {
    std::vector<GlyphInfo> glyphs;
    std::vector<uint32_t> clusters;
    float advanceWidth;
    float advanceHeight;
};

// Unicode normalization for Myanmar text
inline bool isMyanmarCodePoint(uint32_t cp) {
    return (cp >= 0x1000 && cp <= 0x109F);
}

inline bool isMyanmarCombiningMark(uint32_t cp) {
    return (cp >= 0x1031 && cp <= 0x103C) ||
           (cp >= 0x103D && cp <= 0x103E) ||
           cp == 0x103F;
}

inline bool isMyanmarKinzi(uint32_t cp) {
    return cp == 0x1004;  // U+1004 MYANMAR LETTER U
}

// Basic shaping: cluster Myanmar characters and compute rough glyph positions
// This is a placeholder; full HarfBuzz shaping will replace this.
inline ShapedText shapeMyanmarText(const std::vector<uint32_t>& codePoints) {
    ShapedText result;
    float xAdvance = 0.0f;

    for (size_t i = 0; i < codePoints.size(); i++) {
        uint32_t cp = codePoints[i];

        GlyphInfo glyph;
        glyph.glyphId = cp;  // Use codepoint as glyph ID for now
        glyph.xAdvance = 0.0f;
        glyph.yAdvance = 0.0f;
        glyph.xOffset = xAdvance;
        glyph.yOffset = 0.0f;

        // Myanmar characters typically have ~16px advance per glyph
        glyph.xAdvance = 16.0f;
        xAdvance += glyph.xAdvance;

        result.glyphs.push_back(glyph);
        result.clusters.push_back(static_cast<uint32_t>(i));
    }

    result.advanceWidth = xAdvance;
    result.advanceHeight = 16.0f;
    return result;
}

inline std::vector<uint32_t> utf8ToCodePoints(const std::string& utf8) {
    std::vector<uint32_t> result;
    size_t i = 0;

    while (i < utf8.size()) {
        uint32_t cp;
        unsigned char c = utf8[i];

        if (c < 0x80) {
            cp = c;
            i += 1;
        } else if (c < 0xE0) {
            cp = ((c & 0x1F) << 6) | (utf8[i + 1] & 0x3F);
            i += 2;
        } else if (c < 0xF0) {
            cp = ((c & 0x0F) << 12) | ((utf8[i + 1] & 0x3F) << 6) | (utf8[i + 2] & 0x3F);
            i += 3;
        } else {
            cp = ((c & 0x07) << 18) | ((utf8[i + 1] & 0x3F) << 12) |
                 ((utf8[i + 2] & 0x3F) << 6) | (utf8[i + 3] & 0x3F);
            i += 4;
        }

        result.push_back(cp);
    }

    return result;
}

}  // namespace engine
}  // namespace vcc