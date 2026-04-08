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

#include "TcpIo.h"

#include <cerrno>
#include <cstdint>
#include <cstring>
#include <optional>
#include <string>

namespace isaacsim
{
namespace examples
{
namespace ipc
{

class TcpStepServer
{
public:
    explicit TcpStepServer(std::string uri) : m_uri(std::move(uri)), m_listenFd(-1), m_clientFd(-1), m_filled(0)
    {
        std::memset(m_buffer, 0, sizeof(m_buffer));
    }

    ~TcpStepServer()
    {
        disconnect();
    }

    bool connect()
    {
        disconnect();
        std::string host;
        uint16_t port = 0;
        if (!tcp::parseHostPort(m_uri, host, port))
        {
            return false;
        }
        m_listenFd = tcp::listenTcpServer(host, port);
        return m_listenFd >= 0;
    }

    void disconnect()
    {
        tcp::closeFd(m_clientFd);
        tcp::closeFd(m_listenFd);
        m_filled = 0;
    }

    bool isConnected() const
    {
        return m_listenFd >= 0;
    }

    std::optional<uint32_t> tryReceiveStep()
    {
        if (m_listenFd < 0)
        {
            return std::nullopt;
        }

        if (m_clientFd < 0)
        {
            const int c = ::accept(m_listenFd, nullptr, nullptr);
            if (c < 0)
            {
                if (errno == EAGAIN || errno == EWOULDBLOCK || errno == EINTR)
                {
                    return std::nullopt;
                }
                return std::nullopt;
            }
            if (!tcp::setNonBlocking(c))
            {
                tcp::closeSocket(c);
                return std::nullopt;
            }
            m_clientFd = c;
            m_filled = 0;
        }

        while (m_filled < 4)
        {
            const ssize_t n = ::recv(m_clientFd, m_buffer + m_filled, 4 - m_filled, 0);
            if (n > 0)
            {
                m_filled += static_cast<size_t>(n);
                continue;
            }
            if (n == 0)
            {
                tcp::closeFd(m_clientFd);
                m_filled = 0;
                return std::nullopt;
            }
            if (errno == EINTR)
            {
                continue;
            }
            if (errno == EAGAIN || errno == EWOULDBLOCK)
            {
                return std::nullopt;
            }
            tcp::closeFd(m_clientFd);
            m_filled = 0;
            return std::nullopt;
        }

        const uint32_t step = tcp::readLe32(m_buffer);
        m_filled = 0;
        return step;
    }

    const std::string& getUri() const
    {
        return m_uri;
    }

private:
    std::string m_uri;
    int m_listenFd;
    int m_clientFd;
    uint8_t m_buffer[4];
    size_t m_filled;
};

} // namespace ipc
} // namespace examples
} // namespace isaacsim
