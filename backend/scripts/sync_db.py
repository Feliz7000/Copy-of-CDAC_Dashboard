from django.db import connection

def run_sql():
    with connection.cursor() as cursor:
        print("Adding columns to student_test_scores...")
        cursor.execute("ALTER TABLE student_test_scores ADD COLUMN IF NOT EXISTS exam_month DATE")
        cursor.execute("ALTER TABLE student_test_scores ADD COLUMN IF NOT EXISTS exam_year SMALLINT")
        
        print("Populating student_test_scores...")
        cursor.execute("""
            UPDATE student_test_scores 
            SET exam_month = date_trunc('month', exam_date)::date, 
                exam_year = EXTRACT(YEAR FROM exam_date) 
            WHERE exam_month IS NULL
        """)
        
        print("Adding columns to exam_schedule...")
        cursor.execute("ALTER TABLE exam_schedule ADD COLUMN IF NOT EXISTS scheduled_month DATE")
        
        print("Populating exam_schedule...")
        cursor.execute("""
            UPDATE exam_schedule 
            SET scheduled_month = date_trunc('month', scheduled_date)::date 
            WHERE scheduled_month IS NULL
        """)
        print("Database sync complete.")

if __name__ == "__main__":
    run_sql()
