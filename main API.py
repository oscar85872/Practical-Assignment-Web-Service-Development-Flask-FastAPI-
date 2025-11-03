from flask import Flask, request, jsonify
from datetime import datetime
import csv
import os

app = Flask(__name__)

EXPENSES_FILE = 'expenses.csv'
CATEGORIES = ['food', 'transport', 'entertainment', 'bills', 'shopping', 'health', 'education', 'income', 'other']

def init_csv():
    if not os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'amount', 'description', 'category', 'date', 'type'])

def generate_id():
    try:
        if not os.path.exists(EXPENSES_FILE):
            return 1
            
        with open(EXPENSES_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            if not rows:
                return 1
            return max(int(row['id']) for row in rows) + 1
    except Exception as e:
        print(f"Error generating ID: {e}")
        return 1

def reindex_transactions():
    try:
        if not os.path.exists(EXPENSES_FILE):
            return
            
        transactions = []
        with open(EXPENSES_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for i, row in enumerate(reader, 1):
                row['id'] = i
                transactions.append(row)
        
        with open(EXPENSES_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'amount', 'description', 'category', 'date', 'type'])
            for transaction in transactions:
                writer.writerow([
                    transaction['id'],
                    transaction['amount'],
                    transaction['description'],
                    transaction['category'],
                    transaction['date'],
                    transaction['type']
                ])
        
    except Exception as e:
        print(f"Error reindexing transactions: {e}")

def validate_date(date_string):
    try:
        datetime.fromisoformat(date_string)
        return True
    except ValueError:
        return False

@app.route('/')
def home():
    return jsonify({
        'message': 'Personal Expense Tracker API'   
    })

@app.route('/api/status', methods=['GET'])
def status_check():
    return jsonify({
        'status': 'working',
        'message': 'Personal Expense Tracker API is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/transactions', methods=['POST', 'GET'])
def add_transaction():
    try:
        if request.method == 'GET':
            amount = request.args.get('amount')
            description = request.args.get('description')
            category = request.args.get('category')
            date = request.args.get('date')
            transaction_type = request.args.get('type')
            
            data = {
                'amount': amount,
                'description': description,
                'category': category,
                'date': date,
                'type': transaction_type
            }
            request_type = 'GET'
        else:
            data = request.get_json()
            request_type = 'POST'
        
        if not data:
            return jsonify({'error': 'Data required'}), 400
        
        required_fields = ['amount', 'description', 'category', 'date', 'type']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({'error': 'Amount must be greater than 0'}), 400
        except ValueError:
            return jsonify({'error': 'Amount must be a valid number'}), 400
        
        if data['category'] not in CATEGORIES:
            return jsonify({'error': f'Invalid category. Options: {", ".join(CATEGORIES)}'}), 400
        
        if data['type'] not in ['expense', 'income']:
            return jsonify({'error': 'Type must be "expense" or "income"'}), 400
        
        if not validate_date(data['date']):
            return jsonify({'error': 'Date must be in ISO format (YYYY-MM-DD)'}), 400
        
        transaction_id = generate_id()
        transaction = {
            'id': transaction_id,
            'amount': amount,
            'description': data['description'],
            'category': data['category'],
            'date': data['date'],
            'type': data['type']
        }
        
        with open(EXPENSES_FILE, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                transaction['id'],
                transaction['amount'],
                transaction['description'],
                transaction['category'],
                transaction['date'],
                transaction['type']
            ])
        
        message = 'Transaction added successfully'
        if request_type == 'GET':
            message += ' via quick add'
        
        return jsonify({
            'message': message,
            'transaction': transaction,
            'method': request_type
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Error saving transaction: {str(e)}'}), 500

@app.route('/api/transactions/list', methods=['GET'])
def get_transactions():
    try:
        if not os.path.exists(EXPENSES_FILE):
            return jsonify({'count': 0, 'transactions': []}), 200
            
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')
        transaction_type = request.args.get('type')
        
        transactions = []
        with open(EXPENSES_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                row['id'] = int(row['id'])
                row['amount'] = float(row['amount'])
                
                include = True
                
                if start_date and row['date'] < start_date:
                    include = False
                if end_date and row['date'] > end_date:
                    include = False
                if category and row['category'] != category:
                    include = False
                if transaction_type and row['type'] != transaction_type:
                    include = False
                
                if include:
                    transactions.append(row)
        
        return jsonify({
            'count': len(transactions),
            'transactions': transactions
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error reading transactions: {str(e)}'}), 500

@app.route('/api/summary/months', methods=['GET'])
def get_monthly_summaries():
    try:
        year = request.args.get('year', str(datetime.now().year))
        include_empty = request.args.get('include_empty', 'false').lower() == 'true'
        
        try:
            year = int(year)
        except ValueError:
            return jsonify({'error': 'Year must be a valid number'}), 400
        
        if not os.path.exists(EXPENSES_FILE):
            return jsonify({
                'monthly_summaries': {}
            }), 200
        
        month_names = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        
        monthly_data = {}
        months_with_transactions = set()
        
        with open(EXPENSES_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                transaction_date = datetime.fromisoformat(row['date'])
                if transaction_date.year == year:
                    month = transaction_date.month
                    months_with_transactions.add(month)
        
        target_months = months_with_transactions
        if include_empty:
            target_months = set(range(1, 13))
        
        for month in target_months:
            month_name = month_names[month]
            monthly_data[month_name] = {
                'income_by_category': {},
                'expenses_by_category': {}
            }
        
        with open(EXPENSES_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                transaction_date = datetime.fromisoformat(row['date'])
                if transaction_date.year == year:
                    month = transaction_date.month
                    month_name = month_names[month]
                    if month_name in monthly_data:
                        amount = float(row['amount'])
                        
                        if row['type'] == 'income':
                            category = row['category']
                            if category not in monthly_data[month_name]['income_by_category']:
                                monthly_data[month_name]['income_by_category'][category] = 0.0
                            monthly_data[month_name]['income_by_category'][category] += amount
                        else:
                            category = row['category']
                            if category not in monthly_data[month_name]['expenses_by_category']:
                                monthly_data[month_name]['expenses_by_category'][category] = 0.0
                            monthly_data[month_name]['expenses_by_category'][category] += amount
        
        for month_name, data in monthly_data.items():
            data['income_by_category'] = {k: round(v, 2) for k, v in data['income_by_category'].items()}
            data['expenses_by_category'] = {k: round(v, 2) for k, v in data['expenses_by_category'].items()}
        
        sorted_summaries = dict(sorted(
            monthly_data.items(),
            key=lambda x: list(month_names.values()).index(x[0])
        ))
        
        return jsonify({
            'monthly_summaries': sorted_summaries
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error generating monthly summaries: {str(e)}'}), 500
    
@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    try:
        if not os.path.exists(EXPENSES_FILE):
            return jsonify({'error': 'No transactions to delete'}), 404
            
        transactions = []
        found = False
        
        with open(EXPENSES_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if int(row['id']) == transaction_id:
                    found = True
                else:
                    transactions.append(row)
        
        if not found:
            return jsonify({'error': 'Transaction not found'}), 404
        
        with open(EXPENSES_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'amount', 'description', 'category', 'date', 'type'])
            for transaction in transactions:
                writer.writerow([
                    transaction['id'],
                    transaction['amount'],
                    transaction['description'],
                    transaction['category'],
                    transaction['date'],
                    transaction['type']
                ])
        
        reindex_transactions()
        
        return jsonify({'message': 'Transaction deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Error deleting transaction: {str(e)}'}), 500

@app.route('/api/transactions/reindex', methods=['POST'])
def reindex_all_transactions():
    try:
        reindex_transactions()
        return jsonify({'message': 'All transactions reindexed successfully'}), 200
    except Exception as e:
        return jsonify({'error': f'Error reindexing transactions: {str(e)}'}), 500

if __name__ == '__main__':
    init_csv()
    app.run(debug=True)