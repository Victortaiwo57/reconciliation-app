# reconciliation-app

### 🧾 Reconciliation App — Description and Purpose
## ✅ Problem It Solves
In many schools or educational programs, tracking payments and purchases made by enrollees can be chaotic and error-prone. Data is often scattered across paper receipts, Excel files, or informal records.

This app solves the problem by providing:

A secure, centralized, and structured way to track both payments and purchases.

The ability to filter, review, and export transaction history.

A clean interface that prevents accidental submissions via confirmation dialogs.

It’s useful for:
Bursars
Account officers

Admin staff in schools or training institutes
...who need to reconcile financial records easily.

### 🔧 How It Works (Key Features)
1. User Login System
Only authorized users can log in with their email and password.
<img src="https://github.com/Victortaiwo57/reconciliation-app/blob/main/Login.png" alt="Image" width="500" height="300">

3. Dynamic Task Selection
Users can choose to either make a payment or record a purchase.
<img src="https://github.com/Victortaiwo57/reconciliation-app/blob/main/Payment%20recorded%20notification.png" alt="Image" width="500" height="300">

4. Smart Forms with Confirmation
Forms update dynamically based on user input.
- A confirmation modal appears before any action is processed to prevent mistakes.
<img src="https://github.com/Victortaiwo57/reconciliation-app/blob/main/Confirm%20Payment%20submission.png" alt="Image" width="500" height="300">

4. Automatic ID Lookup
When recording payments or purchases, IDs for enrollees, schools, and items are automatically fetched from the database to maintain relational integrity.
<img src="https://github.com/Victortaiwo57/reconciliation-app/blob/main/Purchase%20recorded%20notification.png" width="500" height="300">

5. Filterable and Exportable History Table
Transactions (both payments and purchases) are merged and displayed in one table.

Filters include:
- Date range
- Transaction type (payment or purchase)
- Fee type
- School name

