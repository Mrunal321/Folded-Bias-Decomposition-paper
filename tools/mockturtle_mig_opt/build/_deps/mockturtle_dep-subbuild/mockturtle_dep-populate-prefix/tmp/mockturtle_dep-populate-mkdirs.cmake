# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/home/mrunal/Folded_Bias-Decomposition/tools/mockturtle_mig_opt/build/_deps/mockturtle_dep-src"
  "/home/mrunal/Folded_Bias-Decomposition/tools/mockturtle_mig_opt/build/_deps/mockturtle_dep-build"
  "/home/mrunal/Folded_Bias-Decomposition/tools/mockturtle_mig_opt/build/_deps/mockturtle_dep-subbuild/mockturtle_dep-populate-prefix"
  "/home/mrunal/Folded_Bias-Decomposition/tools/mockturtle_mig_opt/build/_deps/mockturtle_dep-subbuild/mockturtle_dep-populate-prefix/tmp"
  "/home/mrunal/Folded_Bias-Decomposition/tools/mockturtle_mig_opt/build/_deps/mockturtle_dep-subbuild/mockturtle_dep-populate-prefix/src/mockturtle_dep-populate-stamp"
  "/home/mrunal/Folded_Bias-Decomposition/tools/mockturtle_mig_opt/build/_deps/mockturtle_dep-subbuild/mockturtle_dep-populate-prefix/src"
  "/home/mrunal/Folded_Bias-Decomposition/tools/mockturtle_mig_opt/build/_deps/mockturtle_dep-subbuild/mockturtle_dep-populate-prefix/src/mockturtle_dep-populate-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/mrunal/Folded_Bias-Decomposition/tools/mockturtle_mig_opt/build/_deps/mockturtle_dep-subbuild/mockturtle_dep-populate-prefix/src/mockturtle_dep-populate-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/mrunal/Folded_Bias-Decomposition/tools/mockturtle_mig_opt/build/_deps/mockturtle_dep-subbuild/mockturtle_dep-populate-prefix/src/mockturtle_dep-populate-stamp${cfgdir}") # cfgdir has leading slash
endif()
