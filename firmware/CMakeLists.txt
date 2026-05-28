cmake_minimum_required(VERSION 3.22)
project(agentprobe_firmware C)

add_library(agentprobe_firmware INTERFACE)
target_include_directories(agentprobe_firmware INTERFACE include)
