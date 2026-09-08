#include "image-publisher.hpp"


zmq::context_t context{1};
zmq::socket_t publisher{context, zmq::socket_type::pub};
bool initialized = false;

void init_publisher() {
    if (initialized) {
        return;
    }

    publisher.bind("ipc:///tmp/camera.ipc");

    initialized = true;
}

void send_image(cv::Mat& frame) {

    if (!initialized || frame.empty()) {
        return;
    }

    std::vector<uchar> jpg;
    
    cv::imencode(
            ".jpg",
            frame,
            jpg,
            {cv::IMWRITE_JPEG_QUALITY, 80}
        );
        
    zmq::message_t message(jpg.data(), jpg.size());
    publisher.send(message, zmq::send_flags::dontwait);
}


void close_publisher() {
    if (initialized) {
        publisher.close();
        context.close();
        initialized = false;
    }
}
