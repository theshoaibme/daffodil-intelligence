cmake_minimum_required(VERSION 3.14)
project(core LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)

# We use libdatachannel as it is a lightweight WebRTC implementation
FetchContent_Declare(
  datachannel
  GIT_REPOSITORY https://github.com/paullouisageneau/libdatachannel.git
  GIT_TAG        v0.21.0
)

# Configure libdatachannel options
set(NO_WEBSOCKETS OFF CACHE BOOL "" FORCE)
set(NO_MEDIA OFF CACHE BOOL "" FORCE)

FetchContent_MakeAvailable(datachannel)

add_executable(core_app src/main.cpp)
target_link_libraries(core_app PRIVATE datachannel)
