"""
Test cases for dev_v2_getMasteDiscipline API.
"""
import json
from unittest.mock import patch, MagicMock
import pytest
import psycopg2
from dev_v2_getMasteDiscipline.main import dev_v2_get_master_discipline, fetch_master_discipline


class TestFetchMasterDiscipline:
    """Test cases for fetch_master_discipline function."""

    @patch('dev_v2_getMasteDiscipline.main.db_utils.get_db_connection')
    def test_fetch_master_discipline_success(self, mock_get_conn, mock_db_connection):
        """Test successful master discipline fetch."""
        mock_conn, mock_cur = mock_db_connection
        mock_get_conn.return_value = mock_conn
        
        sample_data = [
            {'id': 1, 'discipline_name': 'Software Development', 'description': 'Dev discipline'},
            {'id': 2, 'discipline_name': 'Data Science', 'description': 'Data discipline'}
        ]
        mock_cur.fetchall.return_value = sample_data
        
        result = fetch_master_discipline()
        
        assert len(result) == 2
        assert result[0]['discipline_name'] == 'Software Development'
        mock_cur.execute.assert_called_once_with('SELECT * FROM "MasterDiscipline" ORDER BY id')


class TestDevV2GetMasterDiscipline:
    """Test cases for dev_v2_get_master_discipline Cloud Function."""

    @patch('dev_v2_getMasteDiscipline.main.fetch_master_discipline')
    def test_get_master_discipline_success(self, mock_fetch, mock_flask_request_get):
        """Test successful GET request."""
        sample_data = [
            {'id': 1, 'discipline_name': 'Software Development', 'description': 'Dev discipline'}
        ]
        mock_fetch.return_value = sample_data
        
        response, status_code, headers = dev_v2_get_master_discipline(mock_flask_request_get)
        
        assert status_code == 200
        assert headers['Content-Type'] == 'application/json'
        data = json.loads(response)
        assert data['count'] == 1

    @patch('dev_v2_getMasteDiscipline.main.fetch_master_discipline')
    def test_get_master_discipline_database_error(self, mock_fetch, mock_flask_request_get):
        """Test GET request with database error."""
        mock_fetch.side_effect = psycopg2.Error("Database error")
        
        response, status_code, headers = dev_v2_get_master_discipline(mock_flask_request_get)
        
        assert status_code == 500
        data = json.loads(response)
        assert 'error' in data

    def test_options_request(self, mock_flask_request_options):
        """Test CORS preflight OPTIONS request."""
        response, status_code, headers = dev_v2_get_master_discipline(mock_flask_request_options)
        
        assert status_code == 204
        assert headers['Access-Control-Allow-Origin'] == '*'

