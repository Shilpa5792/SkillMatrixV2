"""
Test cases for dev_v2_getEmployee API.
"""
import json
from unittest.mock import patch, MagicMock
import pytest
import psycopg2
from dev_v2_getEmployee.main import dev_v2_get_employee, fetch_employee


class TestFetchEmployee:
    """Test cases for fetch_employee function."""

    @patch('dev_v2_getEmployee.main.db_utils.get_db_connection')
    def test_fetch_employee_success(self, mock_get_conn, mock_db_connection, sample_employee_data):
        """Test successful employee fetch."""
        mock_conn, mock_cur = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        # Mock cursor fetchall to return sample data
        mock_cur.fetchall.return_value = sample_employee_data
        
        result = fetch_employee()
        
        assert len(result) == 2
        assert result[0]['email'] == 'john.doe@example.com'
        mock_cur.execute.assert_called_once_with('SELECT * FROM "Employee" ORDER BY id')

    @patch('dev_v2_getEmployee.main.db_utils.get_db_connection')
    def test_fetch_employee_empty_result(self, mock_get_conn, mock_db_connection):
        """Test employee fetch with empty result."""
        mock_conn, mock_cur = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cur.fetchall.return_value = []
        
        result = fetch_employee()
        
        assert result == []
        mock_cur.execute.assert_called_once()

    @patch('dev_v2_getEmployee.main.db_utils.get_db_connection')
    def test_fetch_employee_database_error(self, mock_get_conn, mock_db_connection):
        """Test employee fetch with database error."""
        mock_conn, mock_cur = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cur.execute.side_effect = psycopg2.Error("Database connection failed")
        
        with pytest.raises(psycopg2.Error):
            fetch_employee()


class TestDevV2GetEmployee:
    """Test cases for dev_v2_get_employee Cloud Function."""

    @patch('dev_v2_getEmployee.main.fetch_employee')
    def test_get_employee_success(self, mock_fetch, mock_flask_request_get, sample_employee_data):
        """Test successful GET request."""
        mock_fetch.return_value = sample_employee_data
        
        response, status_code, headers = dev_v2_get_employee(mock_flask_request_get)
        
        assert status_code == 200
        assert headers['Content-Type'] == 'application/json'
        assert headers['Access-Control-Allow-Origin'] == '*'
        
        data = json.loads(response)
        assert data['count'] == 2
        assert len(data['results']) == 2
        assert data['results'][0]['email'] == 'john.doe@example.com'

    @patch('dev_v2_getEmployee.main.fetch_employee')
    def test_get_employee_empty_result(self, mock_fetch, mock_flask_request_get):
        """Test GET request with empty result."""
        mock_fetch.return_value = []
        
        response, status_code, headers = dev_v2_get_employee(mock_flask_request_get)
        
        assert status_code == 200
        data = json.loads(response)
        assert data['count'] == 0
        assert data['results'] == []

    @patch('dev_v2_getEmployee.main.fetch_employee')
    def test_get_employee_database_error(self, mock_fetch, mock_flask_request_get):
        """Test GET request with database error."""
        mock_fetch.side_effect = psycopg2.Error("Database error")
        
        response, status_code, headers = dev_v2_get_employee(mock_flask_request_get)
        
        assert status_code == 500
        data = json.loads(response)
        assert 'error' in data

    @patch('dev_v2_getEmployee.main.fetch_employee')
    def test_get_employee_general_exception(self, mock_fetch, mock_flask_request_get):
        """Test GET request with general exception."""
        mock_fetch.side_effect = Exception("Unexpected error")
        
        response, status_code, headers = dev_v2_get_employee(mock_flask_request_get)
        
        assert status_code == 500
        data = json.loads(response)
        assert 'error' in data

    def test_options_request(self, mock_flask_request_options):
        """Test CORS preflight OPTIONS request."""
        response, status_code, headers = dev_v2_get_employee(mock_flask_request_options)
        
        assert status_code == 204
        assert headers['Access-Control-Allow-Origin'] == '*'
        assert headers['Access-Control-Allow-Methods'] == 'GET'
        assert response == ''

    @patch('dev_v2_getEmployee.main.fetch_employee')
    def test_datetime_serialization(self, mock_fetch, mock_flask_request_get):
        """Test that datetime objects are properly serialized."""
        from datetime import datetime
        data_with_datetime = [
            {
                'id': 1,
                'email': 'test@example.com',
                'created_at': datetime(2024, 1, 1, 12, 0, 0)
            }
        ]
        mock_fetch.return_value = data_with_datetime
        
        response, status_code, headers = dev_v2_get_employee(mock_flask_request_get)
        
        assert status_code == 200
        data = json.loads(response)
        assert isinstance(data['results'][0]['created_at'], str)

