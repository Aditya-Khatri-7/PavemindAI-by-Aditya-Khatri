from database import test_db_connection

if __name__ == "__main__":
    print("Testing MongoDB connection...")
    success = test_db_connection()
    if success:
        print("Database test passed!")
    else:
        print("Database test failed!")
