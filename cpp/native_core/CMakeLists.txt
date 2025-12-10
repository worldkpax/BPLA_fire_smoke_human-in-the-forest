cmake_minimum_required(VERSION 3.16)
project(native_core LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(native_core
    native_core.cpp
    native_core.hpp
    bindings.cpp
)

