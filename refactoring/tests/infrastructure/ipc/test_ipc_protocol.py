"""Tests for IPC Protocol."""

from __future__ import annotations

import json

import pytest
from refactoring.src.infrastructure.ipc.ipc_protocol import (
    IPCMessageType,
    IPCRequest,
    IPCResponse,
    create_error_response,
    create_request,
    create_response,
    parse_message,
    validate_request,
    validate_response,
)


class TestIPCMessageType:
    """Tests for IPCMessageType enum."""

    def test_all_message_types_defined(self):
        """All 11 client request types are defined."""
        client_types = [
            IPCMessageType.SEND_MESSAGE,
            IPCMessageType.GET_STATE,
            IPCMessageType.GET_PROVIDERS,
            IPCMessageType.SET_PROVIDER,
            IPCMessageType.GET_TRIGGERS,
            IPCMessageType.SET_TRIGGER,
            IPCMessageType.GET_TEMPLATES,
            IPCMessageType.SET_TEMPLATE,
            IPCMessageType.TEST_MODE,
            IPCMessageType.PING,
            IPCMessageType.SHUTDOWN,
        ]
        assert len(client_types) == 11

    def test_response_types_defined(self):
        """Response types are defined."""
        response_types = [
            IPCMessageType.RESPONSE,
            IPCMessageType.ERROR,
            IPCMessageType.STREAMING_CHUNK,
            IPCMessageType.STREAMING_DONE,
        ]
        assert len(response_types) == 4

    def test_message_type_values_are_strings(self):
        """Message type values are lowercase strings."""
        assert IPCMessageType.SEND_MESSAGE.value == "send_message"
        assert IPCMessageType.PING.value == "ping"
        assert IPCMessageType.RESPONSE.value == "response"


class TestIPCRequest:
    """Tests for IPCRequest."""

    def test_create_request_basic(self):
        """Creating basic request works."""
        request = IPCRequest.create(
            IPCMessageType.PING,
            "req_001"
        )

        assert request.type == "ping"
        assert request.request_id == "req_001"
        assert request.data == {}

    def test_create_request_with_data(self):
        """Creating request with data works."""
        request = IPCRequest.create(
            IPCMessageType.SEND_MESSAGE,
            "req_002",
            user_message="Hello",
            session_id="session_123"
        )

        assert request.type == "send_message"
        assert request.request_id == "req_002"
        assert request.data["user_message"] == "Hello"
        assert request.data["session_id"] == "session_123"

    def test_request_to_json(self):
        """Request serializes to JSON correctly."""
        request = IPCRequest.create(
            IPCMessageType.GET_PROVIDERS,
            "req_003"
        )

        json_str = request.to_json()
        data = json.loads(json_str)

        assert data["type"] == "get_providers"
        assert data["request_id"] == "req_003"
        assert "data" in data

    def test_request_from_json(self):
        """Request deserializes from JSON correctly."""
        json_str = '{"type": "ping", "request_id": "req_004", "data": {}}'

        request = IPCRequest.from_json(json_str)

        assert request.type == "ping"
        assert request.request_id == "req_004"
        assert request.data == {}

    def test_request_roundtrip(self):
        """Request can be serialized and deserialized."""
        original = IPCRequest.create(
            IPCMessageType.SET_PROVIDER,
            "req_005",
            provider="claude"
        )

        json_str = original.to_json()
        restored = IPCRequest.from_json(json_str)

        assert restored.type == original.type
        assert restored.request_id == original.request_id
        assert restored.data == original.data


class TestIPCResponse:
    """Tests for IPCResponse."""

    def test_create_success_response(self):
        """Creating success response works."""
        response = IPCResponse.create(
            "req_001",
            success=True,
            result="pong"
        )

        assert response.type == "response"
        assert response.request_id == "req_001"
        assert response.success is True
        assert response.error_message is None
        assert response.data["result"] == "pong"

    def test_create_error_response(self):
        """Creating error response works."""
        response = IPCResponse.create(
            "req_002",
            success=False,
            error_message="Provider not found"
        )

        assert response.request_id == "req_002"
        assert response.success is False
        assert response.error_message == "Provider not found"

    def test_response_to_json(self):
        """Response serializes to JSON correctly."""
        response = IPCResponse.create(
            "req_003",
            providers=["claude", "openai"]
        )

        json_str = response.to_json()
        data = json.loads(json_str)

        assert data["type"] == "response"
        assert data["request_id"] == "req_003"
        assert data["success"] is True
        assert data["data"]["providers"] == ["claude", "openai"]

    def test_response_from_json(self):
        """Response deserializes from JSON correctly."""
        json_str = '''
        {
            "type": "response",
            "request_id": "req_004",
            "success": true,
            "error_message": null,
            "data": {"result": "ok"}
        }
        '''

        response = IPCResponse.from_json(json_str)

        assert response.type == "response"
        assert response.request_id == "req_004"
        assert response.success is True
        assert response.data["result"] == "ok"

    def test_response_roundtrip(self):
        """Response can be serialized and deserialized."""
        original = IPCResponse.create(
            "req_005",
            success=True,
            llm_response="Hello there!",
            metadata={"model": "claude-3-5-sonnet"}
        )

        json_str = original.to_json()
        restored = IPCResponse.from_json(json_str)

        assert restored.type == original.type
        assert restored.request_id == original.request_id
        assert restored.success == original.success
        assert restored.data == original.data


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_create_request_helper(self):
        """create_request helper creates JSON string."""
        json_str = create_request(
            IPCMessageType.PING,
            "req_001"
        )

        data = json.loads(json_str)
        assert data["type"] == "ping"
        assert data["request_id"] == "req_001"

    def test_create_response_helper(self):
        """create_response helper creates JSON string."""
        json_str = create_response(
            "req_001",
            result="pong"
        )

        data = json.loads(json_str)
        assert data["request_id"] == "req_001"
        assert data["success"] is True
        assert data["data"]["result"] == "pong"

    def test_create_error_response_helper(self):
        """create_error_response helper creates JSON string."""
        json_str = create_error_response(
            "req_001",
            "Something went wrong",
            code=500
        )

        data = json.loads(json_str)
        assert data["request_id"] == "req_001"
        assert data["success"] is False
        assert data["error_message"] == "Something went wrong"
        assert data["data"]["code"] == 500

    def test_parse_message_request(self):
        """parse_message handles request messages."""
        json_str = create_request(IPCMessageType.GET_STATE, "req_001")

        message = parse_message(json_str)

        assert isinstance(message, IPCRequest)
        assert message.type == "get_state"
        assert message.request_id == "req_001"

    def test_parse_message_response(self):
        """parse_message handles response messages."""
        json_str = create_response("req_001", state={"active": True})

        message = parse_message(json_str)

        assert isinstance(message, IPCResponse)
        assert message.request_id == "req_001"
        assert message.success is True


class TestValidation:
    """Tests for message validation."""

    def test_validate_request_success(self):
        """Valid request passes validation."""
        request = IPCRequest.create(IPCMessageType.PING, "req_001")

        assert validate_request(request) is True

    def test_validate_request_missing_type(self):
        """Request without type fails validation."""
        request = IPCRequest(type="", request_id="req_001", data={})

        with pytest.raises(ValueError, match="missing 'type'"):
            validate_request(request)

    def test_validate_request_missing_request_id(self):
        """Request without request_id fails validation."""
        request = IPCRequest(type="ping", request_id="", data={})

        with pytest.raises(ValueError, match="missing 'request_id'"):
            validate_request(request)

    def test_validate_request_invalid_type(self):
        """Request with invalid type fails validation."""
        request = IPCRequest(type="invalid_type", request_id="req_001", data={})

        with pytest.raises(ValueError, match="Invalid message type"):
            validate_request(request)

    def test_validate_response_success(self):
        """Valid response passes validation."""
        response = IPCResponse.create("req_001", success=True)

        assert validate_response(response) is True

    def test_validate_response_missing_request_id(self):
        """Response without request_id fails validation."""
        response = IPCResponse(
            type="response",
            request_id="",
            success=True,
            error_message=None,
            data={}
        )

        with pytest.raises(ValueError, match="missing 'request_id'"):
            validate_response(response)

    def test_validate_response_error_without_message(self):
        """Error response without error_message fails validation."""
        response = IPCResponse(
            type="response",
            request_id="req_001",
            success=False,
            error_message=None,
            data={}
        )

        with pytest.raises(ValueError, match="missing 'error_message'"):
            validate_response(response)

    def test_validate_response_error_with_message(self):
        """Error response with error_message passes validation."""
        response = IPCResponse.create(
            "req_001",
            success=False,
            error_message="Error occurred"
        )

        assert validate_response(response) is True


class TestMessageTypes:
    """Tests for all message type values."""

    def test_all_message_types_unique(self):
        """All message type values are unique."""
        values = [msg_type.value for msg_type in IPCMessageType]
        assert len(values) == len(set(values))

    def test_message_types_lowercase_snake_case(self):
        """All message type values use lowercase snake_case."""
        for msg_type in IPCMessageType:
            assert msg_type.value.islower()
            assert " " not in msg_type.value
            # Allow underscores and lowercase letters
            assert all(c.islower() or c == "_" for c in msg_type.value)
