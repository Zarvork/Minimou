cmake_minimum_required(VERSION 3.14)

project(EPITA_CODEFEST_WEEK LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS TRUE)

find_package(PkgConfig REQUIRED)

pkg_check_modules(FREENECT REQUIRED IMPORTED_TARGET libfreenect)
pkg_check_modules(ZMQ REQUIRED IMPORTED_TARGET libzmq)

add_library(libfreenect::libfreenect ALIAS PkgConfig::FREENECT)

find_package(GLUT REQUIRED)
find_package(OpenGL REQUIRED)
find_package(OpenCV REQUIRED COMPONENTS
  core
  highgui
  imgproc
  calib3d
  imgcodecs
)
find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets)

add_executable(glview src/glview.c)

target_link_libraries(glview
  PRIVATE
    libfreenect::libfreenect
    GLUT::GLUT
    OpenGL::GL
    OpenGL::GLU
    m
)

add_executable(test-cv
  src/test-cv.cpp
  src/image-publisher.cpp
)

add_library(opencv_kinect
  src/capture-cv.hpp
  src/capture-cv.cpp
  src/utils.cpp
  src/calibration-utils.hpp
  src/calibration-utils.cpp
)

target_link_libraries(opencv_kinect
  PRIVATE
    opencv_imgproc
    opencv_calib3d
    libfreenect::libfreenect
    Qt6::Core
  PUBLIC
    opencv_core
    opencv_imgcodecs
)

target_link_libraries(test-cv
  PRIVATE
    opencv_highgui
    opencv_kinect
    PkgConfig::ZMQ
)

add_executable(calibration
  src/calibrate-qt.cpp
  src/calibrate-qt-main.cpp
)

target_link_libraries(calibration
  PRIVATE
    Qt6::Gui
    Qt6::Widgets
    opencv_kinect
)
