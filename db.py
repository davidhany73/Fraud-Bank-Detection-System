import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# إعداد حجم البيانات (ممكن تزود الأرقام عشان تكبر الملفات أكتر)
NUM_CUSTOMERS = 200000
NUM_ACCOUNTS = 2500000
NUM_TRANSACTIONS = 300000

# 1. إنشاء بيانات العملاء (Customers)
print("Generating Customers Data...")
customers = pd.DataFrame({
    'customer_id': range(1, NUM_CUSTOMERS + 1),
    'customer_name': [f"User_{i}" for i in range(1, NUM_CUSTOMERS + 1)]
})
customers.to_csv('customers.csv', index=False)

# 2. إنشاء بيانات الحسابات (Accounts)
print("Generating Accounts Data...")
accounts = pd.DataFrame({
    'account_id': range(101, NUM_ACCOUNTS + 101),
    'customer_id': np.random.choice(customers['customer_id'], NUM_ACCOUNTS),
    'account_type': np.random.choice(['Savings', 'Checking', 'Credit'], NUM_ACCOUNTS)
})
accounts.to_csv('accounts.csv', index=False)

# 3. إنشاء بيانات المعاملات (Transactions)
print("Generating Transactions Data...")
start_date = datetime(2026, 1, 1)
transactions = pd.DataFrame({
    'txn_id': range(1001, NUM_TRANSACTIONS + 1001),
    'account_id': np.random.choice(accounts['account_id'], NUM_TRANSACTIONS),
    'amount': np.random.normal(1500, 2000, NUM_TRANSACTIONS), # بعضها هيكون سالب (invalid)
    'timestamp': [start_date + timedelta(minutes=random.randint(1, 200000)) for _ in range(NUM_TRANSACTIONS)],
    'txn_type': np.random.choice(['Deposit', 'Withdrawal', 'Transfer', 'Payment'], NUM_TRANSACTIONS)
})

# إضافة قيم فارغة (Nulls) بشكل عشوائي لاختبار تنظيف البيانات
transactions.loc[transactions.sample(frac=0.05).index, 'amount'] = np.nan

transactions.to_csv('transactions.csv', index=False)
print("Data Generation Complete! Files saved: customers.csv, accounts.csv, transactions.csv")