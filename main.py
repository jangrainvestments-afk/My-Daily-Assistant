
import sqlite3
from pathlib import Path
from datetime import datetime

DATABASE = Path(__file__).parent / "schedule.db"


def initialize_database():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                event_date TEXT NOT NULL,
                event_time TEXT NOT NULL,
                location TEXT DEFAULT ''
            )
        """)


def add_event():
    title = input("Event name: ").strip()
    date = input("Date (YYYY-MM-DD): ").strip()
    time = input("Time (HH:MM, 24-hour format): ").strip()
    location = input("Location: ").strip()

    if not title:
        print("Event name cannot be empty.")
        return

    try:
        datetime.strptime(date, "%Y-%m-%d")
        datetime.strptime(time, "%H:%M")
    except ValueError:
        print("Invalid date or time. Please try again.")
        return

    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            INSERT INTO events
            (title, event_date, event_time, location)
            VALUES (?, ?, ?, ?)
        """, (title, date, time, location))

    print("Event saved successfully!")


def view_events():
    with sqlite3.connect(DATABASE) as conn:
        events = conn.execute("""
            SELECT id, title, event_date, event_time, location
            FROM events
            ORDER BY event_date, event_time
        """).fetchall()

    print("\n--- Your Schedule ---")
    if not events:
        print("No events added yet.")
    else:
        for event_id, title, date, time, location in events:
            print(f"{date} {time} | {title} | {location}")


def main():
    initialize_database()
    print("\n=== My Daily Assistant ===")

    while True:
        print("\n1. Add event")
        print("2. View schedule")
        print("3. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_event()
        elif choice == "2":
            view_events()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()
