import csv
import sqlite3
import os


def import_data(file_path):
     with open(file_path, 'r') as file:
        reader = csv.reader(file)
        headers = next(reader)

        # Tworzenie połączenia do bazy danych SQLite
        conn = sqlite3.connect('my_database.db')
        cursor = conn.cursor()

        # Tworzenie tabeli
        create_table_query = f'CREATE TABLE IF NOT EXISTS my_table ({", ".join(headers)})'
        cursor.execute(create_table_query)

        # Wstawianie danych
        for row in reader:
            insert_row_query = f'INSERT INTO my_table VALUES ({", ".join(["?"] * len(row))})'
            cursor.execute(insert_row_query, row)

        # Zatwierdzanie zmian i zamykanie połączenia
        conn.commit()
        conn.close()

        success_message = 'Dane zostały pomyślnie zaimportowane do bazy danych.'
        return success_message


def generate_sql_file(file_path):
    table_name = "my_table"  # Nazwa docelowej tabeli

    # Wczytaj dane z pliku CSV
    with open(file_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        headers = next(csv_reader)  # Nagłówki kolumn
        data_rows = list(csv_reader)  # Wiersze danych

    # Wygeneruj polecenie CREATE TABLE
    create_table_query = f"CREATE TABLE {table_name} (\n"
    for header in headers:
        create_table_query += f"    {header} TEXT,\n"  # Przykładowy typ danych TEXT, można dostosować do rzeczywistych typów
    create_table_query = create_table_query.rstrip(",\n") + "\n);"

    # Wygeneruj polecenia INSERT
    insert_queries = []
    for row in data_rows:
        values = "', '".join(row)  # Wartości w formacie 'value1', 'value2', ...
        insert_query = f"INSERT INTO {table_name} VALUES ('{values}');"
        insert_queries.append(insert_query)

    # Utwórz ścieżkę do pliku SQL w katalogu głównym
    sql_file_path = os.path.join(os.getcwd(), "output.sql")

    # Zapisz polecenia SQL do pliku
    with open(sql_file_path, 'w') as sql_file:
        sql_file.write(create_table_query + "\n\n")
        for insert_query in insert_queries:
            sql_file.write(insert_query + "\n")

    return sql_file_path

# Wywołanie funkcji generującej plik SQL
#sql_file_path = generate_sql_file('input.csv')
