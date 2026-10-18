cmake_minimum_required(VERSION 3.22.1)

project("vcc-engine-tests")

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Find GTest
find_package(GTest REQUIRED)

# Include engine source for testing
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../main/cpp)

add_executable(
    vcc-engine-tests
    engine_geometry_test.cpp
)

target_compile_features(vcc-engine-tests PRIVATE cxx_std_17)

target_include_directories(vcc-engine-tests PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/../main/cpp
    ${GTEST_INCLUDE_DIRS}
)

target_link_libraries(
    vcc-engine-tests
    GTest::GTest
    GTest::Main
    pthread
)