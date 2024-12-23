import subprocess
import os
import re
import logging
import sqlite3


def execute_cmd(cmd):
    logging.info('Execute command:%s' % " ".join(cmd))
    completed_process = subprocess.run(cmd, capture_output=True, shell=False, check=True)
    return completed_process.returncode


def execute_script(cmd):
    logging.info('Execute command:%s' % " ".join(cmd))
    process = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while process.poll() is None:
        line = process.stdout.readline().strip()
        if line:
            logging.debug(line)
    return process.returncode


def check_result_file(out_path):
    files = os.listdir(out_path)
    newest_file = None
    re_match_exp = r"^performance_comparison_result_\d{1,20}\.xlsx"
    for file_name in files:
        if re.match(re_match_exp, file_name):
            file_time = file_name.split(".")[0].split("_")[-1]
            if not newest_file or file_time > newest_file.split(".")[0].split("_")[-1]:
                newest_file = file_name

    return newest_file


def select_count(db_path: str, query: str):
    """
    Execute a SQL query to count the number of records in the database.
    """
    conn, cursor = create_connect_db(db_path)
    cursor.execute(query)
    count = cursor.fetchone()
    destroy_db_connect(conn, cursor)
    return count[0]


def select_by_query(db_path: str, query: str, db_class):
    """
    Execute a SQL query and return the first record as an instance of db_class.
    """
    conn, cursor = create_connect_db(db_path)
    cursor.execute(query)
    rows = cursor.fetchall()
    dbs = [db_class(*row) for row in rows]
    destroy_db_connect(conn, cursor)
    return dbs[0]


def create_connect_db(db_file: str) -> tuple:
    """
    Create a connection to the SQLite database.
    """
    try:
        conn = sqlite3.connect(db_file)
        curs = conn.cursor()
        return conn, curs
    except sqlite3.Error as e:
        logging.error("Unable to connect to database: %s", e)
        return None, None


def destroy_db_connect(conn: any, curs: any) -> None:
    """
    Close the database connection and cursor.
    """
    try:
        if isinstance(curs, sqlite3.Cursor):
            curs.close()
    except sqlite3.Error as err:
        logging.error("%s", err)
    try:
        if isinstance(conn, sqlite3.Connection):
            conn.close()
    except sqlite3.Error as err:
        logging.error("%s", err)
