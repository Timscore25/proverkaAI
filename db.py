import sqlite3
import os
import uuid

class DBConnection:
    def __init__(self, db_name='database.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        # Table for token management
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tokens (
                ip TEXT PRIMARY KEY,
                token_count INTEGER DEFAULT 100
            )
        ''')

        # Table for request logs
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS request_logs (
                request_id TEXT PRIMARY KEY,
                ip TEXT,
                text TEXT,
                result TEXT,
                fake_percantage TEXT,
                TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()

    # --- Token Functions ---

    def get_tokens(self, user_ip):
        self.cursor.execute('SELECT token_count FROM tokens WHERE ip = ?', (user_ip,))
        row = self.cursor.fetchone()
        if row:
            return row[0]
        else:
            self.cursor.execute('INSERT INTO tokens (ip, token_count) VALUES (?, ?)', (user_ip, 100))
            self.conn.commit()
            return 100

    def set_tokens(self, user_ip, tokens):
        self.cursor.execute('''
            INSERT INTO tokens (ip, token_count) VALUES (?, ?)
            ON CONFLICT(ip) DO UPDATE SET token_count=excluded.token_count
        ''', (user_ip, tokens))
        self.conn.commit()

    def use_token(self, user_ip, amount=1):
        current_tokens = self.get_tokens(user_ip)
        new_tokens = max(0, current_tokens - amount)
        self.set_tokens(user_ip, new_tokens)
        return new_tokens

    # --- Request Logging Functions ---

    def log_request(self, request_id, user_ip, text, result, fake_percantage):
        self.cursor.execute('''
            INSERT INTO request_logs (request_id, ip, text, result, fake_percantage)
            VALUES (?, ?, ?, ? ,?)
        ''', (request_id, user_ip, text, result, fake_percantage))
        self.conn.commit()
        return request_id

    def get_request(self, request_id = False):
        if request_id:
            self.cursor.execute('SELECT * FROM request_logs WHERE request_id = ?', (request_id,))
            return self.cursor.fetchone()
        else:
            self.cursor.execute('SELECT * FROM request_logs')
            return self.cursor.fetchall()
        
    def get_usage(self):
        self.cursor.execute('SELECT COUNT(request_id) FROM request_logs')
        return self.cursor.fetchone()[0]

    def close(self):
        self.conn.close()
