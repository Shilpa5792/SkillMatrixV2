"""
Test cases for dev_v2_getMasterDomain API.
"""
import json
from unittest.mock import patch, MagicMock
import pytest
import psycopg2
from dev_v2_getMasterDomain.main import dev_v2_get_master_domain, fetch_master_domain


class TestFetchMasterDomain:
    """Test cases for fetch_master_domain function."""

    @patch('dev_v2_getMasterDomain.main.db_utils.get_db_connection')
    def test_fetch_master_domain_success(self, mock_get_conn, mock_db_connection):
        """Test successful master domain fetch."""
        mock_conn, mock_cur = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        sample_data = [
            {'id': 1, 'domain_name': 'Technology', 'description': 'Tech domain'},
            {'id': 2, 'domain_name': 'Business', 'description': 'Business domain'}
        ]
        mock_cur.fetchall.return_value = sample_data
        
        result = fetch_master_domain()
        
        assert len(result) == 2
        assert result[0]['domain_name'] == 'Technology'
        mock_cur.execute.assert_called_once_with('SELECT * FROM "MasterDomain" ORDER BY id')


class TestDevV2GetMasterDomain:
    """Test cases for dev_v2_get_master_domain Cloud Function."""

    @patch('dev_v2_getMasterDomain.main.fetch_master_domain')
    def test_get_master_domain_success(self, mock_fetch, mock_flask_request_get):
        """Test successful GET request."""
        sample_data = [
            {'id': 1, 'domain_name': 'Technology', 'description': 'Tech domain'}
        ]
        mock_fetch.return_value = sample_data
        
        response, status_code, headers = dev_v2_get_master_domain(mock_flask_request_get)
        
        assert status_code == 200
        assert headers['Content-Type'] == 'application/json'
        data = json.loads(response)
        assert data['count'] == 1

    @patch('dev_v2_getMasterDomain.main.fetch_master_domain')
    def test_get_master_domain_database_error(self, mock_fetch, mock_flask_request_get):
        """Test GET request with database error."""
        mock_fetch.side_effect = psycopg2.Error("Database error")
        
        response, status_code, headers = dev_v2_get_master_domain(mock_flask_request_get)
        
        assert status_code == 500
        data = json.loads(response)
        assert 'error' in data

    def test_options_request(self, mock_flask_request_options):
        """Test CORS preflight OPTIONS request."""
        response, status_code, headers = dev_v2_get_master_domain(mock_flask_request_options)
        
        assert status_code == 204
        assert headers['Access-Control-Allow-Origin'] == '*'

