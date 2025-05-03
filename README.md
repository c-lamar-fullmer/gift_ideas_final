# Gift Ideas List

Gift Ideas List is a web application that helps users organize and manage gift ideas for their loved ones. Users can create accounts, add people, and brainstorm gift ideas for each person.

---

## **Project Overview**
This application allows users to:
- Register and log in to their accounts.
- Add, edit, and delete people and their associated gift ideas.
- Search for people or gifts using a search bar.
- View paginated lists of people and their gift ideas.

---

## **Technical Details**
### **Python Version**
This application was developed and tested using **Python 3.9.7**.

### **Browser**
The application was tested using **Google Chrome Version 112.0.5615.49**.

### **PostgreSQL Version**
The database was created and tested using **PostgreSQL 14.15**.

## **Setup and Installation**
Follow these steps to install, configure, and run the application:

1. **Prerequisites**:
   - Ensure you have **Python** (version 3.9.1 or higher) installed on your system. You can download it from [python.org](https://www.python.org/).
   - Ensure you have **PostgreSQL** installed and running on your system.

2. **Install Poetry**:
   - Poetry is used for dependency management and packaging. If Poetry is not installed, you can install it by running:
     ```bash
     curl -sSL [https://install.python-poetry.org](https://install.python-poetry.org) | python3 -
     ```
     Alternatively, you can use `pip` to install Poetry:
     ```bash
     pip install poetry
     ```
     Verify the installation by running:
     ```bash
     poetry --version
     ```
     > **Note**: macOS uses `zsh` as the default shell. The commands in this guide work in both `zsh` and `bash`.

3. **Extract the Project Files**:
   - Unzip the archive to your desired directory.
     ```bash
     unzip gift_ideas_final.zip
     cd gift_ideas_final
     ```

4. **Install Project Dependencies**:
   - Use Poetry to install the dependencies listed in `pyproject.toml`:
     ```bash
     poetry install
     ```

5. **Database Setup**:
   - Open your terminal and connect to the PostgreSQL server using the `psql` command:
     ```bash
     psql postgres
     ```
     You might be prompted for your PostgreSQL user password.
   - Once connected to the `postgres` database, execute the `schema.sql` script to create the necessary database and tables:
     ```sql
     \i schema.sql;
     ```
     You should see output similar to this:
     ```
     CREATE DATABASE
     You are now connected to database "gift_ideas" as user "your_postgres_user".
     CREATE TABLE
     CREATE TABLE
     CREATE TABLE
     gift_ideas=#
     ```
     **Note:** Replace `"your_postgres_user"` with your actual PostgreSQL username.
   - After the database and tables are created, execute the `seed_data.sql` script to populate the database with initial data:
     ```sql
     \i seed_data.sql;
     ```
     You should see output confirming the data insertion, similar to this:
     ```
    gift_ideas=# \i seed_data.sql;
    COPY 1
    COPY 8
    COPY 62
    setval 
    --------
    1164
    (1 row)

    setval 
    --------
        8
    (1 row)

    setval 
    --------
        1
    (1 row)
     ```

6. **Run the Application**:
   - (Optional) Activate the Poetry virtual environment:
     ```bash
     poetry shell
     ```
   - Run the application using Python:
     ```bash
     python app.py
     ```
     Or, if you didn't activate the shell:
     ```bash
     poetry run python app.py
     ```

**Test User Credentials**

The seed data includes a test user account you can use to explore the application:

- **Username**: `Gus`
- **Password**: `Testing123`