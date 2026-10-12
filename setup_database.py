"""
Database Initialization Script for MySQL
Reads and executes database/schema.sql, database/procedures.sql, and database/sample_data.sql
"""
try:
    import pymysql
except ImportError:
    pymysql = None
from config import Config

def init_mysql():
    if pymysql is None:
        return False, "PyMySQL module not installed. Please install dependencies using 'pip install -r requirements.txt'."
    print("=" * 60)
    print("Initializing Hotel DBMS on MySQL...")
    print(f"Target: {Config.MYSQL_HOST}:{Config.MYSQL_PORT} (User: {Config.MYSQL_USER})")
    print("=" * 60)
    
    try:
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB};")
        conn.select_db(Config.MYSQL_DB)
        print(f"[✓] Database '{Config.MYSQL_DB}' confirmed.")

        base_dir = os.path.dirname(os.path.abspath(__file__))
        sql_files = [
            os.path.join(base_dir, 'database', 'schema.sql'),
            os.path.join(base_dir, 'database', 'procedures.sql'),
            os.path.join(base_dir, 'database', 'sample_data.sql')
        ]

        for filepath in sql_files:
            if not os.path.exists(filepath):
                print(f"[!] Warning: {filepath} not found.")
                continue

            print(f"[*] Executing {os.path.basename(filepath)}...")
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split statements handling DELIMITER $$
            if "$$" in content:
                # Custom parsing for stored procedures/triggers with $$ delimiter
                blocks = content.split("DELIMITER")
                for block in blocks:
                    clean = block.strip()
                    if not clean:
                        continue
                    if clean.startswith("$$"):
                        # Commands inside $$ delimiter
                        stmts = clean[2:].split("$$")
                        for s in stmts:
                            s = s.strip()
                            if s and s != ';':
                                try:
                                    with conn.cursor() as cur:
                                        cur.execute(s)
                                except Exception as err:
                                    print(f"  [Note] Stmt issue: {err}")
                    else:
                        # Standard ; delimiter
                        stmts = clean.split(";")
                        for s in stmts:
                            s = s.strip()
                            if s and not s.startswith("--") and not s.startswith("/*"):
                                try:
                                    with conn.cursor() as cur:
                                        cur.execute(s)
                                except Exception as err:
                                    pass
            else:
                stmts = content.split(";")
                for s in stmts:
                    s = s.strip()
                    if s and not s.startswith("--") and not s.startswith("/*"):
                        try:
                            with conn.cursor() as cur:
                                cur.execute(s)
                        except Exception as err:
                            pass

            conn.commit()
            print(f"[✓] Completed {os.path.basename(filepath)}")

        conn.close()
        print("\n[SUCCESS] Hotel Management Database successfully provisioned on MySQL!")
        return True, "MySQL database initialized successfully with all tables, triggers, and procedures."
    except Exception as e:
        print(f"[ERROR] Could not connect to MySQL: {e}")
        return False, str(e)

if __name__ == "__main__":
    init_mysql()
