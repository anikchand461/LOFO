import sqlite3

def get_owners_from_db():
    try:
        # Connect to the database
        conn = sqlite3.connect('lofo.db')
        cursor = conn.cursor()

        # Query to fetch owners (adjust table/column names as needed)
        cursor.execute("SELECT id, desc FROM owners")
        rows = cursor.fetchall()

        # Format results into a list of dictionaries
        owners = [{"id": row[0], "desc": row[1]} for row in rows]

        return owners
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

# Example usage
if __name__ == "__main__":
    owners_list = get_owners_from_db()
    print(owners_list)