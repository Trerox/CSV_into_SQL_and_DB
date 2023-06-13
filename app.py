

from flask import Flask, render_template, request, jsonify, json, redirect, url_for
import os
import pandas as pd

from sql import import_data, generate_sql_file

app = Flask(__name__)

# Ścieżka do folderu uploads
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        files = request.files.getlist('files')
        error_message = None
        success_message = None

        for file in files:
            filename = file.filename
            if not allowed_file(filename):
                error_message = 'Nieprawidłowy format pliku. Dozwolone rozszerzenie to .csv.'
                break

            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            try:
                # Wykrywanie typów danych
                data_types = detect_data_types(file_path)
                print(data_types)  # Wyświetlenie typów danych dla każdej kolumny
                save_data_types(data_types)

                import_data(file_path)  # Importowanie danych do bazy SQLite

                # Generowanie pliku SQL

                generate_sql_file(file_path)

            except pd.errors.ParserError:
                error_message = 'Nieprawidłowy format pliku CSV'
                break

        if error_message:
            return jsonify({'error_message': error_message})
        else:
            success_message = 'Pliki zostały pomyślnie przesłane.'
            return jsonify({'success_message': success_message})

    return render_template('upload.html')


@app.route('/data_sample', methods=['GET', 'POST'])
def data_sample():
    uploads_dir = app.config['UPLOAD_FOLDER']

    if not os.path.exists(uploads_dir):
        return "Brak plików do wyświetlenia"

    file_list = os.listdir(uploads_dir)

    if len(file_list) == 0:
        return "Brak plików do wyświetlenia"

    file_name = file_list[0]
    file_path = os.path.join(uploads_dir, file_name)

    if request.method == 'POST':
        column_info = json.loads(request.form['column_info'])

        # Aktualizuj typy danych przy użyciu funkcji update_data_types
        update_data_types(file_path, column_info)

    # Wywołaj funkcję get_table_data, aby otrzymać próbkę danych
    sample_data = get_table_data(file_path)

    if sample_data is None:
        return "Błąd podczas odczytu pliku CSV"

    column_names = sample_data.columns.tolist()

    # Wywołaj funkcję detect_data_types_from_file, aby otrzymać zaproponowane typy danych dla każdej kolumny
    column_info = []
    data_types = load_data_types()
    for column_name in column_names:
        column_type = data_types.get(column_name, 'unknown')
        suggested_types = ['integer', 'float', 'text', 'unknown']
        column_info.append((column_name, column_type, suggested_types))

    sample_data_list = sample_data.to_dict(orient='records')
    return render_template('data_sample.html', column_info=column_info, sample_data=sample_data_list)

@app.route('/search_table', methods=['GET', 'POST'])
def search_table():
    uploads_dir = app.config['UPLOAD_FOLDER']

    if not os.path.exists(uploads_dir):
        return "Brak plików do wyświetlenia"

    file_list = os.listdir(uploads_dir)

    if len(file_list) == 0:
        return "Brak plików do wyświetlenia"

    file_name = file_list[0]
    file_path = os.path.join(uploads_dir, file_name)

    table_data = get_table_data(file_path)

    if table_data is None:
        return "Błąd podczas odczytu pliku CSV"

    column_names = table_data.columns.tolist()
    search_results = []

    if request.method == 'POST':
        search_query = request.form['search_query']
        # Przeszukaj tabelę w poszukiwaniu pasujących wierszy
        for index, row in table_data.iterrows():
            for column_name in column_names:
                # Konwertuj wartość w kolumnie na napis i sprawdź, czy występuje dopasowanie
                if str(search_query) in str(row[column_name]):
                    search_results.append((column_name, [row.tolist()]))

    return render_template('search_table.html', column_names=column_names, table_data=table_data,
                           search_results=search_results)


def get_table_data(file_path):
    try:
        # Wczytaj plik CSV przy użyciu biblioteki pandas
        table_data = pd.read_csv(file_path)
        return table_data
    except Exception as e:
        print(f"Błąd odczytu pliku CSV: {str(e)}")
        return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'

def detect_data_types(file_path):
    # Wczytanie pliku CSV jako DataFrame
    df = get_table_data(file_path)

    # Słownik do przechowywania typów danych dla każdej kolumny
    data_types = {}

    # Iteracja po kolumnach
    for column in df.columns:
        values = df[column].tolist()  # Pobranie wartości dla danej kolumny
        column_data_type = detect_column_data_type(values)  # Wywołanie funkcji do określenia typu danych
        data_types[column] = column_data_type  # Dodanie typu danych do słownika

    return data_types

def detect_column_data_type(values):
    # Sprawdzenie typu danych dla danej kolumny
    if all(isinstance(value, int) for value in values):
        return 'integer'
    elif all(isinstance(value, float) for value in values):
        return 'float'
    elif all(isinstance(value, str) for value in values):
        return 'text'
    else:
        return 'unknown'


def update_data_types(file_path, column_info):
    data = pd.read_csv(file_path)

    # Wczytaj istniejące typy danych z pliku data_types.json
    data_types = load_data_types()

    # Sprawdź, czy plik jest już w słowniku data_types
    if file_path not in data_types:
        data_types[file_path] = {}

    for column_name, data_type in column_info.items():
        if data_type == "text":
            data[column_name] = data[column_name].astype(object)
        elif data_type == "float":
            data[column_name] = data[column_name].astype(float)
        elif data_type == "integer":
            data[column_name] = data[column_name].astype(int)

        # Aktualizuj słownik przechowujący typy danych dla danego pliku
        data_types[file_path][column_name] = data_type

    data.to_csv(file_path, index=False)

    # Zapisz zmiany w pliku data_types.json
    save_data_types(data_types, 'data_types.json')


def load_data_types():
    try:
        with open('data_types.json', 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data_types(data_types, file_path):
    with open(file_path, 'w') as file:
        json.dump(data_types, file)


if __name__ == '__main__':
    app.run(debug=True)
