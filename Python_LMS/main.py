import json
import sqlite3
import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom
from abc import ABC, abstractmethod

# ==========================================
# 1. Interfaces (Dependency Inversion & Interface Segregation)
# ==========================================

class DataLoader(ABC):
    @abstractmethod
    def load(self, filepath: str) -> list:
        pass

class DataExporter(ABC):
    @abstractmethod
    def export(self, data: dict, filename: str):
        pass

# ==========================================
# 2. Concrete Implementations (Liskov Substitution & Open/Closed)
# ==========================================

class JsonLoader(DataLoader):
    def load(self, filepath: str) -> list:
        with open(filepath, 'r') as file:
            return json.load(file)

class JsonExporter(DataExporter):
    def export(self, data: dict, filename: str):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4, default=str)

class XmlExporter(DataExporter):
    def export(self, data: dict, filename: str):
        root = ET.Element("Results")
        for report_name, rows in data.items():
            report_elem = ET.SubElement(root, report_name)
            for row in rows:
                row_elem = ET.SubElement(report_elem, "Item")
                for key, val in row.items():
                    child = ET.SubElement(row_elem, key)
                    child.text = str(val)
        
        # Pretty print XML
        xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="    ")
        with open(filename, "w") as f:
            f.write(xmlstr)

# ==========================================
# 3. Database Manager (Single Responsibility)
# ==========================================

class DatabaseManager:
    def __init__(self, db_name: str = ":memory:"):
        # Using an in-memory database for blazing fast execution
        self.conn = sqlite3.connect(db_name)
        # Configure connection to return dictionaries instead of tuples
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._setup_schema()

    def _setup_schema(self):
        # Create Tables
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                room INTEGER NOT NULL,
                birthday TEXT NOT NULL,
                sex TEXT NOT NULL,
                FOREIGN KEY (room) REFERENCES rooms(id) ON DELETE CASCADE
            );
            
            -- OPTIMIZATION: Indexes for faster JOINs and Aggregations
            CREATE INDEX IF NOT EXISTS idx_student_room ON students(room);
            CREATE INDEX IF NOT EXISTS idx_student_room_sex ON students(room, sex);
        """)
        self.conn.commit()

    def insert_rooms(self, rooms: list):
        query = "INSERT OR IGNORE INTO rooms (id, name) VALUES (?, ?)"
        data = [(r['id'], r['name']) for r in rooms]
        self.cursor.executemany(query, data)
        self.conn.commit()

    def insert_students(self, students: list):
        query = "INSERT OR IGNORE INTO students (id, name, room, birthday, sex) VALUES (?, ?, ?, ?, ?)"
        data = [(s['id'], s['name'], s['room'], s['birthday'], s['sex']) for s in students]
        self.cursor.executemany(query, data)
        self.conn.commit()

    def execute_read_query(self, query: str) -> list:
        self.cursor.execute(query)
        return [dict(row) for row in self.cursor.fetchall()]

    def close(self):
        self.cursor.close()
        self.conn.close()

# ==========================================
# 4. Query Executor (Math at DB Level)
# ==========================================

class ReportGenerator:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_rooms_with_student_count(self) -> list:
        query = """
            SELECT r.name, COUNT(s.id) as student_count
            FROM rooms r
            LEFT JOIN students s ON r.id = s.room
            GROUP BY r.id, r.name;
        """
        return self.db.execute_read_query(query)

    def get_rooms_smallest_avg_age(self) -> list:
        # SQLite uses julianday for date math
        query = """
            SELECT r.name, 
                   AVG((julianday('now') - julianday(s.birthday)) / 365.2425) as avg_age
            FROM rooms r
            JOIN students s ON r.id = s.room
            GROUP BY r.id, r.name
            ORDER BY avg_age ASC
            LIMIT 5;
        """
        return self.db.execute_read_query(query)

    def get_rooms_largest_age_difference(self) -> list:
        query = """
            SELECT r.name, 
                   MAX((julianday('now') - julianday(s.birthday)) / 365.2425) - 
                   MIN((julianday('now') - julianday(s.birthday)) / 365.2425) as age_diff
            FROM rooms r
            JOIN students s ON r.id = s.room
            GROUP BY r.id, r.name
            ORDER BY age_diff DESC
            LIMIT 5;
        """
        return self.db.execute_read_query(query)

    def get_mixed_sex_rooms(self) -> list:
        query = """
            SELECT r.name
            FROM rooms r
            JOIN students s ON r.id = s.room
            GROUP BY r.id, r.name
            HAVING COUNT(DISTINCT s.sex) > 1;
        """
        return self.db.execute_read_query(query)

# ==========================================
# 5. Main Orchestrator
# ==========================================

def main():
    parser = argparse.ArgumentParser(description="Process hostel student and room data.")
    parser.add_argument("--students", required=True, help="Path to students JSON file")
    parser.add_argument("--rooms", required=True, help="Path to rooms JSON file")
    parser.add_argument("--format", required=True, choices=['json', 'xml'], help="Output format")
    
    args = parser.parse_args()

    # Instantiate our specific dependencies (Dependency Injection)
    loader = JsonLoader() 
    exporter = JsonExporter() if args.format == 'json' else XmlExporter()
    db = DatabaseManager() # Uses fast in-memory DB
    
    try:
        print("Loading files...")
        rooms_data = loader.load(args.rooms)
        students_data = loader.load(args.students)

        print("Writing to database & building indexes...")
        db.insert_rooms(rooms_data)
        db.insert_students(students_data)

        print("Executing queries...")
        reports = ReportGenerator(db)
        
        results = {
            "StudentCounts": reports.get_rooms_with_student_count(),
            "SmallestAverageAge": reports.get_rooms_smallest_avg_age(),
            "LargestAgeDifference": reports.get_rooms_largest_age_difference(),
            "MixedSexRooms": reports.get_mixed_sex_rooms()
        }

        print("Exporting data...")
        output_filename = f"report.{args.format}"
        exporter.export(results, output_filename)
        
        print(f"Success! Results saved to '{output_filename}'.")

    finally:
        db.close()

if __name__ == "__main__":
    main()