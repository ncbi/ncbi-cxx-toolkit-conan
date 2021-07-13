cmake_minimum_required(VERSION 3.1)
project(PackageTest CXX)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

add_executable(basic_sample basic_sample.cpp)
target_link_libraries(basic_sample ${CONAN_LIBS})
