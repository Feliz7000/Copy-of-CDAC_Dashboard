-- File: backend/sql/add_course_indexes.sql
--
-- Course-wise performance indexes for the Student Dashboard.
-- Single-centre system: the only meaningful filter dimension is COURSE.
-- Score tables store only PRN; course filtering always goes through student_master.
--
-- Join path:   scores_XX  →  student_master (on prn)  →  filter by course_id
--
-- CONCURRENTLY: PostgreSQL builds these indexes without table locks.
-- Safe to run on a live database.
-- On an empty dev DB you can drop CONCURRENTLY to make it faster.
--
-- Run with: psql -U <user> -d <database> -f backend/sql/add_course_indexes.sql
-- ─────────────────────────────────────────────────────────────────────────────

-- ── student_master: the join target ──────────────────────────────────────────

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sm_course
    ON student_master (course_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sm_batch
    ON student_master (batch_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sm_course_batch
    ON student_master (course_id, batch_id);

-- ── score tables: the join key (PRN) ─────────────────────────────────────────

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scores_ap_prn ON scores_ap (prn);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scores_as_prn ON scores_as (prn);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scores_cc_prn ON scores_cc (prn);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scores_gr_prn ON scores_gr (prn);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scores_in_prn ON scores_in (prn);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scores_ia_prn ON scores_ia (prn);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scores_na_prn ON scores_na (prn);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scores_pq_prn ON scores_pq (prn);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scores_ps_prn ON scores_ps (prn);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scores_sx_prn ON scores_sx (prn);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scores_ta_prn ON scores_ta (prn);

-- ── test_mapping: most frequent lookup (batch + category, active only) ────────

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tm_batch_category
    ON test_mapping (batch_name, category_code)
    WHERE is_active = TRUE;
