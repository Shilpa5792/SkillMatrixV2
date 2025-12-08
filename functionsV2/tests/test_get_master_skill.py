"""
Test cases for dev_v2_getMasterSkill API.
"""
import json
from unittest.mock import patch, MagicMock
import pytest
import psycopg2
from dev_v2_getMasterSkill.main import dev_v2_get_master_skill, fetch_master_skill


class TestFetchMasterSkill:
    """Test cases for fetch_master_skill function."""

    @patch('dev_v2_getMasterSkill.main.db_utils.get_db_connection')
    def test_fetch_master_skill_success_no_search(self, mock_get_conn, mock_db_connection, sample_master_skill_data):
        """Test successful master skill fetch without search."""
        mock_conn, mock_cur = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cur.fetchall.return_value = sample_master_skill_data
        
        result = fetch_master_skill()
        
        assert len(result) == 2
        assert result[0]['skill_name'] == 'Python Programming'

    @patch('dev_v2_getMasterSkill.main.db_utils.get_db_connection')
    def test_fetch_master_skill_with_search(self, mock_get_conn, mock_db_connection):
        """Test master skill fetch with search parameter."""
        mock_conn, mock_cur = mock_db_connection
        mock_get_conn.return_value = mock_conn
        filtered_data = [{
            'id': 1,
            'skill_name': 'Python Programming',
            'description': 'Python programming language',
            'isMandatory': True,
            'created_at': None,
            'updated_at': None
        }]
        mock_cur.fetchall.return_value = filtered_data
        
        result = fetch_master_skill(search='Python')
        
        assert len(result) == 1
        assert result[0]['skill_name'] == 'Python Programming'
        # Verify SQL was called with search pattern
        call_args = mock_cur.execute.call_args
        assert '%Python%' in str(call_args)

    @patch('dev_v2_getMasterSkill.main.db_utils.get_db_connection')
    def test_fetch_master_skill_empty_result(self, mock_get_conn, mock_db_connection):
        """Test master skill fetch with empty result."""
        mock_conn, mock_cur = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cur.fetchall.return_value = []
        
        result = fetch_master_skill(search='Nonexistent')
        
        assert result == []


class TestDevV2GetMasterSkill:
    """Test cases for dev_v2_get_master_skill Cloud Function."""

    @patch('dev_v2_getMasterSkill.main.fetch_master_skill')
    def test_get_master_skill_success_no_search(self, mock_fetch, mock_flask_request_get, sample_master_skill_data):
        """Test successful GET request without search parameter."""
        mock_flask_request_get.args.get.return_value = None
        mock_fetch.return_value = sample_master_skill_data
        
        response, status_code, headers = dev_v2_get_master_skill(mock_flask_request_get)
        
        assert status_code == 200
        assert headers['Content-Type'] == 'application/json'
        data = json.loads(response)
        assert data['count'] == 2
        mock_fetch.assert_called_once_with(search=None)

    @patch('dev_v2_getMasterSkill.main.fetch_master_skill')
    def test_get_master_skill_with_search(self, mock_fetch, mock_flask_request_get):
        """Test GET request with search parameter."""
        mock_flask_request_get.args.get.side_effect = lambda key, default=None: 'Python' if key == 'search' else default
        filtered_data = [{
            'id': 1,
            'skill_name': 'Python Programming',
            'description': 'Python programming language',
            'isMandatory': True,
            'created_at': None,
            'updated_at': None
        }]
        mock_fetch.return_value = filtered_data
        
        response, status_code, headers = dev_v2_get_master_skill(mock_flask_request_get)
        
        assert status_code == 200
        data = json.loads(response)
        assert data['count'] == 1
        mock_fetch.assert_called_once_with(search='Python')

    @patch('dev_v2_getMasterSkill.main.fetch_master_skill')
    def test_get_master_skill_database_error(self, mock_fetch, mock_flask_request_get):
        """Test GET request with database error."""
        mock_flask_request_get.args.get.return_value = None
        mock_fetch.side_effect = psycopg2.Error("Database error")
        
        response, status_code, headers = dev_v2_get_master_skill(mock_flask_request_get)
        
        assert status_code == 500
        data = json.loads(response)
        assert 'error' in data

    @patch('dev_v2_getMasterSkill.main.fetch_master_skill')
    def test_get_master_skill_datetime_serialization(self, mock_fetch, mock_flask_request_get):
        """Test that datetime objects are properly serialized."""
        from datetime import datetime
        mock_flask_request_get.args.get.return_value = None
        data_with_datetime = [{
            'id': 1,
            'skill_name': 'Test Skill',
            'description': 'Test',
            'isMandatory': False,
            'created_at': datetime(2024, 1, 1, 12, 0, 0),
            'updated_at': datetime(2024, 1, 2, 12, 0, 0)
        }]
        mock_fetch.return_value = data_with_datetime
        
        response, status_code, headers = dev_v2_get_master_skill(mock_flask_request_get)
        
        assert status_code == 200
        data = json.loads(response)
        assert isinstance(data['results'][0]['created_at'], str)
        assert isinstance(data['results'][0]['updated_at'], str)

    def test_options_request(self, mock_flask_request_options):
        """Test CORS preflight OPTIONS request."""
        response, status_code, headers = dev_v2_get_master_skill(mock_flask_request_options)
        
        assert status_code == 204
        assert headers['Access-Control-Allow-Origin'] == '*'

