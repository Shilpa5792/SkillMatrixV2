"""
Test cases for dev_v2_getEmployeeSkill API.
"""
import json
from unittest.mock import patch, MagicMock
import pytest
import psycopg2
from dev_v2_getEmployeeSkill.main import dev_v2_get_employee_skill, fetch_employee_skill_by_email


class TestFetchEmployeeSkillByEmail:
    """Test cases for fetch_employee_skill_by_email function."""

    @patch('dev_v2_getEmployeeSkill.main.db_utils.get_db_connection')
    def test_fetch_employee_skill_success(self, mock_get_conn, mock_db_connection, sample_employee_skill_data):
        """Test successful employee skill fetch."""
        mock_conn, mock_cur = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cur.fetchall.return_value = sample_employee_skill_data
        
        result = fetch_employee_skill_by_email('john.doe@example.com')
        
        assert len(result) == 2
        assert result[0]['Category'] == 'Technology'
        mock_cur.execute.assert_called()

    @patch('dev_v2_getEmployeeSkill.main.db_utils.get_db_connection')
    def test_fetch_employee_skill_empty_result(self, mock_get_conn, mock_db_connection):
        """Test employee skill fetch with empty result."""
        mock_conn, mock_cur = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cur.fetchall.return_value = []
        
        result = fetch_employee_skill_by_email('nonexistent@example.com')
        
        assert result == []

    @patch('dev_v2_getEmployeeSkill.main.db_utils.get_db_connection')
    def test_fetch_employee_skill_case_insensitive(self, mock_get_conn, mock_db_connection, sample_employee_skill_data):
        """Test that email matching is case insensitive."""
        mock_conn, mock_cur = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cur.fetchall.return_value = sample_employee_skill_data
        
        # Test with uppercase email
        result = fetch_employee_skill_by_email('JOHN.DOE@EXAMPLE.COM')
        
        assert len(result) == 2
        # Verify the SQL was called with lowercase email
        call_args = mock_cur.execute.call_args[0]
        assert call_args[1][0].lower() == 'john.doe@example.com'


class TestDevV2GetEmployeeSkill:
    """Test cases for dev_v2_get_employee_skill Cloud Function."""

    @patch('dev_v2_getEmployeeSkill.main.fetch_employee_skill_by_email')
    def test_get_employee_skill_success_get(self, mock_fetch, mock_flask_request_get, sample_employee_skill_data):
        """Test successful GET request."""
        mock_flask_request_get.args.get.return_value = 'john.doe@example.com'
        mock_fetch.return_value = sample_employee_skill_data
        
        response, status_code, headers = dev_v2_get_employee_skill(mock_flask_request_get)
        
        assert status_code == 200
        assert headers['Content-Type'] == 'application/json'
        data = json.loads(response)
        assert data['employeeEmail'] == 'john.doe@example.com'
        assert len(data['skills']) == 2

    @patch('dev_v2_getEmployeeSkill.main.fetch_employee_skill_by_email')
    def test_get_employee_skill_success_post(self, mock_fetch, mock_flask_request_post, sample_employee_skill_data):
        """Test successful POST request."""
        mock_flask_request_post.get_json.return_value = {'email': 'john.doe@example.com'}
        mock_fetch.return_value = sample_employee_skill_data
        
        response, status_code, headers = dev_v2_get_employee_skill(mock_flask_request_post)
        
        assert status_code == 200
        data = json.loads(response)
        assert data['employeeEmail'] == 'john.doe@example.com'

    @patch('dev_v2_getEmployeeSkill.main.fetch_employee_skill_by_email')
    def test_get_employee_skill_missing_email_get(self, mock_fetch, mock_flask_request_get):
        """Test GET request with missing email parameter."""
        mock_flask_request_get.args.get.return_value = None
        
        response, status_code, headers = dev_v2_get_employee_skill(mock_flask_request_get)
        
        assert status_code == 400
        data = json.loads(response)
        assert 'error' in data
        assert 'email' in data['error'].lower()
        mock_fetch.assert_not_called()

    @patch('dev_v2_getEmployeeSkill.main.fetch_employee_skill_by_email')
    def test_get_employee_skill_missing_email_post(self, mock_fetch, mock_flask_request_post):
        """Test POST request with missing email in body."""
        mock_flask_request_post.get_json.return_value = {}
        
        response, status_code, headers = dev_v2_get_employee_skill(mock_flask_request_post)
        
        assert status_code == 400
        data = json.loads(response)
        assert 'error' in data
        mock_fetch.assert_not_called()

    @patch('dev_v2_getEmployeeSkill.main.fetch_employee_skill_by_email')
    def test_get_employee_skill_empty_json_post(self, mock_fetch, mock_flask_request_post):
        """Test POST request with empty JSON."""
        mock_flask_request_post.get_json.return_value = None
        
        response, status_code, headers = dev_v2_get_employee_skill(mock_flask_request_post)
        
        assert status_code == 400
        mock_fetch.assert_not_called()

    @patch('dev_v2_getEmployeeSkill.main.fetch_employee_skill_by_email')
    def test_get_employee_skill_database_error(self, mock_fetch, mock_flask_request_get):
        """Test GET request with database error."""
        mock_flask_request_get.args.get.return_value = 'test@example.com'
        mock_fetch.side_effect = psycopg2.Error("Database error")
        
        response, status_code, headers = dev_v2_get_employee_skill(mock_flask_request_get)
        
        assert status_code == 500
        data = json.loads(response)
        assert 'error' in data

    @patch('dev_v2_getEmployeeSkill.main.fetch_employee_skill_by_email')
    def test_get_employee_skill_email_lowercase(self, mock_fetch, mock_flask_request_get, sample_employee_skill_data):
        """Test that email is converted to lowercase."""
        mock_flask_request_get.args.get.return_value = 'JOHN.DOE@EXAMPLE.COM'
        mock_fetch.return_value = sample_employee_skill_data
        
        response, status_code, headers = dev_v2_get_employee_skill(mock_flask_request_get)
        
        assert status_code == 200
        data = json.loads(response)
        assert data['employeeEmail'] == 'john.doe@example.com'
        # Verify fetch was called with lowercase email
        mock_fetch.assert_called_once_with('john.doe@example.com')

    def test_options_request(self, mock_flask_request_options):
        """Test CORS preflight OPTIONS request."""
        response, status_code, headers = dev_v2_get_employee_skill(mock_flask_request_options)
        
        assert status_code == 204
        assert headers['Access-Control-Allow-Origin'] == '*'
        assert headers['Access-Control-Allow-Methods'] == 'GET, POST, OPTIONS'

    @patch('dev_v2_getEmployeeSkill.main.fetch_employee_skill_by_email')
    def test_get_employee_skill_empty_result(self, mock_fetch, mock_flask_request_get):
        """Test GET request with empty result."""
        mock_flask_request_get.args.get.return_value = 'nonexistent@example.com'
        mock_fetch.return_value = []
        
        response, status_code, headers = dev_v2_get_employee_skill(mock_flask_request_get)
        
        assert status_code == 200
        data = json.loads(response)
        assert data['employeeEmail'] == 'nonexistent@example.com'
        assert data['skills'] == []

