"""
Test cases for dev_v2_getSkillHierarchyLink API.
"""
import json
from unittest.mock import patch, MagicMock
import pytest
import psycopg2
from dev_v2_getSkillHierarchyLink.main import dev_v2_get_skill_hierarchy_link, fetch_skill_hierarchy_link


class TestFetchSkillHierarchyLink:
    """Test cases for fetch_skill_hierarchy_link function."""

    @patch('dev_v2_getSkillHierarchyLink.main.db_utils.get_db_connection')
    def test_fetch_skill_hierarchy_link_success(self, mock_get_conn, mock_db_connection):
        """Test successful skill hierarchy link fetch."""
        mock_conn, mock_cur = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        sample_data = [
            {
                'id': 1,
                'domain_id': 1,
                'discipline_id': 1,
                'skill_id': 1,
                'framework_id': 1
            },
            {
                'id': 2,
                'domain_id': 1,
                'discipline_id': 1,
                'skill_id': 2,
                'framework_id': 2
            }
        ]
        mock_cur.fetchall.return_value = sample_data
        
        result = fetch_skill_hierarchy_link()
        
        assert len(result) == 2
        assert result[0]['id'] == 1
        mock_cur.execute.assert_called_once_with('SELECT * FROM "SkillHierarchyLink" ORDER BY id')

    @patch('dev_v2_getSkillHierarchyLink.main.db_utils.get_db_connection')
    def test_fetch_skill_hierarchy_link_empty_result(self, mock_get_conn, mock_db_connection):
        """Test skill hierarchy link fetch with empty result."""
        mock_conn, mock_cur = mock_db_connection
        mock_get_conn.return_value = mock_conn
        mock_cur.fetchall.return_value = []
        
        result = fetch_skill_hierarchy_link()
        
        assert result == []


class TestDevV2GetSkillHierarchyLink:
    """Test cases for dev_v2_get_skill_hierarchy_link Cloud Function."""

    @patch('dev_v2_getSkillHierarchyLink.main.fetch_skill_hierarchy_link')
    def test_get_skill_hierarchy_link_success(self, mock_fetch, mock_flask_request_get):
        """Test successful GET request."""
        sample_data = [
            {
                'id': 1,
                'domain_id': 1,
                'discipline_id': 1,
                'skill_id': 1,
                'framework_id': 1
            }
        ]
        mock_fetch.return_value = sample_data
        
        response, status_code, headers = dev_v2_get_skill_hierarchy_link(mock_flask_request_get)
        
        assert status_code == 200
        assert headers['Content-Type'] == 'application/json'
        data = json.loads(response)
        assert data['count'] == 1
        assert data['results'][0]['id'] == 1

    @patch('dev_v2_getSkillHierarchyLink.main.fetch_skill_hierarchy_link')
    def test_get_skill_hierarchy_link_empty_result(self, mock_fetch, mock_flask_request_get):
        """Test GET request with empty result."""
        mock_fetch.return_value = []
        
        response, status_code, headers = dev_v2_get_skill_hierarchy_link(mock_flask_request_get)
        
        assert status_code == 200
        data = json.loads(response)
        assert data['count'] == 0
        assert data['results'] == []

    @patch('dev_v2_getSkillHierarchyLink.main.fetch_skill_hierarchy_link')
    def test_get_skill_hierarchy_link_database_error(self, mock_fetch, mock_flask_request_get):
        """Test GET request with database error."""
        mock_fetch.side_effect = psycopg2.Error("Database error")
        
        response, status_code, headers = dev_v2_get_skill_hierarchy_link(mock_flask_request_get)
        
        assert status_code == 500
        data = json.loads(response)
        assert 'error' in data

    @patch('dev_v2_getSkillHierarchyLink.main.fetch_skill_hierarchy_link')
    def test_get_skill_hierarchy_link_general_exception(self, mock_fetch, mock_flask_request_get):
        """Test GET request with general exception."""
        mock_fetch.side_effect = Exception("Unexpected error")
        
        response, status_code, headers = dev_v2_get_skill_hierarchy_link(mock_flask_request_get)
        
        assert status_code == 500
        data = json.loads(response)
        assert 'error' in data

    def test_options_request(self, mock_flask_request_options):
        """Test CORS preflight OPTIONS request."""
        response, status_code, headers = dev_v2_get_skill_hierarchy_link(mock_flask_request_options)
        
        assert status_code == 204
        assert headers['Access-Control-Allow-Origin'] == '*'
        assert headers['Access-Control-Allow-Methods'] == 'GET'

