cmake_minimum_required(VERSION 3.16)
project(PackageTest)
set(PackageName ncbi-cxx-toolkit-public)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup(TARGETS)
find_package(${PackageName} REQUIRED)

add_executable(basic_sample basic_sample.cpp)
target_link_libraries(basic_sample ${PackageName}::${PackageName})
