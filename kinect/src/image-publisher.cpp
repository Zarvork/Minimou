#include "image-publisher.hpp"

zmq::context_t context{1};
zmq::socket_t rgb_publisher{context, zmq::socket_type::pub};
zmq::socket_t depth_publisher{context, zmq::socket_type::pub};
bool initialized = false;

void init_publisher() {
    if (initialized) {
        return;
    }

    rgb_publisher.bind("ipc:///tmp/camera_rgb.ipc");
    depth_publisher.bind("ipc:///tmp/camera_depth.ipc");

    initialized = true;
}

void send_rgb_image(cv::Mat& frame) {
    if (!initialized || frame.empty()) {
        return;
    }

    std::vector<uchar> jpg;
    cv::Mat bgr_frame;

    cv::cvtColor(frame, bgr_frame, cv::COLOR_RGB2BGR);

    cv::imencode(
        ".jpg",
        bgr_frame,
        jpg,
        {cv::IMWRITE_JPEG_QUALITY, 80}
    );

    zmq::message_t message(jpg.data(), jpg.size());
    rgb_publisher.send(message, zmq::send_flags::dontwait);
}

void send_depth_image(cv::Mat& frame) {
    if (!initialized || frame.empty()) {
        return;
    }

    if (frame.type() != CV_16UC1) {
        std::cerr << "send_depth_image: format inattendu, CV_16UC1 attendu"
                  << std::endl;
        return;
    }

    std::vector<uchar> png;
    cv::imencode(".png", frame, png);

    zmq::message_t message(png.data(), png.size());
    depth_publisher.send(message, zmq::send_flags::dontwait);
}

void close_publisher() {
    if (initialized) {
        rgb_publisher.close();
        depth_publisher.close();
        context.close();
        initialized = false;
    }
}