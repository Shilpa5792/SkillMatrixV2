"""
Shared pytest fixtures for testing Cloud Functions.
"""
import json
from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
from flask import Request


@pytest.fixture
def mock_db_connection():
    """Mock database connection."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.cursor.return_value.__exit__.return_value = None
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=None)
    return mock_conn, mock_cur


@pytest.fixture
def sample_employee_data():
    """Sample employee data for testing."""
    return [
        {
            'id': 1,
            'email': 'john.doe@example.com',
            'name': 'John Doe',
            'created_at': datetime(2024, 1, 1, 12, 0, 0),
            'updated_at': datetime(2024, 1, 2, 12, 0, 0)
        },
        {
            'id': 2,
            'email': 'jane.smith@example.com',
            'name': 'Jane Smith',
            'created_at': datetime(2024, 1, 3, 12, 0, 0),
            'updated_at': datetime(2024, 1, 4, 12, 0, 0)
        }
    ]


@pytest.fixture
def sample_employee_skill_data():
    """Sample employee skill data for testing."""
    return [
        {
            'hashId': 'abc123',
            'Category': 'Technology',
            'Sub-Category': 'Software Development',
            'Sub-Sub-Category': 'Python',
            'Tools': 'Django',
            'Level': 'Intermediate',
            'Status': 'Approved',
            'RejectReason': None
        },
        {
            'hashId': 'def456',
            'Category': 'Technology',
            'Sub-Category': 'Software Development',
            'Sub-Sub-Category': 'JavaScript',
            'Tools': 'React',
            'Level': 'Advanced',
            'Status': 'Approved',
            'RejectReason': None
        }
    ]


@pytest.fixture
def sample_master_skill_data():
    """Sample master skill data for testing."""
    return [
        {
            'id': 1,
            'skill_name': 'Python Programming',
            'description': 'Python programming language',
            'isMandatory': True,
            'created_at': datetime(2024, 1, 1, 12, 0, 0),
            'updated_at': datetime(2024, 1, 2, 12, 0, 0)
        },
        {
            'id': 2,
            'skill_name': 'JavaScript Programming',
            'description': 'JavaScript programming language',
            'isMandatory': False,
            'created_at': datetime(2024, 1, 3, 12, 0, 0),
            'updated_at': datetime(2024, 1, 4, 12, 0, 0)
        }
    ]


@pytest.fixture
def mock_flask_request_get():
    """Mock Flask GET request."""
    request = MagicMock(spec=Request)
    request.method = 'GET'
    request.args = MagicMock()
    request.get_json = MagicMock(return_value=None)
    return request


@pytest.fixture
def mock_flask_request_post():
    """Mock Flask POST request."""
    request = MagicMock(spec=Request)
    request.method = 'POST'
    request.args = MagicMock()
    return request


@pytest.fixture
def mock_flask_request_options():
    """Mock Flask OPTIONS request."""
    request = MagicMock(spec=Request)
    request.method = 'OPTIONS'
    return request

