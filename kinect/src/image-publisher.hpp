#pragma once


#include <zmq.hpp>
#include <opencv2/opencv.hpp>
#include <iostream>
#include <vector>

void init_publisher();
void send_rgb_image(cv::Mat& frame);
void send_depth_image(cv::Mat& frame);
void close_publisher();