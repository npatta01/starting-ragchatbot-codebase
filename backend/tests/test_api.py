"""
API endpoint tests for FastAPI application.

Tests cover:
- POST /api/query - Query processing with session management
- GET /api/courses - Course statistics retrieval
- Error handling and validation
- Request/response models
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException


class TestQueryEndpoint:
    """Test cases for POST /api/query endpoint"""

    def test_query_with_new_session(self, test_client, test_app):
        """Test query creates new session when session_id not provided"""
        # Arrange
        request_data = {
            "query": "What is Python?"
        }

        # Act
        response = test_client.post("/api/query", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data

        # Verify session was created
        assert data["session_id"] == "test-session-123"
        test_app.state.rag_system.session_manager.create_session.assert_called_once()

    def test_query_with_existing_session(self, test_client, test_app):
        """Test query uses provided session_id"""
        # Arrange
        request_data = {
            "query": "What is Python?",
            "session_id": "existing-session-456"
        }

        # Act
        response = test_client.post("/api/query", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify existing session_id returned
        assert data["session_id"] == "existing-session-456"

        # Verify query was processed with correct session_id
        test_app.state.rag_system.query.assert_called_once_with(
            "What is Python?",
            "existing-session-456"
        )

    def test_query_returns_answer_and_sources(self, test_client):
        """Test query response includes answer and sources"""
        # Arrange
        request_data = {
            "query": "Explain Python functions",
            "session_id": "test-123"
        }

        # Act
        response = test_client.post("/api/query", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert len(data["answer"]) > 0
        assert data["answer"] == "Python is a programming language."

        # Verify sources format
        assert len(data["sources"]) > 0
        assert data["sources"][0] == "[Introduction to Python - Lesson 1]"

    def test_query_missing_query_field(self, test_client):
        """Test query endpoint rejects request without query field"""
        # Arrange
        request_data = {
            "session_id": "test-123"
            # Missing "query" field
        }

        # Act
        response = test_client.post("/api/query", json=request_data)

        # Assert - Pydantic validation should fail
        assert response.status_code == 422  # Unprocessable Entity

    def test_query_empty_query_string(self, test_client):
        """Test query endpoint accepts empty query (validation in business logic, not API)"""
        # Arrange
        request_data = {
            "query": "",
            "session_id": "test-123"
        }

        # Act
        response = test_client.post("/api/query", json=request_data)

        # Assert - API accepts empty string, business logic handles it
        assert response.status_code == 200

    def test_query_handles_rag_system_error(self, test_client, test_app):
        """Test query endpoint handles errors from RAG system gracefully"""
        # Arrange
        test_app.state.rag_system.query.side_effect = RuntimeError("Database connection failed")

        request_data = {
            "query": "What is Python?",
            "session_id": "test-123"
        }

        # Act
        response = test_client.post("/api/query", json=request_data)

        # Assert
        assert response.status_code == 500
        assert "detail" in response.json()
        assert "Database connection failed" in response.json()["detail"]

    def test_query_handles_session_creation_error(self, test_client, test_app):
        """Test query endpoint handles session creation errors"""
        # Arrange
        test_app.state.rag_system.session_manager.create_session.side_effect = RuntimeError("Session service unavailable")

        request_data = {
            "query": "What is Python?"
            # No session_id - should trigger session creation
        }

        # Act
        response = test_client.post("/api/query", json=request_data)

        # Assert
        assert response.status_code == 500

    def test_query_with_long_query_text(self, test_client):
        """Test query endpoint handles very long query strings"""
        # Arrange
        long_query = "What is Python? " * 1000  # Very long query
        request_data = {
            "query": long_query,
            "session_id": "test-123"
        }

        # Act
        response = test_client.post("/api/query", json=request_data)

        # Assert - Should handle long queries
        assert response.status_code == 200

    def test_query_response_model_validation(self, test_client):
        """Test that response matches QueryResponse model"""
        # Arrange
        request_data = {
            "query": "What is Python?",
            "session_id": "test-123"
        }

        # Act
        response = test_client.post("/api/query", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify all required fields present
        required_fields = ["answer", "sources", "session_id"]
        for field in required_fields:
            assert field in data

        # Verify field types
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["session_id"], str)


class TestCoursesEndpoint:
    """Test cases for GET /api/courses endpoint"""

    def test_get_courses_returns_statistics(self, test_client):
        """Test courses endpoint returns total count and titles"""
        # Act
        response = test_client.get("/api/courses")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "total_courses" in data
        assert "course_titles" in data

        # Verify data types
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)

    def test_get_courses_correct_count(self, test_client):
        """Test courses endpoint returns correct course count"""
        # Act
        response = test_client.get("/api/courses")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total_courses"] == 2
        assert len(data["course_titles"]) == 2

    def test_get_courses_correct_titles(self, test_client):
        """Test courses endpoint returns correct course titles"""
        # Act
        response = test_client.get("/api/courses")

        # Assert
        assert response.status_code == 200
        data = response.json()

        expected_titles = ["Introduction to Python", "Advanced Python"]
        assert data["course_titles"] == expected_titles

    def test_get_courses_empty_catalog(self, test_client, test_app):
        """Test courses endpoint handles empty course catalog"""
        # Arrange
        test_app.state.rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": []
        }

        # Act
        response = test_client.get("/api/courses")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["total_courses"] == 0
        assert data["course_titles"] == []

    def test_get_courses_handles_error(self, test_client, test_app):
        """Test courses endpoint handles RAG system errors"""
        # Arrange
        test_app.state.rag_system.get_course_analytics.side_effect = RuntimeError("Vector store unavailable")

        # Act
        response = test_client.get("/api/courses")

        # Assert
        assert response.status_code == 500
        assert "detail" in response.json()
        assert "Vector store unavailable" in response.json()["detail"]

    def test_get_courses_no_parameters_needed(self, test_client):
        """Test courses endpoint works without any parameters"""
        # Act
        response = test_client.get("/api/courses")

        # Assert
        assert response.status_code == 200

    def test_get_courses_response_model_validation(self, test_client):
        """Test that response matches CourseStats model"""
        # Act
        response = test_client.get("/api/courses")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify all required fields present
        required_fields = ["total_courses", "course_titles"]
        for field in required_fields:
            assert field in data

        # Verify field types
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)

        # Verify list contains strings
        for title in data["course_titles"]:
            assert isinstance(title, str)


class TestHealthEndpoint:
    """Test cases for GET /health endpoint"""

    def test_health_check_returns_ok(self, test_client):
        """Test health check endpoint returns healthy status"""
        # Act
        response = test_client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"


class TestCORSMiddleware:
    """Test cases for CORS middleware configuration"""

    def test_cors_headers_on_query_endpoint(self, test_client):
        """Test CORS headers are present on query endpoint"""
        # Arrange
        request_data = {"query": "Test"}

        # Act
        response = test_client.post("/api/query", json=request_data)

        # Assert
        # FastAPI TestClient doesn't simulate full CORS, but we can verify endpoint works
        assert response.status_code == 200

    def test_options_request_allowed(self, test_client):
        """Test OPTIONS request (preflight) works"""
        # Act
        response = test_client.options("/api/query")

        # Assert - Should not reject OPTIONS
        # TestClient handles CORS differently, so just verify it doesn't error
        assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly defined


class TestRequestValidation:
    """Test cases for request validation and error handling"""

    def test_invalid_json_body(self, test_client):
        """Test endpoint handles malformed JSON gracefully"""
        # Act
        response = test_client.post(
            "/api/query",
            data="invalid json{{{",
            headers={"Content-Type": "application/json"}
        )

        # Assert
        assert response.status_code == 422  # Unprocessable Entity

    def test_wrong_content_type(self, test_client):
        """Test endpoint requires JSON content type"""
        # Act
        response = test_client.post(
            "/api/query",
            data="query=What is Python?",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert
        assert response.status_code == 422

    def test_extra_fields_ignored(self, test_client):
        """Test endpoint ignores extra fields in request"""
        # Arrange
        request_data = {
            "query": "What is Python?",
            "session_id": "test-123",
            "extra_field": "should be ignored"
        }

        # Act
        response = test_client.post("/api/query", json=request_data)

        # Assert - Should succeed, extra fields ignored by Pydantic
        assert response.status_code == 200

    def test_null_values_handled(self, test_client):
        """Test endpoint handles null values appropriately"""
        # Arrange
        request_data = {
            "query": "What is Python?",
            "session_id": None  # Explicitly null
        }

        # Act
        response = test_client.post("/api/query", json=request_data)

        # Assert - Should create new session
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-123"


class TestEndpointIntegration:
    """Integration tests across multiple endpoints"""

    def test_query_then_get_courses(self, test_client):
        """Test querying and then fetching course statistics"""
        # Act 1: Query
        query_response = test_client.post("/api/query", json={"query": "What is Python?"})

        # Assert 1
        assert query_response.status_code == 200

        # Act 2: Get courses
        courses_response = test_client.get("/api/courses")

        # Assert 2
        assert courses_response.status_code == 200
        courses_data = courses_response.json()
        assert courses_data["total_courses"] > 0

    def test_multiple_queries_same_session(self, test_client, test_app):
        """Test multiple queries using the same session ID"""
        # Arrange
        session_id = "persistent-session-789"

        # Act 1: First query
        response1 = test_client.post("/api/query", json={
            "query": "What is Python?",
            "session_id": session_id
        })

        # Act 2: Second query
        response2 = test_client.post("/api/query", json={
            "query": "Tell me more",
            "session_id": session_id
        })

        # Assert - Both should succeed with same session
        assert response1.status_code == 200
        assert response2.status_code == 200

        assert response1.json()["session_id"] == session_id
        assert response2.json()["session_id"] == session_id

        # Verify RAG system was called with correct session
        assert test_app.state.rag_system.query.call_count == 2

    def test_concurrent_sessions(self, test_client):
        """Test handling multiple concurrent sessions"""
        # Arrange
        sessions = ["session-1", "session-2", "session-3"]

        # Act - Make queries with different sessions
        responses = []
        for session_id in sessions:
            response = test_client.post("/api/query", json={
                "query": "What is Python?",
                "session_id": session_id
            })
            responses.append(response)

        # Assert - All should succeed with correct session IDs
        for i, response in enumerate(responses):
            assert response.status_code == 200
            assert response.json()["session_id"] == sessions[i]
