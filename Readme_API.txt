Install instructions

1. Install Flask library (pip install Flask)
2. Run main Api.py
3. Open the URL  http://127.0.0.1:5000

This is an API that allows you to track expenses and displays a simple summary. Expenses are saved in a .csv file. 

I have created another Python file called Functions.py in which I have four functions:

1. Add a transaction that receives a dictionary as an argument.
2. Add transactions from a .csv file in order to test the endpoints.
3. Delete a specific transaction with its ID.
4. Delete all transactions.

In addition, you can also add a transaction by placing the following path:
http://localhost:5000/api/transactions?amount=250&description=Cineplanet&category=entertainment&date=2025-11-03&type=expense

Roles:
Oscar Manuel Hurtado Talavera - backend programmer
