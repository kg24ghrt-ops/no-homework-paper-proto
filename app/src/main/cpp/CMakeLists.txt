cmake_minimum_required(VERSION 3.22.1)

project("vcc-engine")

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Minimal Skia stub for the initial build phase.
# The full Skia integration will be added in Stage 6.
add_library(
    vcc-engine
    SHARED
    native-engine.cpp
    engine_geometry.cpp
    engine_render.cpp
    engine_text.cpp
)

find_library(
    log-lib
    log
)

target_compile_features(vcc-engine PRIVATE cxx_std_17)

target_include_directories(vcc-engine PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(
    vcc-engine
    ${log-lib}
    android
)