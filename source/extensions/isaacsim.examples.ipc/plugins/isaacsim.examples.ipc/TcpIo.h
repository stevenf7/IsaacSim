// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#pragma once

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/types.h>

#include <cerrno>
#include <cstdint>
#include <cstring>
#include <fcntl.h>
#include <string>
#include <unistd.h>

namespace isaacsim
{
namespace examples
{
namespace ipc
{
namespace tcp
{

inline void writeLe64(uint8_t* out, int64_t value)
{
    for (int i = 0; i < 8; ++i)
    {
        out[i] = static_cast<uint8_t>((static_cast<uint64_t>(value) >> (8 * i)) & 0xFFu);
    }
}

inline int64_t readLe64(const uint8_t* data)
{
    uint64_t v = 0;
    for (int i = 0; i < 8; ++i)
    {
        v |= static_cast<uint64_t>(data[i]) << (8 * i);
    }
    return static_cast<int64_t>(v);
}

inline void writeLe32(uint8_t* out, uint32_t value)
{
    for (int i = 0; i < 4; ++i)
    {
        out[i] = static_cast<uint8_t>((value >> (8 * i)) & 0xFFu);
    }
}

inline uint32_t readLe32(const uint8_t* data)
{
    uint32_t v = 0;
    for (int i = 0; i < 4; ++i)
    {
        v |= static_cast<uint32_t>(data[i]) << (8 * i);
    }
    return v;
}

inline bool parseHostPort(const std::string& uri, std::string& outHost, uint16_t& outPort)
{
    const size_t colon = uri.rfind(':');
    if (colon == std::string::npos || colon == 0 || colon + 1 >= uri.size())
    {
        return false;
    }
    outHost = uri.substr(0, colon);
    try
    {
        const unsigned long p = std::stoul(uri.substr(colon + 1));
        if (p > 65535u)
        {
            return false;
        }
        outPort = static_cast<uint16_t>(p);
    }
    catch (...)
    {
        return false;
    }
    return true;
}

inline bool setNonBlocking(int fd)
{
    const int flags = fcntl(fd, F_GETFL, 0);
    if (flags < 0)
    {
        return false;
    }
    return fcntl(fd, F_SETFL, flags | O_NONBLOCK) == 0;
}

inline void closeSocket(int fd)
{
    if (fd >= 0)
    {
        ::close(fd);
    }
}

inline void closeFd(int& fd)
{
    if (fd >= 0)
    {
        ::close(fd);
        fd = -1;
    }
}

inline bool sendAll(int fd, const void* data, size_t length)
{
    const char* bytes = static_cast<const char*>(data);
    size_t sent = 0;
    while (sent < length)
    {
        const ssize_t n = ::send(fd, bytes + sent, length - sent, MSG_NOSIGNAL);
        if (n < 0)
        {
            if (errno == EINTR)
            {
                continue;
            }
            return false;
        }
        if (n == 0)
        {
            return false;
        }
        sent += static_cast<size_t>(n);
    }
    return true;
}

inline int connectTcpClient(const std::string& host, uint16_t port)
{
    const int fd = ::socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0)
    {
        return -1;
    }

    sockaddr_in addr;
    std::memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    if (inet_pton(AF_INET, host.c_str(), &addr.sin_addr) != 1)
    {
        closeSocket(fd);
        return -1;
    }

    if (::connect(fd, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) != 0)
    {
        closeSocket(fd);
        return -1;
    }
    return fd;
}

inline int listenTcpServer(const std::string& bindHost, uint16_t port)
{
    const int fd = ::socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0)
    {
        return -1;
    }

    int one = 1;
    if (setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one)) != 0)
    {
        closeSocket(fd);
        return -1;
    }

    sockaddr_in addr;
    std::memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    if (inet_pton(AF_INET, bindHost.c_str(), &addr.sin_addr) != 1)
    {
        closeSocket(fd);
        return -1;
    }

    if (::bind(fd, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) != 0)
    {
        closeSocket(fd);
        return -1;
    }

    if (::listen(fd, 1) != 0)
    {
        closeSocket(fd);
        return -1;
    }

    if (!setNonBlocking(fd))
    {
        closeSocket(fd);
        return -1;
    }

    return fd;
}

} // namespace tcp
} // namespace ipc
} // namespace examples
} // namespace isaacsim
