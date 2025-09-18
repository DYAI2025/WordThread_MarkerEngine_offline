import sqlite3
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
import os
import tempfile
from pathlib import Path

class SQLiteHandler:
    """Handle SQLite database operations for WordThread Marker-Engine"""
    
    def __init__(self, db_path: str):
        """Initialize SQLite handler with database path"""
        self.db_path = db_path
        self.connection = None
        self.tables_info = {}
        
    def connect(self) -> bool:
        """Connect to SQLite database"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            return True
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from database"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
    
    def get_table_list(self) -> List[str]:
        """Get list of tables in the database"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            return tables
        except sqlite3.Error as e:
            print(f"Error getting table list: {e}")
            return []
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema information for a specific table"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({table_name});")
            
            schema = []
            for row in cursor.fetchall():
                schema.append({
                    'column_id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'not_null': bool(row[3]),
                    'default_value': row[4],
                    'primary_key': bool(row[5])
                })
            
            return schema
        except sqlite3.Error as e:
            print(f"Error getting table schema for {table_name}: {e}")
            return []
    
    def get_table_row_count(self, table_name: str) -> int:
        """Get row count for a specific table"""
        if not self.connection:
            return 0
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            return cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"Error getting row count for {table_name}: {e}")
            return 0
    
    def extract_table_data(self, table_name: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Extract data from a specific table"""
        if not self.connection:
            return []
        
        try:
            query = f"SELECT * FROM {table_name}"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            # Convert rows to dictionaries
            rows = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                rows.append(row_dict)
            
            return rows
        except sqlite3.Error as e:
            print(f"Error extracting data from {table_name}: {e}")
            return []
    
    def extract_data(self, row_limit: int = 10000) -> Dict[str, Any]:
        """Extract all relevant data from the database"""
        if not self.connect():
            return {'error': 'Failed to connect to database'}
        
        try:
            extracted_data = {
                'database_info': {
                    'path': self.db_path,
                    'size_bytes': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                },
                'tables': {},
                'schema_info': {},
                'extraction_metadata': {
                    'row_limit': row_limit,
                    'extracted_tables': []
                }
            }
            
            # Get all tables
            tables = self.get_table_list()
            
            for table_name in tables:
                # Get schema information
                schema = self.get_table_schema(table_name)
                extracted_data['schema_info'][table_name] = schema
                
                # Get row count
                row_count = self.get_table_row_count(table_name)
                
                # Extract data (with limit)
                table_data = self.extract_table_data(table_name, limit=row_limit)
                
                extracted_data['tables'][table_name] = table_data
                extracted_data['extraction_metadata']['extracted_tables'].append({
                    'table_name': table_name,
                    'total_rows': row_count,
                    'extracted_rows': len(table_data),
                    'columns': len(schema),
                    'truncated': row_count > row_limit
                })
            
            return extracted_data
            
        except Exception as e:
            return {'error': f'Data extraction failed: {str(e)}'}
        finally:
            self.disconnect()
    
    def validate_marker_schema(self) -> Dict[str, Any]:
        """Validate database schema against expected marker structure"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'schema_compliance': {}
        }
        
        if not self.connect():
            validation_result['valid'] = False
            validation_result['errors'].append('Failed to connect to database')
            return validation_result
        
        try:
            # Expected table schemas
            expected_schemas = {
                'hits': {
                    'required_columns': ['id', 'marker_id', 'ts'],
                    'optional_columns': ['conv', 'payload']
                },
                'messages': {
                    'required_columns': ['id', 'timestamp'],
                    'optional_columns': ['conversation_id', 'content']
                },
                'aggregates': {
                    'required_columns': [],
                    'optional_columns': ['id', 'type', 'value', 'timestamp']
                },
                'scores': {
                    'required_columns': [],
                    'optional_columns': ['id', 'marker_id', 'score', 'timestamp']
                },
                'drift_axes': {
                    'required_columns': [],
                    'optional_columns': ['id', 'axis_name', 'value', 'timestamp']
                },
                'provenance': {
                    'required_columns': [],
                    'optional_columns': ['id', 'source', 'data', 'timestamp']
                }
            }
            
            tables = self.get_table_list()
            
            # Check each expected table
            for table_name, expected_schema in expected_schemas.items():
                table_validation = {
                    'exists': table_name in tables,
                    'required_columns_present': [],
                    'missing_required_columns': [],
                    'optional_columns_present': [],
                    'additional_columns': []
                }
                
                if table_name in tables:
                    schema = self.get_table_schema(table_name)
                    actual_columns = [col['name'] for col in schema]
                    
                    # Check required columns
                    for req_col in expected_schema['required_columns']:
                        if req_col in actual_columns:
                            table_validation['required_columns_present'].append(req_col)
                        else:
                            table_validation['missing_required_columns'].append(req_col)
                            validation_result['errors'].append(
                                f"Missing required column '{req_col}' in table '{table_name}'"
                            )
                    
                    # Check optional columns
                    for opt_col in expected_schema['optional_columns']:
                        if opt_col in actual_columns:
                            table_validation['optional_columns_present'].append(opt_col)
                    
                    # Identify additional columns
                    expected_all = set(expected_schema['required_columns'] + expected_schema['optional_columns'])
                    actual_set = set(actual_columns)
                    additional = actual_set - expected_all
                    table_validation['additional_columns'] = list(additional)
                    
                    # Check for missing required columns
                    if table_validation['missing_required_columns']:
                        validation_result['valid'] = False
                
                else:
                    # Table doesn't exist
                    if expected_schema['required_columns']:  # Only warn for tables with required columns
                        validation_result['warnings'].append(f"Expected table '{table_name}' not found")
                
                validation_result['schema_compliance'][table_name] = table_validation
            
            # Additional validations
            self._validate_data_types(validation_result)
            self._validate_relationships(validation_result)
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Schema validation failed: {str(e)}")
        finally:
            self.disconnect()
        
        return validation_result
    
    def _validate_data_types(self, validation_result: Dict[str, Any]):
        """Validate data types in key columns"""
        try:
            # Check hits table data types
            if 'hits' in validation_result['schema_compliance'] and validation_result['schema_compliance']['hits']['exists']:
                hits_schema = self.get_table_schema('hits')
                
                for column in hits_schema:
                    col_name = column['name']
                    col_type = column['type'].upper()
                    
                    if col_name == 'ts':
                        if 'INT' not in col_type and 'REAL' not in col_type and 'NUMERIC' not in col_type:
                            validation_result['warnings'].append(
                                f"Timestamp column 'ts' has unexpected type '{col_type}', expected numeric"
                            )
                    
                    elif col_name == 'marker_id':
                        if 'TEXT' not in col_type and 'VARCHAR' not in col_type:
                            validation_result['warnings'].append(
                                f"Marker ID column has unexpected type '{col_type}', expected text"
                            )
        
        except Exception as e:
            validation_result['warnings'].append(f"Data type validation failed: {str(e)}")
    
    def _validate_relationships(self, validation_result: Dict[str, Any]):
        """Validate relationships between tables"""
        try:
            # Check if conversation IDs in hits match messages
            if (validation_result['schema_compliance'].get('hits', {}).get('exists') and 
                validation_result['schema_compliance'].get('messages', {}).get('exists')):
                
                # Sample check for conversation ID consistency
                hits_sample = self.extract_table_data('hits', limit=100)
                messages_sample = self.extract_table_data('messages', limit=100)
                
                hits_convs = set(hit.get('conv') for hit in hits_sample if hit.get('conv'))
                msg_convs = set(msg.get('conversation_id') for msg in messages_sample if msg.get('conversation_id'))
                
                if hits_convs and msg_convs:
                    overlap = len(hits_convs.intersection(msg_convs))
                    if overlap == 0:
                        validation_result['warnings'].append(
                            "No conversation ID overlap found between hits and messages tables"
                        )
        
        except Exception as e:
            validation_result['warnings'].append(f"Relationship validation failed: {str(e)}")
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the database"""
        if not self.connect():
            return {'error': 'Failed to connect to database'}
        
        try:
            summary = {
                'database_info': {
                    'path': self.db_path,
                    'size_bytes': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                },
                'table_summary': {},
                'data_quality': {},
                'marker_analysis': {}
            }
            
            tables = self.get_table_list()
            
            for table_name in tables:
                row_count = self.get_table_row_count(table_name)
                schema = self.get_table_schema(table_name)
                
                summary['table_summary'][table_name] = {
                    'row_count': row_count,
                    'column_count': len(schema),
                    'columns': [col['name'] for col in schema]
                }
                
                # Detailed analysis for hits table
                if table_name == 'hits' and row_count > 0:
                    hits_analysis = self._analyze_hits_table()
                    summary['marker_analysis'] = hits_analysis
            
            return summary
            
        except Exception as e:
            return {'error': f'Summary generation failed: {str(e)}'}
        finally:
            self.disconnect()
    
    def _analyze_hits_table(self) -> Dict[str, Any]:
        """Analyze hits table for marker patterns"""
        analysis = {
            'total_hits': 0,
            'unique_markers': 0,
            'marker_categories': {},
            'time_range': {},
            'conversation_stats': {}
        }
        
        try:
            # Get sample data for analysis
            hits_data = self.extract_table_data('hits', limit=5000)
            
            if hits_data:
                analysis['total_hits'] = len(hits_data)
                
                # Analyze markers
                markers = set()
                categories = {}
                conversations = set()
                timestamps = []
                
                for hit in hits_data:
                    if 'marker_id' in hit and hit['marker_id']:
                        marker_id = hit['marker_id']
                        markers.add(marker_id)
                        
                        # Categorize marker
                        if marker_id.startswith('ATO_'):
                            category = 'ATO'
                        elif marker_id.startswith('SEM_'):
                            category = 'SEM'
                        elif marker_id.startswith('CLU_'):
                            category = 'CLU'
                        elif marker_id.startswith('MEMA_'):
                            category = 'MEMA'
                        else:
                            category = 'OTHER'
                        
                        categories[category] = categories.get(category, 0) + 1
                    
                    if 'conv' in hit and hit['conv']:
                        conversations.add(hit['conv'])
                    
                    if 'ts' in hit and hit['ts']:
                        try:
                            timestamps.append(float(hit['ts']))
                        except (ValueError, TypeError):
                            pass
                
                analysis['unique_markers'] = len(markers)
                analysis['marker_categories'] = categories
                analysis['conversation_stats'] = {
                    'unique_conversations': len(conversations),
                    'avg_hits_per_conversation': len(hits_data) / len(conversations) if conversations else 0
                }
                
                if timestamps:
                    analysis['time_range'] = {
                        'start_timestamp': min(timestamps),
                        'end_timestamp': max(timestamps),
                        'span_hours': (max(timestamps) - min(timestamps)) / 3600
                    }
        
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
    
    def export_to_csv(self, table_name: str, output_path: str) -> bool:
        """Export table data to CSV file"""
        if not self.connect():
            return False
        
        try:
            # Extract all data from table
            data = self.extract_table_data(table_name)
            
            if data:
                df = pd.DataFrame(data)
                df.to_csv(output_path, index=False)
                return True
            
            return False
            
        except Exception as e:
            print(f"CSV export failed: {e}")
            return False
        finally:
            self.disconnect()
    
    def query_custom(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Execute custom SQL query"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            rows = []
            for row in cursor.fetchall():
                rows.append(dict(row))
            
            return rows
            
        except sqlite3.Error as e:
            print(f"Query execution failed: {e}")
            return []
    
    def get_marker_statistics(self) -> Dict[str, Any]:
        """Get detailed marker statistics"""
        if not self.connect():
            return {}
        
        try:
            stats = {
                'marker_frequency': {},
                'temporal_distribution': {},
                'conversation_distribution': {}
            }
            
            # Marker frequency
            marker_query = """
                SELECT marker_id, COUNT(*) as frequency 
                FROM hits 
                WHERE marker_id IS NOT NULL 
                GROUP BY marker_id 
                ORDER BY frequency DESC
                LIMIT 50
            """
            
            marker_results = self.query_custom(marker_query)
            stats['marker_frequency'] = {row['marker_id']: row['frequency'] for row in marker_results}
            
            # Temporal distribution (by hour)
            temporal_query = """
                SELECT 
                    strftime('%H', datetime(ts, 'unixepoch')) as hour,
                    COUNT(*) as frequency
                FROM hits 
                WHERE ts IS NOT NULL
                GROUP BY hour
                ORDER BY hour
            """
            
            temporal_results = self.query_custom(temporal_query)
            stats['temporal_distribution'] = {int(row['hour']): row['frequency'] for row in temporal_results}
            
            # Conversation distribution
            conv_query = """
                SELECT conv, COUNT(*) as frequency 
                FROM hits 
                WHERE conv IS NOT NULL 
                GROUP BY conv 
                ORDER BY frequency DESC
                LIMIT 20
            """
            
            conv_results = self.query_custom(conv_query)
            stats['conversation_distribution'] = {row['conv']: row['frequency'] for row in conv_results}
            
            return stats
            
        except Exception as e:
            return {'error': str(e)}
        finally:
            self.disconnect()

def create_test_database(db_path: str) -> bool:
    """Create a test SQLite database with sample marker data"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create hits table
        cursor.execute('''
            CREATE TABLE hits (
                id TEXT PRIMARY KEY,
                marker_id TEXT NOT NULL,
                ts REAL NOT NULL,
                conv TEXT,
                payload TEXT
            )
        ''')
        
        # Create messages table
        cursor.execute('''
            CREATE TABLE messages (
                id TEXT PRIMARY KEY,
                timestamp REAL NOT NULL,
                conversation_id TEXT,
                content TEXT
            )
        ''')
        
        # Create sample data
        import time
        current_time = time.time()
        
        sample_hits = [
            ('hit_001', 'ATO_GREETING', current_time - 3600, 'conv_001', '{"confidence": 0.95}'),
            ('hit_002', 'SEM_POSITIVE_SENTIMENT', current_time - 3500, 'conv_001', '{"confidence": 0.87}'),
            ('hit_003', 'CLU_ENGAGEMENT', current_time - 3400, 'conv_001', '{"confidence": 0.92}'),
            ('hit_004', 'ATO_QUESTION', current_time - 3000, 'conv_002', '{"confidence": 0.88}'),
            ('hit_005', 'MEMA_TOPIC_SHIFT', current_time - 2800, 'conv_002', '{"confidence": 0.79}')
        ]
        
        cursor.executemany(
            'INSERT INTO hits (id, marker_id, ts, conv, payload) VALUES (?, ?, ?, ?, ?)',
            sample_hits
        )
        
        sample_messages = [
            ('msg_001', current_time - 3600, 'conv_001', 'Hello there!'),
            ('msg_002', current_time - 3500, 'conv_001', 'How are you doing today?'),
            ('msg_003', current_time - 3000, 'conv_002', 'What is the weather like?'),
            ('msg_004', current_time - 2800, 'conv_002', 'Actually, let me ask about something else.')
        ]
        
        cursor.executemany(
            'INSERT INTO messages (id, timestamp, conversation_id, content) VALUES (?, ?, ?, ?)',
            sample_messages
        )
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Test database creation failed: {e}")
        return False
