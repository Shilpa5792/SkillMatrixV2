"""
Test cases for dev_v2_getEmployeeCertificates API.
"""
import json
from unittest.mock import patch, MagicMock
import pytest
import psycopg2
from dev_v2_getEmployeeCertificates.main import dev_v2_get_employee_certificate, fetch_employee_certificate


class TestFetchEmployeeCertificate:
    """Test cases for fetch_employee_certificate function."""

    @patch('dev_v2_getEmployeeCertificates.main.db_utils.get_db_connection')
    def test_fetch_employee_certificate_success(self, mock_get_conn, mock_db_connection):
        """Test successful employee certificate fetch."""
        mock_conn, mock_cur = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        sample_data = [
            {
                'id': 1,
                'employeeId': 1,
                'certificateId': 1,
                'issuedDate': '2024-01-01',
                'expiryDate': '2025-01-01'
            }
        ]
        mock_cur.fetchall.return_value = sample_data
        
        result = fetch_employee_certificate()
        
        assert len(result) == 1
        assert result[0]['id'] == 1
        mock_cur.execute.assert_called_once_with('SELECT * FROM "EmployeeCertificates" ORDER BY id')

    @patch('dev_v2_getEmployeeCertificates.main.db_utils.get_db_connection')
    def test_fetch_employee_certificate_empty_result(self, mock_get_conn, mock_db_connection):
        """Test employee certificate fetch with empty result."""
        mock_conn, mock_cur = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cur.fetchall.return_value = []
        
        result = fetch_employee_certificate()
        
        assert result == []


class TestDevV2GetEmployeeCertificate:
    """Test cases for dev_v2_get_employee_certificate Cloud Function."""

    @patch('dev_v2_getEmployeeCertificates.main.fetch_employee_certificate')
    def test_get_employee_certificate_success(self, mock_fetch, mock_flask_request_get):
        """Test successful GET request."""
        sample_data = [
            {
                'id': 1,
                'employeeId': 1,
                'certificateId': 1,
                'issuedDate': '2024-01-01',
                'expiryDate': '2025-01-01'
            }
        ]
        mock_fetch.return_value = sample_data
        
        response, status_code, headers = dev_v2_get_employee_certificate(mock_flask_request_get)
        
        assert status_code == 200
        assert headers['Content-Type'] == 'application/json'
        data = json.loads(response)
        assert data['count'] == 1

    @patch('dev_v2_getEmployeeCertificates.main.fetch_employee_certificate')
    def test_get_employee_certificate_database_error(self, mock_fetch, mock_flask_request_get):
        """Test GET request with database error."""
        mock_fetch.side_effect = psycopg2.Error("Database error")
        
        response, status_code, headers = dev_v2_get_employee_certificate(mock_flask_request_get)
        
        assert status_code == 500
        data = json.loads(response)
        assert 'error' in data

    def test_options_request(self, mock_flask_request_options):
        """Test CORS preflight OPTIONS request."""
        response, status_code, headers = dev_v2_get_employee_certificate(mock_flask_request_options)
        
        assert status_code == 204
        assert headers['Access-Control-Allow-Origin'] == '*'

