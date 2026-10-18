#include <gtest/gtest.h>
#include <cmath>
#include <vector>
#include <string>

// Include the geometry engine for host-side testing
#include "../main/cpp/engine_geometry.cpp"

using namespace vcc::engine;

// B5 paper dimensions
constexpr double B5_WIDTH = 176.0;
constexpr double B5_HEIGHT = 250.0;

// Test: B5 paper dimensions are correct
TEST(GeometryTest, B5PaperDimensions) {
    EXPECT_DOUBLE_EQ(176.0, B5_WIDTH_MM);
    EXPECT_DOUBLE_EQ(250.0, B5_HEIGHT_MM);
}

// Test: Content rect computation
TEST(GeometryTest, ContentRect) {
    PageConfig config;
    config.pageWidth = B5_WIDTH;
    config.pageHeight = B5_HEIGHT;
    config.leftMargin = 20.0;
    config.topMargin = 20.0;
    config.rightMargin = 20.0;
    config.bottomMargin = 20.0;

    Rect content = computeContentRect(config);
    EXPECT_DOUBLE_EQ(20.0, content.left);
    EXPECT_DOUBLE_EQ(20.0, content.top);
    EXPECT_DOUBLE_EQ(156.0, content.right);  // 176 - 20
    EXPECT_DOUBLE_EQ(230.0, content.bottom); // 250 - 20
}

// Test: Line count computation
TEST(GeometryTest, LineCount) {
    PageConfig config;
    config.pageWidth = B5_WIDTH;
    config.pageHeight = B5_HEIGHT;
    config.topMargin = 20.0;
    config.bottomMargin = 20.0;
    config.lineSpacing = 8.0;

    int lineCount = computeLineCount(config);
    // Content height = 250 - 20 - 20 = 210
    // Lines = 210 / 8 = 26.25 -> 26
    EXPECT_EQ(26, lineCount);
}

// Test: Line count with explicit value
TEST(GeometryTest, LineCountExplicit) {
    PageConfig config;
    config.lineCount = 10;
    EXPECT_EQ(10, computeLineCount(config));
}

// Test: Line count minimum is 1
TEST(GeometryTest, LineCountMinimum) {
    PageConfig config;
    config.pageWidth = 100.0;
    config.pageHeight = 100.0;
    config.topMargin = 45.0;
    config.bottomMargin = 45.0;
    config.lineSpacing = 100.0;  // Only 10px available, spacing 100 -> 0 lines

    int lineCount = computeLineCount(config);
    EXPECT_EQ(1, lineCount);  // Minimum is 1
}

// Test: mmToPx conversion
TEST(GeometryTest, MmToPx) {
    double px = mmToPx(25.4, 96.0);
    EXPECT_DOUBLE_EQ(96.0, px);
}

// Test: pxToMm conversion
TEST(GeometryTest, PxToMm) {
    double mm = pxToMM(96.0, 96.0);
    EXPECT_DOUBLE_EQ(25.4, mm);
}

// Test: Rect containment
TEST(GeometryTest, RectContains) {
    Rect rect = {10.0, 10.0, 100.0, 100.0};
    EXPECT_TRUE(rectContains(rect, {50.0, 50.0}));
    EXPECT_TRUE(rectContains(rect, {10.0, 10.0}));
    EXPECT_TRUE(rectContains(rect, {100.0, 100.0}));
    EXPECT_FALSE(rectContains(rect, {5.0, 50.0}));
    EXPECT_FALSE(rectContains(rect, {105.0, 50.0}));
}

// Test: Clamp function
TEST(GeometryTest, Clamp) {
    EXPECT_DOUBLE_EQ(5.0, clamp(5.0, 0.0, 10.0));
    EXPECT_DOUBLE_EQ(0.0, clamp(-5.0, 0.0, 10.0));
    EXPECT_DOUBLE_EQ(10.0, clamp(15.0, 0.0, 10.0));
}

// Test: Line Y position
TEST(GeometryTest, LineYPosition) {
    PageConfig config;
    config.topMargin = 20.0;
    config.lineSpacing = 8.0;

    double y0 = computeLineY(config, 0);
    EXPECT_DOUBLE_EQ(24.0, y0);  // 20 + 0.5 * 8

    double y1 = computeLineY(config, 1);
    EXPECT_DOUBLE_EQ(32.0, y1);  // 20 + 1.5 * 8
}

// Test: Invalid dimensions
TEST(GeometryTest, InvalidDimensions) {
    PageConfig config;
    config.pageWidth = 0.0;
    config.pageHeight = 100.0;
    config.topMargin = 10.0;
    config.bottomMargin = 10.0;
    config.lineSpacing = 8.0;

    // With zero page width, content rect should still compute
    Rect content = computeContentRect(config);
    EXPECT_DOUBLE_EQ(0.0, content.right);
}

// Test: Large document handling
TEST(GeometryTest, LargeDocument) {
    PageConfig config;
    config.pageWidth = B5_WIDTH;
    config.pageHeight = B5_HEIGHT;
    config.topMargin = 20.0;
    config.bottomMargin = 20.0;
    config.lineSpacing = 1.0;  // Very tight spacing

    int lineCount = computeLineCount(config);
    // 210 / 1 = 210 lines
    EXPECT_EQ(210, lineCount);
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}