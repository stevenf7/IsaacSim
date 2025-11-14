// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

#include "isaacsim/ucx/core/UcxListener.h"

#include <carb/logging/Log.h>

#include <netinet/in.h>

#include <algorithm>
#include <cassert>
#include <chrono>
#include <stdexcept>
#include <thread>

namespace isaacsim::ucx::core
{
UCXListener::UCXListener(std::shared_ptr<ucxx::Context> context, uint16_t port)
    : m_context(context), m_port(port), m_shutdown(false)
{
    if (!m_context)
    {
        throw std::runtime_error("UCXListener: context cannot be null");
    }

    initialize();
}

UCXListener::~UCXListener()
{
    try
    {
        shutdown();
    }
    catch (const std::exception& e)
    {
        CARB_LOG_ERROR("Error during UCXListener destruction: %s", e.what());
    }
}

bool UCXListener::waitForConnection(int timeout_ms)
{
    if (timeout_ms < -1)
    {
        throw std::invalid_argument("UCXListener::waitForConnection: timeout_ms must be >= -1");
    }

    if (m_shutdown.load())
    {
        return false;
    }

    {
        std::unique_lock<std::mutex> lock(m_endpoint_mutex);
        if (m_endpoint)
        {
            return true;
        }
        if (timeout_ms == -1)
        {
            m_connection_condition.wait(lock, [this]() { return m_endpoint != nullptr || m_shutdown.load(); });
        }
        else
        {
            m_connection_condition.wait_for(lock, std::chrono::milliseconds(timeout_ms),
                                            [this]() { return m_endpoint != nullptr || m_shutdown.load(); });
        }
    }

    return isConnected();
}

bool UCXListener::isConnected() const
{
    std::lock_guard<std::mutex> lock(m_endpoint_mutex);
    return m_endpoint != nullptr;
}

void UCXListener::startProgressThread()
{
    if (m_worker && !m_worker->isProgressThreadRunning())
    {
        m_worker->startProgressThread();
        CARB_LOG_INFO("Started progress thread for listener on port %u", m_port);
    }
}

void UCXListener::stopProgressThread()
{
    if (m_worker && m_worker->isProgressThreadRunning())
    {
        m_worker->stopProgressThread();
        CARB_LOG_INFO("Stopped progress thread for listener on port %u", m_port);
    }
}

void UCXListener::shutdown()
{
    // Check if already shut down to prevent multiple shutdowns
    bool expected = false;
    if (!m_shutdown.compare_exchange_strong(expected, true))
    {
        // Already shutting down or shut down
        return;
    }

    // Wake up any threads waiting for connection
    m_connection_condition.notify_all();

    // Stop the progress thread FIRST, before destroying any resources
    // This prevents the thread from accessing resources during destruction
    if (m_worker && m_worker->isProgressThreadRunning())
    {
        try
        {
            m_worker->stopProgressThread();
        }
        catch (const std::exception& e)
        {
            CARB_LOG_ERROR("Error stopping progress thread: %s", e.what());
        }
    }

    // Now that progress thread is stopped, cancel any inflight requests
    if (m_worker)
    {
        try
        {
            m_worker->cancelInflightRequests();
        }
        catch (const std::exception& e)
        {
            CARB_LOG_ERROR("Error canceling inflight requests: %s", e.what());
        }
    }

    // Clean up resources in safe order
    {
        std::lock_guard<std::mutex> lock(m_endpoint_mutex);
        if (m_endpoint)
        {
            m_endpoint.reset();
        }
    }

    if (m_listener)
    {
        m_listener.reset();
    }

    if (m_worker)
    {
        m_worker.reset();
    }
}

std::shared_ptr<ucxx::Request> UCXListener::tagSend(const void* buffer, size_t length, uint64_t tag)
{
    if (m_shutdown.load())
    {
        throw std::runtime_error("Listener is shutting down or shut down");
    }
    std::lock_guard<std::mutex> lock(m_endpoint_mutex);
    if (!m_endpoint)
    {
        throw std::runtime_error("No client connected");
    }
    // Note: ucxx::Endpoint::tagSend expects non-const void* - data won't be modified
    return m_endpoint->tagSend(const_cast<void*>(buffer), length, ucxx::Tag{ tag });
}

std::shared_ptr<ucxx::Request> UCXListener::tagMultiSend(const std::vector<const void*>& buffer,
                                                         const std::vector<size_t>& size,
                                                         const std::vector<int>& isCuda,
                                                         const uint64_t tag)
{
    if (m_shutdown.load())
    {
        throw std::runtime_error("Listener is shutting down or shut down");
    }
    std::lock_guard<std::mutex> lock(m_endpoint_mutex);
    if (!m_endpoint)
    {
        throw std::runtime_error("No client connected");
    }
    // Convert const void* to void* for ucxx API
    std::vector<void*> non_const_buffer;
    non_const_buffer.reserve(buffer.size());
    for (const void* ptr : buffer)
    {
        non_const_buffer.push_back(const_cast<void*>(ptr));
    }
    return m_endpoint->tagMultiSend(non_const_buffer, size, isCuda, ucxx::Tag{ tag }, false);
}

std::shared_ptr<ucxx::Request> UCXListener::tagReceive(void* buffer, size_t length, uint64_t tag, uint64_t mask)
{
    if (m_shutdown.load())
    {
        throw std::runtime_error("Listener is shutting down or shut down");
    }
    std::lock_guard<std::mutex> lock(m_endpoint_mutex);
    if (!m_endpoint)
    {
        throw std::runtime_error("No client connected");
    }
    return m_endpoint->tagRecv(buffer, length, ucxx::Tag{ tag }, ucxx::TagMask{ mask });
}

std::shared_ptr<ucxx::Request> UCXListener::tagMultiReceive(const uint64_t tag, const uint64_t tagMask)
{
    if (m_shutdown.load())
    {
        throw std::runtime_error("Listener is shutting down or shut down");
    }
    std::lock_guard<std::mutex> lock(m_endpoint_mutex);
    if (!m_endpoint)
    {
        throw std::runtime_error("No client connected");
    }
    return m_endpoint->tagMultiRecv(ucxx::Tag{ tag }, ucxx::TagMask{ tagMask }, false);
}

void UCXListener::onConnectionRequest(ucp_conn_request_h conn_request, void* arg)
{
    if (!conn_request || !arg)
    {
        CARB_LOG_ERROR("UCXListener::onConnectionRequest: invalid parameters");
        return;
    }

    char ip_str[INET6_ADDRSTRLEN];
    char port_str[INET6_ADDRSTRLEN];
    ucp_conn_request_attr_t attr{};

    UCXListener* listener = static_cast<UCXListener*>(arg);
    assert(listener != nullptr);
    attr.field_mask = UCP_CONN_REQUEST_ATTR_FIELD_CLIENT_ADDR;
    ucxx::utils::ucsErrorThrow(ucp_conn_request_query(conn_request, &attr));
    ucxx::utils::sockaddr_get_ip_port_str(&attr.client_address, ip_str, port_str, INET6_ADDRSTRLEN);
    CARB_LOG_INFO("Server received a connection request from client at address %s:%s", ip_str, port_str);
    listener->createConnection(conn_request);
}

void UCXListener::initialize()
{
    if (m_listener)
    {
        CARB_LOG_INFO("Listener is active, skip initialization");
        return;
    }
    try
    {
        m_worker = m_context->createWorker();
        if (!m_worker)
        {
            throw std::runtime_error("UCXListener: failed to create worker");
        }

        m_listener = m_worker->createListener(m_port, onConnectionRequest, this);
        if (!m_listener)
        {
            throw std::runtime_error("UCXListener: failed to create listener");
        }

        if (m_port == 0)
        {
            m_port = m_listener->getPort();
        }

        CARB_LOG_INFO("Listener created on port %u", m_port);
    }
    catch (const std::exception& e)
    {
        throw std::runtime_error(std::string("UCXListener: initialization failed - ") + e.what());
    }

    m_shutdown.store(false);
    startProgressThread();
}

void UCXListener::createConnection(ucp_conn_request_h conn_request)
{
    if (m_shutdown.load())
    {
        CARB_LOG_WARN("Connection request received during shutdown, rejecting");
        return;
    }

    try
    {
        // Create endpoint with error handling to match client configuration
        std::shared_ptr<ucxx::Endpoint> endpoint = m_listener->createEndpointFromConnRequest(conn_request, true);
        if (!endpoint)
        {
            CARB_LOG_ERROR("Failed to create endpoint from connection request");
            return;
        }

        endpoint->setCloseCallback(
            [this](ucs_status_t status, std::shared_ptr<void>) { onEndpointClosed(status); }, nullptr);
        {
            std::lock_guard<std::mutex> lock(m_endpoint_mutex);
            m_endpoint = endpoint;
            m_connection_condition.notify_all();
        }
    }
    catch (const std::exception& e)
    {
        CARB_LOG_ERROR("Exception during endpoint creation: %s", e.what());
    }
}

void UCXListener::onEndpointClosed(ucs_status_t status)
{
    CARB_LOG_INFO("Endpoint closed with status %d", status);
    // Only clear endpoint if not shutting down to avoid deadlock
    if (!m_shutdown.load())
    {
        std::lock_guard<std::mutex> lock(m_endpoint_mutex);
        m_endpoint.reset();
    }
}

} // namespace isaacsim::ucx::core
