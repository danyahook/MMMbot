import sqlite3


class DBHelper:
    def __init__(self, dbname="todo.sql"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname, check_same_thread=False)

    def add_user(self, user_id, id_hash, user_name, status):
        stmt = "INSERT INTO users (user_id, id_hash, user_name, status) VALUES (?, ?, ?, ?)"
        args = (user_id, id_hash, user_name, status)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def rate_update_by_hid(self, id_hash):
        stmt = "UPDATE users SET rate = rate + 1, balance = balance + 1 WHERE id_hash = (?)"
        args = (id_hash,)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_info(self, user_id):
        stmt = "SELECT * FROM users WHERE user_id = (?)"
        args = (user_id,)
        return [x for x in self.conn.execute(stmt, args)]

    def get_info_all(self):
        stmt = "SELECT * FROM users"
        return [x for x in self.conn.execute(stmt)]

    def get_user_by_hid(self, id_hash):
        stmt = "SELECT * FROM users WHERE id_hash = (?)"
        args = (id_hash,)
        return [x for x in self.conn.execute(stmt, args)]

    def get_users_rate(self):
        stmt = "SELECT sum(rate) FROM users"
        return [x[-1] for x in self.conn.execute(stmt)]

    def get_valid_users(self):
        stmt = "SELECT * FROM users WHERE status = 1"
        return [x for x in self.conn.execute(stmt)]

    def get_between_time(self, between):
        stmt = "SELECT * FROM users WHERE reg_time >= datetime('now', ?)"
        args = (between,)
        return [x for x in self.conn.execute(stmt, args)]

    def is_valid(self, id_hash):
        stmt = "UPDATE users SET status = 1 WHERE id_hash = (?)"
        args = (id_hash,)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def is_valid_by_id(self, uid, status):
        stmt = f"UPDATE users SET status = {status} WHERE id = (?)"
        args = (uid,)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def btc_address(self, id_hash, btc_adr):
        stmt = f"UPDATE users SET address = '{btc_adr}' WHERE user_id = (?)"
        args = (id_hash,)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_balance_by_id(self, uid):
        stmt = "SELECT user_id, user_name, balance FROM users WHERE id = (?)"
        args = (uid,)
        return [x for x in self.conn.execute(stmt, args)]

    def capitalization(self, value):
        stmt = f"UPDATE users SET balance = balance * {value} WHERE invest = 0"
        self.conn.execute(stmt)
        self.conn.commit()

    def capitalization_invest(self, value):
        stmt = f"UPDATE users SET balance = balance * {value} WHERE invest = 1"
        self.conn.execute(stmt)
        self.conn.commit()

    def set_balance_by_id(self, id_hash, balance):
        stmt = f"UPDATE users SET balance = '{balance}' WHERE user_id = (?)"
        args = (id_hash,)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def set_invest(self, uid, status):
        stmt = f"UPDATE users SET invest = {status} WHERE id = (?)"
        args = (uid,)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def admin(self):
        stmt = "SELECT password FROM admin WHERE username='admin'"
        return [x[-1] for x in self.conn.execute(stmt)]

    def get_percent(self, status):
        stmt = "SELECT per_count FROM percent WHERE id = (?)"
        args = (status,)
        return [x[-1] for x in self.conn.execute(stmt, args)]

    def get_btn_text(self, bit):
        stmt = "SELECT btn_text FROM items WHERE id = (?)"
        args = (bit,)
        return [x[-1] for x in self.conn.execute(stmt, args)]

    def get_user_id_by_id(self, uid):
        stmt = "SELECT user_id FROM users WHERE id = (?)"
        args = (uid,)
        return [x[-1] for x in self.conn.execute(stmt, args)]

    def get_investor_id(self, invest):
        stmt = "SELECT user_id FROM users WHERE invest = (?)"
        args = (invest,)
        return [x[-1] for x in self.conn.execute(stmt, args)]

    def get_valid_id(self, status):
        stmt = "SELECT user_id FROM users WHERE status = (?)"
        args = (status,)
        return [x[-1] for x in self.conn.execute(stmt, args)]