-- Custom Views Creation Script
-- You can select only the required columns by commenting out the ones you do not need.
-- Leading commas are used so you can easily comment out a line like this:
--    --,test_05

DROP VIEW IF EXISTS view_batches CASCADE;
CREATE OR REPLACE VIEW view_batches AS
SELECT
     batch_name
    ,batch_month
    ,batch_year
    ,is_active
FROM batches;

DROP VIEW IF EXISTS view_category_course_mapping CASCADE;
CREATE OR REPLACE VIEW view_category_course_mapping AS
SELECT
     id
    ,category_code
    ,course_code
    ,is_active
FROM category_course_mapping;

DROP VIEW IF EXISTS view_centres CASCADE;
CREATE OR REPLACE VIEW view_centres AS
SELECT
     centre_code
    ,centre_name
    ,is_active
FROM centres;

DROP VIEW IF EXISTS view_courses CASCADE;
CREATE OR REPLACE VIEW view_courses AS
SELECT
     course_code
    ,course_name
    ,is_active
FROM courses;

DROP VIEW IF EXISTS view_main_categories CASCADE;
CREATE OR REPLACE VIEW view_main_categories AS
SELECT
     category_code
    ,category_name
    ,max_marks_per_subtest
    ,no_of_subtests
    ,scaled_marks
    ,is_active
FROM main_categories;

DROP VIEW IF EXISTS view_student_master CASCADE;
CREATE OR REPLACE VIEW view_student_master AS
SELECT
     prn
    ,student_full_name
    ,centre_id
    ,course_id
    ,batch_id
    ,is_active
FROM student_master;

DROP VIEW IF EXISTS view_test_mapping CASCADE;
CREATE OR REPLACE VIEW view_test_mapping AS
SELECT
     id
    ,batch_name
    ,category_code
    ,logical_name
    ,column_slot
    ,max_marks
    -- ,sequence
    ,is_active
    -- ,created_at
    -- ,updated_at
FROM test_mapping;

DROP VIEW IF EXISTS view_scores_ap CASCADE;
CREATE OR REPLACE VIEW view_scores_ap AS
SELECT
     prn
    -- ,last_updated
    ,test_01
    ,test_02
    ,test_03
    ,test_04
    ,test_05
    ,test_06
    ,test_07
    ,test_08
    ,test_09
    ,test_10
    ,test_11
    ,test_12
    ,test_13
    ,test_14
    ,test_15
    ,test_16
    ,test_17
    ,test_18
    ,test_19
    ,test_20
FROM scores_ap;

DROP VIEW IF EXISTS view_scores_as CASCADE;
CREATE OR REPLACE VIEW view_scores_as AS
SELECT
     prn
    -- ,last_updated
    ,test_01
    ,test_02
    ,test_03
    ,test_04
    ,test_05
    ,test_06
    ,test_07
    ,test_08
    ,test_09
    ,test_10
    ,test_11
    ,test_12
    ,test_13
    ,test_14
    ,test_15
    ,test_16
    ,test_17
    ,test_18
    ,test_19
    ,test_20
    ,test_21
    ,test_22
    ,test_23
    ,test_24
    ,test_25
    ,test_26
    ,test_27
    ,test_28
    ,test_29
    ,test_30
FROM scores_as;

DROP VIEW IF EXISTS view_scores_cc CASCADE;
CREATE OR REPLACE VIEW view_scores_cc AS
SELECT
     prn
    -- ,last_updated
    ,test_01
    ,test_02
    ,test_03
    ,test_04
    ,test_05
    ,test_06
    ,test_07
    ,test_08
FROM scores_cc;

DROP VIEW IF EXISTS view_scores_gr CASCADE;
CREATE OR REPLACE VIEW view_scores_gr AS
SELECT
     prn
    -- ,last_updated
    ,test_01
    ,test_02
    ,test_03
    ,test_04
    ,test_05
    ,test_06
    ,test_07
    ,test_08
    ,test_09
    ,test_10
FROM scores_gr;

DROP VIEW IF EXISTS view_scores_ia CASCADE;
CREATE OR REPLACE VIEW view_scores_ia AS
SELECT
     prn
    -- ,last_updated
    ,test_01
    ,test_02
    ,test_03
    ,test_04
    ,test_05
    ,test_06
    ,test_07
    ,test_08
FROM scores_ia;

DROP VIEW IF EXISTS view_scores_in CASCADE;
CREATE OR REPLACE VIEW view_scores_in AS
SELECT
     prn
    -- ,last_updated
    ,test_01
    ,test_02
    ,test_03
    ,test_04
    ,test_05
FROM scores_in;

DROP VIEW IF EXISTS view_scores_na CASCADE;
CREATE OR REPLACE VIEW view_scores_na AS
SELECT
     prn
    -- ,last_updated
    ,test_01
    ,test_02
    ,test_03
    ,test_04
    ,test_05
FROM scores_na;

DROP VIEW IF EXISTS view_scores_pq CASCADE;
CREATE OR REPLACE VIEW view_scores_pq AS
SELECT
     prn
    -- ,last_updated
    ,test_01
    ,test_02
    ,test_03
    ,test_04
    ,test_05
    ,test_06
    ,test_07
    ,test_08
    ,test_09
    ,test_10
    ,test_11
    ,test_12
    ,test_13
    ,test_14
    ,test_15
    ,test_16
    ,test_17
    ,test_18
    ,test_19
    ,test_20
    ,test_21
    ,test_22
    ,test_23
    ,test_24
    ,test_25
    ,test_26
    ,test_27
    ,test_28
    ,test_29
    ,test_30
FROM scores_pq;

DROP VIEW IF EXISTS view_scores_ps CASCADE;
CREATE OR REPLACE VIEW view_scores_ps AS
SELECT
     prn
    -- ,last_updated
    ,test_01
    ,test_02
    ,test_03
    ,test_04
    ,test_05
    ,test_06
    ,test_07
    ,test_08
    ,test_09
    ,test_10
FROM scores_ps;

DROP VIEW IF EXISTS view_scores_sx CASCADE;
CREATE OR REPLACE VIEW view_scores_sx AS
SELECT
     prn
    -- ,last_updated
    ,test_01
    ,test_02
    ,test_03
    ,test_04
    ,test_05
    ,test_06
    ,test_07
    ,test_08
    ,test_09
    ,test_10
FROM scores_sx;

DROP VIEW IF EXISTS view_scores_ta CASCADE;
CREATE OR REPLACE VIEW view_scores_ta AS
SELECT
     prn
    -- ,last_updated
    ,test_01
    ,test_02
    ,test_03
    ,test_04
    ,test_05
FROM scores_ta;
