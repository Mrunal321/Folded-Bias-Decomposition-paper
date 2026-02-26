cmake_minimum_required(VERSION 3.20)
project(mockturtle_mig_opt LANGUAGES CXX)

include(FetchContent)

# Keep dependency build lean.
set(MOCKTURTLE_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(MOCKTURTLE_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(MOCKTURTLE_BUILD_EXPERIMENTS OFF CACHE BOOL "" FORCE)
set(MOCKTURTLE_ENABLE_ABC OFF CACHE BOOL "" FORCE)
set(BILL_Z3 OFF CACHE BOOL "" FORCE)

FetchContent_Declare(
  mockturtle_dep
  GIT_REPOSITORY https://github.com/lsils/mockturtle.git
  GIT_TAG master
  GIT_SHALLOW TRUE
)

FetchContent_MakeAvailable(mockturtle_dep)

add_executable(mockturtle_mig_opt src/mockturtle_mig_opt.cpp)
target_link_libraries(mockturtle_mig_opt PRIVATE mockturtle)
target_compile_features(mockturtle_mig_opt PRIVATE cxx_std_17)

