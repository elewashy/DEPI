
import os
import random
import csv
import json
import pandas as pd
from faker import Faker
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from datetime import date
from typing import cast

app = Flask(__name__)
fake = Faker()

RECORDS_PER_PAGE = 50

def generate_data(num_records=1000):
    if not os.path.exists('data'):
        os.makedirs('data')
    file_path_txt = 'data/records.txt'
    records = []
    for i in range(1, num_records + 1):
        record = {
            "id": i,
            "name": fake.name(),
            "city": fake.city(),
            "salary": random.randint(30000, 150000),
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=65).strftime('%Y-%m-%d')
        }
        records.append(record)
    with open(file_path_txt, 'w') as f:
        header = "id,name,city,salary,date_of_birth\n"
        f.write(header)
        for record in records:
            f.write(f"{record['id']},{record['name']},{record['city']},{record['salary']},{record['date_of_birth']}\n")
    return f"Successfully created {num_records} records in data/records.txt."

def process_data():
    if not os.path.exists('processed_data'):
        os.makedirs('processed_data')
    file_path_txt_in = 'data/records.txt'
    if not os.path.exists(file_path_txt_in):
        return "Source file not found. Please generate data first."

    df = pd.read_csv(file_path_txt_in)
    
    def assign_salary_category(salary):
        if salary > 100000:
            return 'High'
        elif salary > 60000:
            return 'Medium'
        else:
            return 'Low'
            
    df['salary_category'] = df['salary'].apply(assign_salary_category)

    # Save to different formats
    df.to_csv('processed_data/records_with_salary_col.csv', index=False)
    df.to_csv('processed_data/records_with_salary_col.txt', index=False, sep=',')
    df.to_json('processed_data/records_with_salary_col.json', orient='records', indent=4)
    
    return "Successfully processed data and created new files."

@app.route('/stats')
def view_stats():
    file_path = 'processed_data/records_with_salary_col.csv'
    if not os.path.exists(file_path):
        return redirect(url_for('index'))

    df = pd.read_csv(file_path)

    # Calculate statistics
    total_records = len(df)
    average_salary = df['salary'].mean()
    salary_distribution = df['salary_category'].value_counts().to_dict()
    top_cities = df['city'].value_counts().nlargest(5).to_dict()
    
    # Calculate age
    df['date_of_birth'] = pd.to_datetime(df['date_of_birth'])
    ages = (pd.to_datetime('today') - df['date_of_birth']).dt.days / 365.25
    average_age = ages.mean()

    stats = {
        'total_records': total_records,
        'average_salary': f"${average_salary:,.2f}",
        'average_age': f"{average_age:.1f} years",
        'salary_distribution': salary_distribution,
        'top_cities': top_cities
    }

    return render_template('stats.html', stats=stats)

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''
    if request.method == 'POST':
        if 'generate' in request.form:
            num_records = request.form.get('num_records', 1000, type=int)
            # Basic validation
            if num_records < 1:
                num_records = 1
            if num_records > 10000: # Safety limit
                num_records = 10000
            message = generate_data(num_records=num_records)
        elif 'process' in request.form:
            message = process_data()
    
    processed_files = []
    if os.path.exists('processed_data'):
        processed_files = os.listdir('processed_data')

    return render_template('index.html', message=message, processed_files=processed_files)

@app.route('/view/<filename>')
def view_file(filename):
    page = request.args.get('page', 1, type=int)
    search_name = request.args.get('search_name', '')
    filter_city = request.args.get('filter_city', '')
    filter_salary = request.args.get('filter_salary', '')

    file_path = os.path.join('processed_data', filename)
    if not os.path.exists(file_path):
        return "File not found.", 404
    
    df: pd.DataFrame = pd.DataFrame()
    try:
        if filename.endswith('.csv') or filename.endswith('.txt'):
            df = pd.read_csv(file_path)
        elif filename.endswith('.json'):
            df = pd.read_json(file_path)
        else:
            return "Unsupported file format.", 400
    except Exception as e:
        return f"Error reading file: {e}", 500

    # Get unique values for filters
    cities = [''] + sorted(df['city'].unique().tolist())
    salary_categories = [''] + sorted(df['salary_category'].unique().tolist())

    # Apply filters
    if search_name:
        df = cast(pd.DataFrame, df[df['name'].str.contains(search_name, case=False, na=False)])
    if filter_city:
        df = cast(pd.DataFrame, df[df['city'] == filter_city])
    if filter_salary:
        df = cast(pd.DataFrame, df[df['salary_category'] == filter_salary])

    # Paginate data
    total_records = len(df)
    total_pages = (total_records + RECORDS_PER_PAGE - 1) // RECORDS_PER_PAGE
    start = (page - 1) * RECORDS_PER_PAGE
    end = start + RECORDS_PER_PAGE
    paginated_df = df.iloc[start:end]

    # Smart Pagination Logic
    pages_to_show = []
    if total_pages > 1:
        pagination_range = 5  # Number of page links to show
        half_range = (pagination_range - 1) // 2
        
        start_page = page - half_range
        end_page = page + half_range

        if start_page < 1:
            end_page += (1 - start_page)
            start_page = 1
        
        if end_page > total_pages:
            start_page -= (end_page - total_pages)
            end_page = total_pages
        
        start_page = max(1, start_page)
        
        pages_to_show = list(range(start_page, end_page + 1))

    return render_template('view.html', 
                           filename=filename, 
                           data=paginated_df.to_html(classes='table table-striped table-bordered', index=False, justify='center'),
                           page=page,
                           total_pages=total_pages,
                           search_name=search_name,
                           filter_city=filter_city,
                           filter_salary=filter_salary,
                           cities=cities,
                           salary_categories=salary_categories,
                           pages_to_show=pages_to_show)

@app.route('/download/<filename>')
def download_file(filename):
    directory = os.path.join(os.getcwd(), 'processed_data')
    return send_from_directory(directory, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True) 