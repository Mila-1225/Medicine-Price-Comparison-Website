#  MEDICINE PRICE COMPARISON SYSTEM

The **Medicine Price Comparison System** is a **web-based application** that allows users to search and compare medicine prices from multiple pharmacies in one place.

This system helps customers:

* Find the **lowest medicine price**
* Locate **nearby medical stores**
* Check **medicine availability instantly**

The platform also provides **dedicated dashboards** for **Store Owners** and **Administrators** to manage medicines, pharmacies, and system operations efficiently.

---

#  PROJECT OBJECTIVE

The main objective of this project is to create a system that helps users **save money and time** by easily comparing medicine prices from multiple pharmacies.

It also helps pharmacies **digitally manage their medicine inventory** and improve accessibility for customers.

---

#  FEATURES

✔ Instant **medicine search**
✔ **Compare prices** from different pharmacies
✔ Find the **lowest available price**
✔ Locate **nearby pharmacies**
✔ Pharmacy owners can **manage medicine inventory**
✔ Admin can **approve or reject pharmacies**
✔ Easy-to-use **dashboard interface**
✔ Improves **price transparency in medicines**

---

#  SYSTEM MODULES

##  USER MODULE

Users can:

* Search medicines by name
* Compare medicine prices
* View medicine availability
* Locate nearby pharmacies
* Choose the lowest price option

---

##  STORE OWNER MODULE

Pharmacy owners can:

* Register their pharmacy
* Add new medicines
* Update medicine prices
* Manage medicine stock
* Remove unavailable medicines

---

##  ADMIN MODULE

Administrators can:

* Approve or reject pharmacy registrations
* Manage all registered pharmacies
* Monitor medicine listings
* Maintain system data
* Ensure system security

---

#  INSTALLATION GUIDE

Follow these steps to run the project locally.

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/medicine-price-comparison.git
```

---

## 2️⃣ Navigate to the Project Folder

```bash
cd medicine-price-comparison
```

---

## 3️⃣ Install Dependencies

```bash
npm install
```

---

## 4️⃣ Setup MongoDB Database

1. Install **MongoDB**
2. Start the MongoDB service
3. Create a database

Example connection string:

```
mongodb://localhost:27017/medicineDB
```

Update this inside your **backend configuration file**.

---

## 5️⃣ Run Backend Server

```bash
npm start
```

---

## 6️⃣ Run Frontend

```bash
cd frontend
npm install
npm start
```

---

## 7️⃣ Open Application

Open in browser:

```
http://localhost:3000
```

---

#  LOGIN INFORMATION (EXAMPLE)

##  ADMIN LOGIN

Email:

```
admin@system.com
```

Password:

```
admin123
```

---

##  STORE OWNER LOGIN

Email:

```
store@pharmacy.com
```

Password:

```
store123
```

---

##  USER ACCESS

Users can **search medicines without login** depending on system configuration.

---

#  API ENDPOINTS

## Medicine API

```
GET /api/medicines
```

Get all medicines.

```
GET /api/medicines/:name
```

Search medicine by name.

```
POST /api/medicines
```

Add a new medicine (store owner).

---

## Pharmacy API

```
POST /api/pharmacy/register
```

Register pharmacy.

```
GET /api/pharmacy/list
```

View pharmacies.

---

#  TECHNOLOGIES USED

**Frontend**

* HTML
* CSS
* JavaScript
* React.js

**Backend**

* Node.js
* Express.js

**Database**

* MongoDB

**Tools**

* Git
* GitHub
* VS Code

---

#  CONTRIBUTING

Contributions are welcome!

Steps to contribute:

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Commit your updates
5. Create a pull request

---
