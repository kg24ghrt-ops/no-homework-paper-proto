#include <jni.h>
#include <vector>
#include <string>
#include <cstring>

// Rendering engine - manages draw commands and rendering state.
// This is a minimal implementation; full Skia integration will replace this.

namespace vcc {
namespace engine {

struct DrawCommand {
    enum Type {
        FILL_RECT,
        DRAW_LINE,
        DRAW_TEXT,
        DRAW_IMAGE,
        SET_COLOR,
        CLIP_RECT
    };

    Type type;
    float x1, y1, x2, y2;
    float r, g, b, a;
    float lineWidth;
};

class RenderState {
public:
    std::vector<DrawCommand> commands;
    float currentColor[4] = {0.0f, 0.0f, 0.0f, 1.0f};

    void reset() {
        commands.clear();
    }

    void beginFrame() {
        commands.clear();
    }

    void endFrame() {
        // Flush commands to GPU (placeholder)
    }

    void drawRect(float x, float y, float w, float h,
                  float r, float g, float b, float a) {
        DrawCommand cmd;
        cmd.type = DrawCommand::FILL_RECT;
        cmd.x1 = x;
        cmd.y1 = y;
        cmd.x2 = w;
        cmd.y2 = h;
        cmd.r = r;
        cmd.g = g;
        cmd.b = b;
        cmd.a = a;
        commands.push_back(cmd);
    }

    void drawLine(float x1, float y1, float x2, float y2,
                  float r, float g, float b, float a, float width) {
        DrawCommand cmd;
        cmd.type = DrawCommand::DRAW_LINE;
        cmd.x1 = x1;
        cmd.y1 = y1;
        cmd.x2 = x2;
        cmd.y2 = y2;
        cmd.r = r;
        cmd.g = g;
        cmd.b = b;
        cmd.a = a;
        cmd.lineWidth = width;
        commands.push_back(cmd);
    }

    size_t commandCount() const {
        return commands.size();
    }
};

}  // namespace engine
}  // namespace vcc