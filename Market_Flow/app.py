import os
import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
import plotly.graph_objects as go
import plotly.utils
from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
import subprocess

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database configuration - using local SQLite files
DATABASE_URL = 'db/orders.db'
CUSTOMER_DATABASE_URL = 'db/customers.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    return conn

def get_customer_db_connection():
    """Get customer database connection"""
    conn = sqlite3.connect(CUSTOMER_DATABASE_URL)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    """Home page with overview statistics"""
    try:
        conn = get_db_connection()
        
        # Get overview statistics
        stats = {}
        cursor = conn.cursor()
        
        # Total orders
        stats['total_orders'] = cursor.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
        
        # Total revenue (in EGP)
        stats['total_revenue'] = cursor.execute('SELECT SUM(amount) FROM orders').fetchone()[0] or 0
        
        # Unique customers
        stats['unique_customers'] = cursor.execute('SELECT COUNT(DISTINCT customer_full_name) FROM orders').fetchone()[0]
        
        # Unique products
        stats['unique_products'] = cursor.execute('SELECT COUNT(DISTINCT product_id) FROM orders').fetchone()[0]
        
        # Top branch by sales
        top_branch = cursor.execute('''
            SELECT branch, SUM(amount) as total_sales 
            FROM orders 
            GROUP BY branch 
            ORDER BY total_sales DESC 
            LIMIT 1
        ''').fetchone()
        stats['top_branch'] = dict(top_branch) if top_branch else {'branch': 'N/A', 'total_sales': 0}
        
        # Recent orders count (last 7 days)
        stats['recent_orders'] = cursor.execute('''
            SELECT COUNT(*) FROM orders 
            WHERE transaction_date >= date('now', '-7 days')
        ''').fetchone()[0]
        
        conn.close()
        
        return render_template('home.html', stats=stats)
    
    except Exception as e:
        print(f'Error loading dashboard: {str(e)}')
        return render_template('home.html', stats={})

@app.route('/orders')
def orders_dashboard():
    """Orders dashboard with filtering and pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '', type=str)
    branch_filter = request.args.get('branch', '', type=str)
    date_from = request.args.get('date_from', '', type=str)
    date_to = request.args.get('date_to', '', type=str)
    
    try:
        conn = get_db_connection()
        
        # Build query with filters
        query = 'SELECT * FROM orders WHERE 1=1'
        params = []
        
        if search:
            query += ' AND (customer_full_name LIKE ? OR product_name LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%'])
        
        if branch_filter:
            query += ' AND branch = ?'
            params.append(branch_filter)
        
        if date_from:
            query += ' AND transaction_date >= ?'
            params.append(date_from)
        
        if date_to:
            query += ' AND transaction_date <= ?'
            params.append(date_to)
        
        # Get total count for pagination
        count_query = query.replace('SELECT *', 'SELECT COUNT(*)')
        total_orders = conn.execute(count_query, params).fetchone()[0]
        
        # Add pagination
        query += ' ORDER BY transaction_date DESC LIMIT ? OFFSET ?'
        params.extend([per_page, (page - 1) * per_page])
        
        orders = conn.execute(query, params).fetchall()
        orders = [dict(order) for order in orders]
        
        # Get available branches for filter dropdown
        branches = conn.execute('SELECT DISTINCT branch FROM orders ORDER BY branch').fetchall()
        branches = [row[0] for row in branches]
        
        conn.close()
        
        # Calculate pagination info
        total_pages = (total_orders + per_page - 1) // per_page
        
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total_orders,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_num': page - 1 if page > 1 else None,
            'next_num': page + 1 if page < total_pages else None
        }
        
        return render_template('orders.html', 
                             orders=orders, 
                             pagination=pagination,
                             branches=branches,
                             filters={
                                 'search': search,
                                 'branch': branch_filter,
                                 'date_from': date_from,
                                 'date_to': date_to
                             })
    
    except Exception as e:
        print(f'Error loading orders: {str(e)}')
        # Still provide pagination info even in error case
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': 0,
            'total_pages': 0,
            'has_prev': page > 1,
            'has_next': False,
            'prev_num': page - 1 if page > 1 else None,
            'next_num': None
        }
        return render_template('orders.html', 
                             orders=[], 
                             pagination=pagination,
                             branches=[],
                             filters={
                                 'search': search,
                                 'branch': branch_filter,
                                 'date_from': date_from,
                                 'date_to': date_to
                             })

@app.route('/visualizations')
def visualizations():
    """Data visualizations page"""
    return render_template('visualizations.html')

@app.route('/control-panel')
def control_panel():
    """Control panel for pipeline operations"""
    return render_template('control_panel.html')

# API Endpoints
@app.route('/api/orders')
def api_orders():
    """API endpoint to get orders with filtering"""
    try:
        conn = get_db_connection()
        
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        search = request.args.get('search', '', type=str)
        branch = request.args.get('branch', '', type=str)
        date_from = request.args.get('date_from', '', type=str)
        date_to = request.args.get('date_to', '', type=str)
        
        # Build query
        query = 'SELECT * FROM orders WHERE 1=1'
        params = []
        
        if search:
            query += ' AND (customer_full_name LIKE ? OR product_name LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%'])
        
        if branch:
            query += ' AND branch = ?'
            params.append(branch)
        
        if date_from:
            query += ' AND transaction_date >= ?'
            params.append(date_from)
        
        if date_to:
            query += ' AND transaction_date <= ?'
            params.append(date_to)
        
        query += ' ORDER BY transaction_date DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        orders = conn.execute(query, params).fetchall()
        orders = [dict(order) for order in orders]
        
        # Get total count
        count_query = query.replace('SELECT *', 'SELECT COUNT(*)').replace('ORDER BY transaction_date DESC', '').replace('LIMIT ? OFFSET ?', '')
        count_params = params[:-2]  # Remove limit and offset
        total_count = conn.execute(count_query, count_params).fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'orders': orders,
            'total': total_count,
            'limit': limit,
            'offset': offset
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/export')
def api_export_orders():
    """Export orders to CSV or Excel"""
    try:
        format_type = request.args.get('format', 'csv').lower()
        
        conn = get_db_connection()
        
        # Build query with same filters as orders page
        query = 'SELECT * FROM orders WHERE 1=1'
        params = []
        
        search = request.args.get('search', '', type=str)
        branch = request.args.get('branch', '', type=str)
        date_from = request.args.get('date_from', '', type=str)
        date_to = request.args.get('date_to', '', type=str)
        
        if search:
            query += ' AND (customer_full_name LIKE ? OR product_name LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%'])
        
        if branch:
            query += ' AND branch = ?'
            params.append(branch)
        
        if date_from:
            query += ' AND transaction_date >= ?'
            params.append(date_from)
        
        if date_to:
            query += ' AND transaction_date <= ?'
            params.append(date_to)
        
        query += ' ORDER BY transaction_date DESC'
        
        # Get data using pandas for easy export
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        # Create in-memory file
        output = BytesIO()
        
        if format_type == 'excel':
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'orders_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
        else:  # CSV
            df.to_csv(output, index=False)
            output.seek(0)
            return send_file(
                output,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'orders_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
    
    except Exception as e:
        print(f'Export failed: {str(e)}')
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route('/api/analytics/sales-over-time')
def api_sales_over_time():
    """API endpoint for sales over time chart data"""
    try:
        conn = get_db_connection()
        days = request.args.get('days', 30, type=int)
        
        # Get daily sales for the specified number of days
        query = '''
            SELECT 
                DATE(transaction_date) as date,
                SUM(amount) as total_sales,
                COUNT(*) as order_count
            FROM orders 
            WHERE transaction_date >= date('now', '-{} days')
            GROUP BY DATE(transaction_date)
            ORDER BY date
        '''.format(days)
        
        results = conn.execute(query).fetchall()
        
        data = {
            'dates': [row[0] for row in results],
            'sales': [float(row[1]) for row in results],
            'orders': [row[2] for row in results]
        }
        
        conn.close()
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/top-products')
def api_top_products():
    """API endpoint for top selling products"""
    try:
        conn = get_db_connection()
        limit = request.args.get('limit', 10, type=int)
        
        query = '''
            SELECT 
                product_name,
                SUM(quantity) as total_quantity,
                SUM(amount) as total_sales,
                COUNT(*) as order_count
            FROM orders 
            GROUP BY product_id, product_name
            ORDER BY total_sales DESC
            LIMIT ?
        '''
        
        results = conn.execute(query, (limit,)).fetchall()
        
        data = [{
            'product_name': row[0],
            'total_quantity': row[1],
            'total_sales': float(row[2]),
            'order_count': row[3]
        } for row in results]
        
        conn.close()
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/sales-by-branch')
def api_sales_by_branch():
    """API endpoint for sales by branch"""
    try:
        conn = get_db_connection()
        
        query = '''
            SELECT 
                branch,
                SUM(amount) as total_sales,
                COUNT(*) as order_count
            FROM orders 
            GROUP BY branch
            ORDER BY total_sales DESC
        '''
        
        results = conn.execute(query).fetchall()
        
        data = [{
            'branch': row[0],
            'total_sales': float(row[1]),
            'order_count': row[2]
        } for row in results]
        
        conn.close()
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/top-customers')
def api_top_customers():
    """API endpoint for top customers by transaction count"""
    try:
        conn = get_db_connection()
        limit = request.args.get('limit', 10, type=int)
        
        query = '''
            SELECT 
                customer_full_name,
                COUNT(*) as transaction_count,
                SUM(amount) as total_spent
            FROM orders 
            GROUP BY customer_full_name
            ORDER BY transaction_count DESC
            LIMIT ?
        '''
        
        results = conn.execute(query, (limit,)).fetchall()
        
        data = [{
            'customer_name': row[0],
            'transaction_count': row[1],
            'total_spent': float(row[2])
        } for row in results]
        
        conn.close()
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Pipeline Control Endpoints
@app.route('/api/pipeline/etl', methods=['POST'])
def api_run_etl():
    """Run ETL pipeline"""
    try:
        # Import and run the ETL function
        from etl_pipeline import etl_pipeline
        etl_pipeline()
        return jsonify({'status': 'success', 'message': 'ETL pipeline completed successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/pipeline/delta-load', methods=['POST'])
def api_run_delta_load():
    """Run delta load"""
    try:
        from delta_load import delta_load
        delta_load()
        return jsonify({'status': 'success', 'message': 'Delta load completed successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/pipeline/update-prices', methods=['POST'])
def api_update_prices():
    """Update product prices"""
    try:
        from update_prices import main as update_prices_main
        update_prices_main()
        return jsonify({'status': 'success', 'message': 'Product prices updated successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/pipeline/currency-conversion', methods=['POST'])
def api_currency_conversion():
    """Check current exchange rate (currency conversion is now integrated into ETL)"""
    try:
        from currency_conversion import get_usd_to_egp_rate
        current_rate = get_usd_to_egp_rate()
        return jsonify({
            'status': 'success', 
            'message': f'Current USD to EGP rate: {current_rate}. Note: Currency conversion is now automatically handled during ETL process.',
            'exchange_rate': current_rate
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/exchange-rate')
def api_exchange_rate():
    """Get current USD to EGP exchange rate"""
    try:
        from currency_conversion import get_usd_to_egp_rate
        current_rate = get_usd_to_egp_rate()
        return jsonify({
            'success': True,
            'exchange_rate': current_rate,
            'base_currency': 'USD',
            'target_currency': 'EGP'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
