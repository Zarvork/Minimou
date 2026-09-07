
cmake_minimum_required(VERSION 3.14)

# set the project name
project(EPITA_CODEFEST_WEEK)

set(CMAKE_CXX_STANDARD 20)

set(CMAKE_EXPORT_COMPILE_COMMANDS TRUE)

# find_package(libfreenect REQUIRED)
find_package(libfreenect REQUIRED)
add_library(libfreenect::libfreenect INTERFACE IMPORTED)
target_include_directories(libfreenect::libfreenect INTERFACE ${FREENECT_INCLUDE_DIRS})
target_link_directories(libfreenect::libfreenect INTERFACE ${FREENECT_LIBRARY_DIRS})
target_link_libraries(libfreenect::libfreenect INTERFACE ${FREENECT_LIBRARIES})

find_package(GLUT REQUIRED)
find_package(OpenGL REQUIRED)
find_package(OpenCV REQUIRED COMPONENTS core highgui imgproc calib3d imgcodecs)
find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets)


# Pseudo target to OpenNI
#add_library(OpenNI INTERFACE)
#target_include_directories(OpenNI INTERFACE thirdparty/OpenNI/Include)
#target_link_libraries(OpenNI INTERFACE ${CMAKE_SOURCE_DIR}/thirdparty/OpenNI/Redist/libOpenNI2.so)


# add the executable
add_executable(glview src/glview.c)
# target_link_libraries(glview PRIVATE libfreenect::libfreenect GLUT::GLUT OpenGL::GL)
target_link_libraries(glview PRIVATE libfreenect::libfreenect GLUT::GLUT OpenGL::GL OpenGL::GLU m)

add_executable(test-cv src/test-cv.cpp)

add_library(opencv_kinect src/capture-cv.hpp src/capture-cv.cpp src/utils.cpp src/calibration-utils.hpp src/calibration-utils.cpp)
target_link_libraries(opencv_kinect PRIVATE opencv_imgproc opencv_calib3d libfreenect::libfreenect Qt6::Core)
target_link_libraries(opencv_kinect PUBLIC opencv_core opencv_imgcodecs)

target_link_libraries(test-cv PRIVATE opencv_highgui opencv_kinect)

add_executable(calibration src/calibrate-qt.cpp src/calibrate-qt-main.cpp)
target_link_libraries(calibration PRIVATE Qt6::Gui Qt6::Widgets opencv_kinect)
