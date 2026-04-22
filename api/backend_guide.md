# 🚀 NewsHub Backend: The Ultimate Technical Deep Dive

Welcome to the **NewsHub** backend! This guide is designed for developers who want to understand exactly how every piece of technology in this project works and how they fit together.

---

## 🏗️ 1. Core Technologies & "How They Are Used"

### 🏦 ORM (Object-Relational Mapping) - *SQLAlchemy*
**What is it?** 
In the old days, developers had to write raw SQL strings like `SELECT * FROM users WHERE email = '...'`. This is error-prone and messy. An ORM allows you to treat database tables as **Python Classes**.

**How it's used in NewsHub:**
The `User` class is our "Blueprint."
```python
# File: api/models.py
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    full_name = Column(String(100))
    # ...
```
When we do `db.query(models.User).all()`, SQLAlchemy automatically converts that into SQL for the MySQL database. You don't have to worry about the database syntax; you just work with Python objects.

### 🛡️ Security & Hashing - *Bcrypt*
**What is it?**
Never, ever store a password in plain text. If the database is leaked, everyone's account is compromised. Instead, we "Hash" them.

**How it's used in NewsHub:**
We use the `bcrypt` library to protect users.
```python
# File: api/security.py
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
```
1.  **Hashing**: When you register, we take your password, add a random string called a **Salt**, and run it through a complex math function to get a unique "fingerprint" (the hash).
2.  **Verification**: During login, we take the password you typed, hash it again, and check if it matches the "fingerprint" we stored. We never actually know what your password is!

### 🔍 Data Validation - *Pydantic*
**What is it?**
Pydantic is a library that enforces "Types" on your data. It acts as a shield for your API.

**How it's used in NewsHub:**
We define classes like `SignupData` to filter incoming data. 
```python
# File: api/schemas.py
class SignupData(BaseModel):
    full_name: str
    email: str
    password: str
    interest_ids: List[int]
```
If the frontend tries to send a number instead of a string for the `email`, FastAPI will automatically reject the request with a "422 Unprocessable Entity" error before the code even tries to run. This keeps your database clean.

### 🌐 CORS (Cross-Origin Resource Sharing)
**What is it?**
Browsers have a security rule: a website on `http://localhost:4200` (your Angular app) cannot talk to a server on `http://localhost:8000` (your FastAPI app) unless the server explicitly gives permission.

**How it's used in NewsHub:**
We tell the backend to allow requests from any origin (`*`) so that your Angular app can fetch data without being blocked by the browser.
```python
# File: api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📂 2. Detailed File Roles

*   **`api/database.py`**: Handles the "Handshake" with MySQL. It uses a **Connection Pool**, which keeps several database connections open at once so it doesn't have to start a new one for every single request (which is slow).
*   **`api/main.py`**: The central nervous system. It uses **Decorators** like `@app.post("/login")` to tell FastAPI which URL should trigger which Python function.
*   **`api/crud.py`**: Contains the "Logic." For example, the `upsert_news_record` function is clever—it handles complex logic to make sure we don't save duplicate news articles or duplicate sources.

---

## 🔄 3. Advanced Workflow: The "Atomic" Signup

One of the most interesting parts of this backend is the **Atomic Transaction** found in `api/main.py`.

```python
# File: api/main.py
@app.post("/complete-signup")
def complete_signup(data: schemas.SignupData, db: Session = Depends(database.get_db)):
    try:
        # 1. Insert User
        new_user = models.User(...)
        db.add(new_user)
        db.commit() # Save the user first
        
        # 2. Insert Interests
        if data.interest_ids:
            # ... logic to link interests ...
            db.commit()
            
        return {"message": "Signup complete"}
    except Exception as e:
        db.rollback() # If ANYTHING fails, undo everything!
        raise HTTPException(status_code=500, detail=str(e))
```

1.  **The Goal**: A user should only be created if their interests are also successfully saved.
2.  **The Workflow**:
    *   Start a database session.
    *   Create the User.
    *   *If that works*, link the Interests.
    *   *If anything fails* (like a duplicate email), the code calls `db.rollback()`. This "undoes" everything so you don't end up with a "half-created" user.
    *   Only at the very end do we call `db.commit()` to make it permanent.

---

## 🚀 4. Future Technology: JWT (JSON Web Tokens)

*Note: Currently, the project uses simple session-based logic. JWT is a common next step for professional apps.*

**What is it?**
Instead of the backend "remembering" who you are, it gives you a digital "Passport" (a Token) after you log in. You send this passport back with every request.

**How it would be used:**
1.  **Login**: User sends credentials.
2.  **Token Generation**: Backend creates a signed JWT containing your User ID.
3.  **Client Storage**: The frontend saves this token in `localStorage`.
4.  **Authorization**: For every request (like "Get my favorites"), the frontend sends the token in the "Header." The backend verifies the signature and knows exactly who is asking.

---

## 🚦 5. Summary for Newbies

| Technology | Role | Analogy |
| :--- | :--- | :--- |
| **FastAPI** | Web Server | The Restaurant Building |
| **Endpoints** | URLs | The Menu Items |
| **SQLAlchemy** | ORM | The Waiter (translates your order to the chef) |
| **MySQL** | Database | The Pantry/Fridge (where food is stored) |
| **Bcrypt** | Security | The Safe (protects the secret recipes) |
| **Pydantic** | Validation | The Quality Control (checks the ingredients) |

---

*This guide is your roadmap to the NewsHub architecture. Use it to explore the code and understand the "why" behind the "how"!*
