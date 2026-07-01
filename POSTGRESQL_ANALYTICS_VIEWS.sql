-- PostgreSQL Analytics Views for Power BI
-- Comprehensive views for batch percentile analysis and spider chart data

-- =============================================================================
-- VIEW 1: v_batch_percentile
-- Purpose: Calculate percentile ranking within batch for each student-category
-- Used in: Power BI - CCEE (Class Comparison Effectiveness Evaluation) chart
-- =============================================================================

CREATE VIEW v_batch_percentile AS
WITH category_batch_stats AS (
    -- Calculate batch statistics per category
    SELECT 
        s.centre_code,
        s.course_code,
        s.enroll_year,
        s.batch_month,
        scs.category_code,
        scs.category_name,
        scs.original_total,
        scs.scaled_total,
        ROUND(AVG(scs.scaled_score)::NUMERIC, 2) AS batch_avg_scaled_score,
        ROUND(MAX(scs.scaled_score)::NUMERIC, 2) AS batch_max_scaled_score,
        ROUND(MIN(scs.scaled_score)::NUMERIC, 2) AS batch_min_scaled_score,
        COUNT(DISTINCT s.prn) AS batch_size,
        STDDEV_POP(scs.scaled_score) AS batch_stddev_scaled_score
    FROM students s
    INNER JOIN v_student_category_scores scs 
        ON s.prn = scs.prn
    WHERE s.is_active = TRUE
    GROUP BY 
        s.centre_code,
        s.course_code,
        s.enroll_year,
        s.batch_month,
        scs.category_code,
        scs.category_name,
        scs.original_total,
        scs.scaled_total
),
student_percentile AS (
    -- Calculate percentile rank for each student in their batch-category
    SELECT 
        s.prn,
        s.full_name,
        s.centre_code,
        s.course_code,
        s.enroll_year,
        s.batch_month,
        scs.category_code,
        scs.category_name,
        scs.original_total,
        scs.scaled_total,
        ROUND(scs.scaled_score::NUMERIC, 2) AS scaled_score,
        cbs.batch_avg_scaled_score,
        cbs.batch_max_scaled_score,
        cbs.batch_min_scaled_score,
        cbs.batch_size,
        ROUND(cbs.batch_stddev_scaled_score::NUMERIC, 2) AS batch_stddev,
        -- Calculate percentile rank (0-100)
        ROUND(
            (PERCENT_RANK() OVER (
                PARTITION BY 
                    s.centre_code,
                    s.course_code,
                    s.enroll_year,
                    s.batch_month,
                    scs.category_code
                ORDER BY scs.scaled_score DESC NULLS LAST
            ) * 100)::NUMERIC,
            2
        ) AS percentile_rank,
        -- Calculate z-score relative to batch mean
        CASE 
            WHEN cbs.batch_stddev_scaled_score = 0 THEN 0
            ELSE ROUND(
                ((scs.scaled_score - cbs.batch_avg_scaled_score) / cbs.batch_stddev_scaled_score)::NUMERIC,
                2
            )
        END AS z_score,
        -- Rank position in batch (1 = best)
        ROW_NUMBER() OVER (
            PARTITION BY 
                s.centre_code,
                s.course_code,
                s.enroll_year,
                s.batch_month,
                scs.category_code
            ORDER BY scs.scaled_score DESC NULLS LAST
        ) AS rank_in_batch,
        -- Categorize performance relative to batch average
        CASE 
            WHEN scs.scaled_score >= cbs.batch_avg_scaled_score + (cbs.batch_stddev_scaled_score * 1) THEN 'Excellent (>1σ above mean)'
            WHEN scs.scaled_score >= cbs.batch_avg_scaled_score THEN 'Good (above mean)'
            WHEN scs.scaled_score >= cbs.batch_avg_scaled_score - (cbs.batch_stddev_scaled_score * 1) THEN 'Fair (below mean)'
            ELSE 'Poor (<1σ below mean)'
        END AS performance_tier
    FROM students s
    INNER JOIN v_student_category_scores scs 
        ON s.prn = scs.prn
    INNER JOIN category_batch_stats cbs
        ON s.centre_code = cbs.centre_code
        AND s.course_code = cbs.course_code
        AND s.enroll_year = cbs.enroll_year
        AND s.batch_month = cbs.batch_month
        AND scs.category_code = cbs.category_code
    WHERE s.is_active = TRUE
)
SELECT 
    prn,
    full_name,
    centre_code,
    course_code,
    enroll_year,
    batch_month,
    category_code,
    category_name,
    original_total,
    scaled_total,
    scaled_score,
    batch_avg_scaled_score,
    batch_max_scaled_score,
    batch_min_scaled_score,
    batch_size,
    batch_stddev,
    percentile_rank,
    z_score,
    rank_in_batch,
    performance_tier
FROM student_percentile
ORDER BY 
    centre_code,
    course_code,
    enroll_year,
    batch_month,
    category_code,
    prn;

-- Create indexes for performance
CREATE INDEX idx_batch_percentile_prn ON v_batch_percentile(prn);
CREATE INDEX idx_batch_percentile_batch ON v_batch_percentile(centre_code, course_code, enroll_year, batch_month);
CREATE INDEX idx_batch_percentile_category ON v_batch_percentile(category_code);


-- =============================================================================
-- VIEW 2: v_spider_chart_data
-- Purpose: Format student category scores alongside batch averages for radar charts
-- Used in: Power BI - Radar/Spider chart visualization
-- Filters can be applied in Power BI using parameter for prn
-- =============================================================================

CREATE VIEW v_spider_chart_data AS
WITH student_data AS (
    -- Get student's scores per category
    SELECT 
        s.prn,
        s.full_name,
        s.centre_code,
        s.course_code,
        s.enroll_year,
        s.batch_month,
        scs.category_code,
        scs.category_name,
        ROUND(scs.scaled_score::NUMERIC, 2) AS student_score,
        ROUND(scs.scaled_total::NUMERIC, 2) AS category_max,
        -- Calculate student's performance as percentage of category max
        ROUND(
            (scs.scaled_score / NULLIF(scs.scaled_total, 0) * 100)::NUMERIC,
            2
        ) AS student_score_pct
    FROM students s
    INNER JOIN v_student_category_scores scs 
        ON s.prn = scs.prn
    WHERE s.is_active = TRUE
),
batch_averages AS (
    -- Calculate batch average per category
    SELECT 
        s.centre_code,
        s.course_code,
        s.enroll_year,
        s.batch_month,
        scs.category_code,
        scs.category_name,
        ROUND(AVG(scs.scaled_score)::NUMERIC, 2) AS batch_avg_score,
        ROUND(
            (AVG(scs.scaled_score) / NULLIF(MAX(scs.scaled_total), 0) * 100)::NUMERIC,
            2
        ) AS batch_avg_score_pct
    FROM students s
    INNER JOIN v_student_category_scores scs 
        ON s.prn = scs.prn
    WHERE s.is_active = TRUE
    GROUP BY 
        s.centre_code,
        s.course_code,
        s.enroll_year,
        s.batch_month,
        scs.category_code,
        scs.category_name
)
SELECT 
    sd.prn,
    sd.full_name,
    sd.centre_code,
    sd.course_code,
    sd.enroll_year,
    sd.batch_month,
    sd.category_code,
    sd.category_name,
    sd.student_score,
    ba.batch_avg_score,
    sd.category_max,
    sd.student_score_pct,
    ba.batch_avg_score_pct,
    -- Calculate difference (for variance visualization)
    ROUND((sd.student_score - ba.batch_avg_score)::NUMERIC, 2) AS score_diff,
    ROUND((sd.student_score_pct - ba.batch_avg_score_pct)::NUMERIC, 2) AS score_pct_diff,
    -- Determine if student is above or below batch average
    CASE 
        WHEN sd.student_score >= ba.batch_avg_score THEN 'Above Average'
        ELSE 'Below Average'
    END AS performance_status,
    -- Order for chart display
    ROW_NUMBER() OVER (
        PARTITION BY sd.prn, sd.centre_code, sd.course_code, sd.enroll_year, sd.batch_month
        ORDER BY sd.category_code
    ) AS category_order
FROM student_data sd
LEFT JOIN batch_averages ba
    ON sd.centre_code = ba.centre_code
    AND sd.course_code = ba.course_code
    AND sd.enroll_year = ba.enroll_year
    AND sd.batch_month = ba.batch_month
    AND sd.category_code = ba.category_code
ORDER BY 
    sd.prn,
    sd.centre_code,
    sd.course_code,
    sd.enroll_year,
    sd.batch_month,
    sd.category_code;

-- Create indexes for performance
CREATE INDEX idx_spider_prn ON v_spider_chart_data(prn);
CREATE INDEX idx_spider_batch ON v_spider_chart_data(centre_code, course_code, enroll_year, batch_month);
CREATE INDEX idx_spider_category ON v_spider_chart_data(category_code);


-- =============================================================================
-- VIEW 3: v_category_ranking (Bonus View)
-- Purpose: Rank students within each category for comparative analysis
-- =============================================================================

CREATE VIEW v_category_ranking AS
SELECT 
    s.prn,
    s.full_name,
    s.centre_code,
    s.course_code,
    s.enroll_year,
    s.batch_month,
    scs.category_code,
    scs.category_name,
    ROUND(scs.scaled_score::NUMERIC, 2) AS scaled_score,
    ROUND(scs.scaled_total::NUMERIC, 2) AS scaled_total,
    -- Rank within category (across all batches)
    ROW_NUMBER() OVER (
        PARTITION BY scs.category_code
        ORDER BY scs.scaled_score DESC NULLS LAST
    ) AS global_rank,
    -- Rank within category within batch
    ROW_NUMBER() OVER (
        PARTITION BY 
            s.centre_code,
            s.course_code,
            s.enroll_year,
            s.batch_month,
            scs.category_code
        ORDER BY scs.scaled_score DESC NULLS LAST
    ) AS batch_rank,
    -- Percentile within category
    ROUND(
        (PERCENT_RANK() OVER (
            PARTITION BY scs.category_code
            ORDER BY scs.scaled_score DESC NULLS LAST
        ) * 100)::NUMERIC,
        2
    ) AS global_percentile,
    -- Count of students in category batch
    COUNT(*) OVER (
        PARTITION BY 
            s.centre_code,
            s.course_code,
            s.enroll_year,
            s.batch_month,
            scs.category_code
    ) AS students_in_batch_category
FROM students s
INNER JOIN v_student_category_scores scs 
    ON s.prn = scs.prn
WHERE s.is_active = TRUE
ORDER BY 
    scs.category_code,
    scs.scaled_score DESC NULLS LAST;

CREATE INDEX idx_category_ranking_prn ON v_category_ranking(prn);
CREATE INDEX idx_category_ranking_category ON v_category_ranking(category_code, batch_rank);


-- =============================================================================
-- VIEW 4: v_comprehensive_student_analytics (Bonus View)
-- Purpose: Single-row comprehensive view per student for overall dashboards
-- =============================================================================

CREATE VIEW v_comprehensive_student_analytics AS
WITH student_totals AS (
    SELECT 
        sgt.prn,
        sgt.full_name,
        sgt.centre_code,
        sgt.course_code,
        sgt.enroll_year,
        sgt.batch_month,
        ROUND(sgt.grand_total::NUMERIC, 2) AS grand_total,
        sgt.grade,
        sgt.description AS grade_description
    FROM v_student_grand_total sgt
),
category_stats AS (
    SELECT 
        prn,
        COUNT(DISTINCT category_code) AS categories_completed,
        ROUND(AVG(scaled_score)::NUMERIC, 2) AS avg_category_score,
        ROUND(MAX(scaled_score)::NUMERIC, 2) AS best_category_score,
        ROUND(MIN(scaled_score)::NUMERIC, 2) AS worst_category_score
    FROM v_student_category_scores
    GROUP BY prn
),
test_stats AS (
    SELECT 
        prn,
        COUNT(*) AS total_test_attempts,
        SUM(CASE WHEN is_absent = FALSE THEN 1 ELSE 0 END) AS tests_completed,
        SUM(CASE WHEN is_absent = TRUE THEN 1 ELSE 0 END) AS tests_absent,
        ROUND(AVG(CASE WHEN is_absent = FALSE THEN score ELSE NULL END)::NUMERIC, 2) AS avg_test_score,
        ROUND(MAX(score)::NUMERIC, 2) AS best_test_score,
        ROUND(MIN(CASE WHEN is_absent = FALSE THEN score ELSE NULL END)::NUMERIC, 2) AS worst_test_score
    FROM student_test_scores
    GROUP BY prn
),
batch_context AS (
    SELECT 
        st.prn,
        ROUND(AVG(sgt.grand_total)::NUMERIC, 2) AS batch_avg_total,
        ROUND(MAX(sgt.grand_total)::NUMERIC, 2) AS batch_max_total,
        COUNT(DISTINCT st.prn) AS batch_size,
        ROW_NUMBER() OVER (
            PARTITION BY st.centre_code, st.course_code, st.enroll_year, st.batch_month
            ORDER BY sgt.grand_total DESC NULLS LAST
        ) AS rank_in_batch
    FROM students st
    INNER JOIN v_student_grand_total sgt 
        ON st.prn = sgt.prn
    WHERE st.is_active = TRUE
    GROUP BY st.prn, st.centre_code, st.course_code, st.enroll_year, st.batch_month
)
SELECT 
    st.prn,
    st.full_name,
    st.centre_code,
    st.course_code,
    st.enroll_year,
    st.batch_month,
    st.grand_total,
    st.grade,
    st.grade_description,
    cs.categories_completed,
    cs.avg_category_score,
    cs.best_category_score,
    cs.worst_category_score,
    ts.total_test_attempts,
    ts.tests_completed,
    ts.tests_absent,
    ts.avg_test_score,
    ts.best_test_score,
    ts.worst_test_score,
    bc.batch_avg_total,
    bc.batch_max_total,
    bc.batch_size,
    bc.rank_in_batch,
    ROUND(
        ((bc.batch_size - bc.rank_in_batch + 1)::NUMERIC / bc.batch_size * 100),
        2
    ) AS percentile_rank,
    ROUND((st.grand_total - bc.batch_avg_total)::NUMERIC, 2) AS diff_from_batch_avg
FROM student_totals st
LEFT JOIN category_stats cs ON st.prn = cs.prn
LEFT JOIN test_stats ts ON st.prn = ts.prn
LEFT JOIN batch_context bc ON st.prn = bc.prn
ORDER BY st.centre_code, st.course_code, st.enroll_year, st.batch_month, st.prn;

CREATE INDEX idx_comprehensive_prn ON v_comprehensive_student_analytics(prn);
CREATE INDEX idx_comprehensive_batch ON v_comprehensive_student_analytics(centre_code, course_code, enroll_year, batch_month);


-- =============================================================================
-- VALIDATION QUERIES (Optional - for testing)
-- =============================================================================

-- Test v_batch_percentile
-- SELECT * FROM v_batch_percentile 
-- WHERE prn = '123456789012' AND category_code = 'MSE'
-- LIMIT 1;

-- Test v_spider_chart_data
-- SELECT * FROM v_spider_chart_data 
-- WHERE prn = '123456789012'
-- ORDER BY category_order;

-- Test v_category_ranking
-- SELECT * FROM v_category_ranking 
-- WHERE category_code = 'MSE'
-- ORDER BY global_rank
-- LIMIT 10;

-- Test v_comprehensive_student_analytics
-- SELECT prn, full_name, grand_total, grade, percentile_rank 
-- FROM v_comprehensive_student_analytics
-- WHERE centre_code = '001' AND course_code = '28'
-- ORDER BY grand_total DESC;

-- =============================================================================
-- VIEW 5: v_placement_report
-- Purpose: All-Subtests Placement Report with category scaling and cutoffs
-- =============================================================================

CREATE OR REPLACE VIEW v_placement_report AS
WITH
-- ── CC ───────────────────────────────────────────────────────────────────────
cc_scores AS (
    SELECT
        sm.prn,
        tm_agg.n_configured,
        tm_agg.raw_max,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) THEN COALESCE(sc.test_01, 0) ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) THEN COALESCE(sc.test_02, 0) ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) THEN COALESCE(sc.test_03, 0) ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) THEN COALESCE(sc.test_04, 0) ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) THEN COALESCE(sc.test_05, 0) ELSE 0 END +
         CASE WHEN 'test_06' = ANY(tm_agg.slots) THEN COALESCE(sc.test_06, 0) ELSE 0 END +
         CASE WHEN 'test_07' = ANY(tm_agg.slots) THEN COALESCE(sc.test_07, 0) ELSE 0 END +
         CASE WHEN 'test_08' = ANY(tm_agg.slots) THEN COALESCE(sc.test_08, 0) ELSE 0 END
        ) AS cc_raw_sum,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) AND sc.test_01 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) AND sc.test_02 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) AND sc.test_03 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) AND sc.test_04 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) AND sc.test_05 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_06' = ANY(tm_agg.slots) AND sc.test_06 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_07' = ANY(tm_agg.slots) AND sc.test_07 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_08' = ANY(tm_agg.slots) AND sc.test_08 IS NOT NULL THEN 1 ELSE 0 END
        ) AS cc_subtests_entered,
        CASE WHEN 'test_01' = ANY(tm_agg.slots) THEN sc.test_01 ELSE NULL END AS cc_s1,
        CASE WHEN 'test_02' = ANY(tm_agg.slots) THEN sc.test_02 ELSE NULL END AS cc_s2,
        CASE WHEN 'test_03' = ANY(tm_agg.slots) THEN sc.test_03 ELSE NULL END AS cc_s3,
        CASE WHEN 'test_04' = ANY(tm_agg.slots) THEN sc.test_04 ELSE NULL END AS cc_s4,
        CASE WHEN 'test_05' = ANY(tm_agg.slots) THEN sc.test_05 ELSE NULL END AS cc_s5,
        CASE WHEN 'test_06' = ANY(tm_agg.slots) THEN sc.test_06 ELSE NULL END AS cc_s6,
        CASE WHEN 'test_07' = ANY(tm_agg.slots) THEN sc.test_07 ELSE NULL END AS cc_s7,
        CASE WHEN 'test_08' = ANY(tm_agg.slots) THEN sc.test_08 ELSE NULL END AS cc_s8
    FROM student_master sm
    LEFT JOIN scores_cc sc ON sc.prn = sm.prn
    CROSS JOIN LATERAL (
        SELECT array_agg(column_slot) AS slots, COUNT(*) AS n_configured, SUM(max_marks) AS raw_max
        FROM test_mapping WHERE batch_name = sm.batch_id AND category_code = 'CC' AND is_active = TRUE
    ) tm_agg
    WHERE sm.is_active = TRUE
),
-- ── IA ───────────────────────────────────────────────────────────────────────
ia_scores AS (
    SELECT
        sm.prn,
        tm_agg.n_configured,
        tm_agg.raw_max,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) THEN COALESCE(sc.test_01, 0) ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) THEN COALESCE(sc.test_02, 0) ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) THEN COALESCE(sc.test_03, 0) ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) THEN COALESCE(sc.test_04, 0) ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) THEN COALESCE(sc.test_05, 0) ELSE 0 END +
         CASE WHEN 'test_06' = ANY(tm_agg.slots) THEN COALESCE(sc.test_06, 0) ELSE 0 END +
         CASE WHEN 'test_07' = ANY(tm_agg.slots) THEN COALESCE(sc.test_07, 0) ELSE 0 END +
         CASE WHEN 'test_08' = ANY(tm_agg.slots) THEN COALESCE(sc.test_08, 0) ELSE 0 END
        ) AS ia_raw_sum,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) AND sc.test_01 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) AND sc.test_02 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) AND sc.test_03 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) AND sc.test_04 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) AND sc.test_05 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_06' = ANY(tm_agg.slots) AND sc.test_06 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_07' = ANY(tm_agg.slots) AND sc.test_07 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_08' = ANY(tm_agg.slots) AND sc.test_08 IS NOT NULL THEN 1 ELSE 0 END
        ) AS ia_subtests_entered,
        CASE WHEN 'test_01' = ANY(tm_agg.slots) THEN sc.test_01 ELSE NULL END AS ia_s1,
        CASE WHEN 'test_02' = ANY(tm_agg.slots) THEN sc.test_02 ELSE NULL END AS ia_s2,
        CASE WHEN 'test_03' = ANY(tm_agg.slots) THEN sc.test_03 ELSE NULL END AS ia_s3,
        CASE WHEN 'test_04' = ANY(tm_agg.slots) THEN sc.test_04 ELSE NULL END AS ia_s4,
        CASE WHEN 'test_05' = ANY(tm_agg.slots) THEN sc.test_05 ELSE NULL END AS ia_s5,
        CASE WHEN 'test_06' = ANY(tm_agg.slots) THEN sc.test_06 ELSE NULL END AS ia_s6,
        CASE WHEN 'test_07' = ANY(tm_agg.slots) THEN sc.test_07 ELSE NULL END AS ia_s7,
        CASE WHEN 'test_08' = ANY(tm_agg.slots) THEN sc.test_08 ELSE NULL END AS ia_s8
    FROM student_master sm
    LEFT JOIN scores_ia sc ON sc.prn = sm.prn
    CROSS JOIN LATERAL (
        SELECT array_agg(column_slot) AS slots, COUNT(*) AS n_configured, SUM(max_marks) AS raw_max
        FROM test_mapping WHERE batch_name = sm.batch_id AND category_code = 'IA' AND is_active = TRUE
    ) tm_agg
    WHERE sm.is_active = TRUE
),
-- ── AP ───────────────────────────────────────────────────────────────────────
ap_scores AS (
    SELECT
        sm.prn,
        tm_agg.n_configured,
        tm_agg.raw_max,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) THEN COALESCE(sc.test_01, 0) ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) THEN COALESCE(sc.test_02, 0) ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) THEN COALESCE(sc.test_03, 0) ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) THEN COALESCE(sc.test_04, 0) ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) THEN COALESCE(sc.test_05, 0) ELSE 0 END +
         CASE WHEN 'test_06' = ANY(tm_agg.slots) THEN COALESCE(sc.test_06, 0) ELSE 0 END +
         CASE WHEN 'test_07' = ANY(tm_agg.slots) THEN COALESCE(sc.test_07, 0) ELSE 0 END +
         CASE WHEN 'test_08' = ANY(tm_agg.slots) THEN COALESCE(sc.test_08, 0) ELSE 0 END +
         CASE WHEN 'test_09' = ANY(tm_agg.slots) THEN COALESCE(sc.test_09, 0) ELSE 0 END +
         CASE WHEN 'test_10' = ANY(tm_agg.slots) THEN COALESCE(sc.test_10, 0) ELSE 0 END +
         CASE WHEN 'test_11' = ANY(tm_agg.slots) THEN COALESCE(sc.test_11, 0) ELSE 0 END +
         CASE WHEN 'test_12' = ANY(tm_agg.slots) THEN COALESCE(sc.test_12, 0) ELSE 0 END +
         CASE WHEN 'test_13' = ANY(tm_agg.slots) THEN COALESCE(sc.test_13, 0) ELSE 0 END +
         CASE WHEN 'test_14' = ANY(tm_agg.slots) THEN COALESCE(sc.test_14, 0) ELSE 0 END +
         CASE WHEN 'test_15' = ANY(tm_agg.slots) THEN COALESCE(sc.test_15, 0) ELSE 0 END +
         CASE WHEN 'test_16' = ANY(tm_agg.slots) THEN COALESCE(sc.test_16, 0) ELSE 0 END +
         CASE WHEN 'test_17' = ANY(tm_agg.slots) THEN COALESCE(sc.test_17, 0) ELSE 0 END +
         CASE WHEN 'test_18' = ANY(tm_agg.slots) THEN COALESCE(sc.test_18, 0) ELSE 0 END +
         CASE WHEN 'test_19' = ANY(tm_agg.slots) THEN COALESCE(sc.test_19, 0) ELSE 0 END +
         CASE WHEN 'test_20' = ANY(tm_agg.slots) THEN COALESCE(sc.test_20, 0) ELSE 0 END
        ) AS ap_raw_sum,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) AND sc.test_01 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) AND sc.test_02 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) AND sc.test_03 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) AND sc.test_04 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) AND sc.test_05 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_06' = ANY(tm_agg.slots) AND sc.test_06 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_07' = ANY(tm_agg.slots) AND sc.test_07 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_08' = ANY(tm_agg.slots) AND sc.test_08 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_09' = ANY(tm_agg.slots) AND sc.test_09 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_10' = ANY(tm_agg.slots) AND sc.test_10 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_11' = ANY(tm_agg.slots) AND sc.test_11 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_12' = ANY(tm_agg.slots) AND sc.test_12 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_13' = ANY(tm_agg.slots) AND sc.test_13 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_14' = ANY(tm_agg.slots) AND sc.test_14 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_15' = ANY(tm_agg.slots) AND sc.test_15 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_16' = ANY(tm_agg.slots) AND sc.test_16 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_17' = ANY(tm_agg.slots) AND sc.test_17 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_18' = ANY(tm_agg.slots) AND sc.test_18 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_19' = ANY(tm_agg.slots) AND sc.test_19 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_20' = ANY(tm_agg.slots) AND sc.test_20 IS NOT NULL THEN 1 ELSE 0 END
        ) AS ap_subtests_entered,
        CASE WHEN 'test_01' = ANY(tm_agg.slots) THEN sc.test_01 ELSE NULL END AS ap_s1,
        CASE WHEN 'test_02' = ANY(tm_agg.slots) THEN sc.test_02 ELSE NULL END AS ap_s2,
        CASE WHEN 'test_03' = ANY(tm_agg.slots) THEN sc.test_03 ELSE NULL END AS ap_s3,
        CASE WHEN 'test_04' = ANY(tm_agg.slots) THEN sc.test_04 ELSE NULL END AS ap_s4,
        CASE WHEN 'test_05' = ANY(tm_agg.slots) THEN sc.test_05 ELSE NULL END AS ap_s5,
        CASE WHEN 'test_06' = ANY(tm_agg.slots) THEN sc.test_06 ELSE NULL END AS ap_s6,
        CASE WHEN 'test_07' = ANY(tm_agg.slots) THEN sc.test_07 ELSE NULL END AS ap_s7,
        CASE WHEN 'test_08' = ANY(tm_agg.slots) THEN sc.test_08 ELSE NULL END AS ap_s8,
        CASE WHEN 'test_09' = ANY(tm_agg.slots) THEN sc.test_09 ELSE NULL END AS ap_s9,
        CASE WHEN 'test_10' = ANY(tm_agg.slots) THEN sc.test_10 ELSE NULL END AS ap_s10,
        CASE WHEN 'test_11' = ANY(tm_agg.slots) THEN sc.test_11 ELSE NULL END AS ap_s11,
        CASE WHEN 'test_12' = ANY(tm_agg.slots) THEN sc.test_12 ELSE NULL END AS ap_s12,
        CASE WHEN 'test_13' = ANY(tm_agg.slots) THEN sc.test_13 ELSE NULL END AS ap_s13,
        CASE WHEN 'test_14' = ANY(tm_agg.slots) THEN sc.test_14 ELSE NULL END AS ap_s14,
        CASE WHEN 'test_15' = ANY(tm_agg.slots) THEN sc.test_15 ELSE NULL END AS ap_s15,
        CASE WHEN 'test_16' = ANY(tm_agg.slots) THEN sc.test_16 ELSE NULL END AS ap_s16,
        CASE WHEN 'test_17' = ANY(tm_agg.slots) THEN sc.test_17 ELSE NULL END AS ap_s17,
        CASE WHEN 'test_18' = ANY(tm_agg.slots) THEN sc.test_18 ELSE NULL END AS ap_s18,
        CASE WHEN 'test_19' = ANY(tm_agg.slots) THEN sc.test_19 ELSE NULL END AS ap_s19,
        CASE WHEN 'test_20' = ANY(tm_agg.slots) THEN sc.test_20 ELSE NULL END AS ap_s20
    FROM student_master sm
    LEFT JOIN scores_ap sc ON sc.prn = sm.prn
    CROSS JOIN LATERAL (
        SELECT array_agg(column_slot) AS slots, COUNT(*) AS n_configured, SUM(max_marks) AS raw_max
        FROM test_mapping WHERE batch_name = sm.batch_id AND category_code = 'AP' AND is_active = TRUE
    ) tm_agg
    WHERE sm.is_active = TRUE
),
-- ── SX ───────────────────────────────────────────────────────────────────────
sx_scores AS (
    SELECT
        sm.prn,
        tm_agg.n_configured,
        tm_agg.raw_max,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) THEN COALESCE(sc.test_01, 0) ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) THEN COALESCE(sc.test_02, 0) ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) THEN COALESCE(sc.test_03, 0) ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) THEN COALESCE(sc.test_04, 0) ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) THEN COALESCE(sc.test_05, 0) ELSE 0 END +
         CASE WHEN 'test_06' = ANY(tm_agg.slots) THEN COALESCE(sc.test_06, 0) ELSE 0 END +
         CASE WHEN 'test_07' = ANY(tm_agg.slots) THEN COALESCE(sc.test_07, 0) ELSE 0 END +
         CASE WHEN 'test_08' = ANY(tm_agg.slots) THEN COALESCE(sc.test_08, 0) ELSE 0 END +
         CASE WHEN 'test_09' = ANY(tm_agg.slots) THEN COALESCE(sc.test_09, 0) ELSE 0 END +
         CASE WHEN 'test_10' = ANY(tm_agg.slots) THEN COALESCE(sc.test_10, 0) ELSE 0 END
        ) AS sx_raw_sum,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) AND sc.test_01 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) AND sc.test_02 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) AND sc.test_03 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) AND sc.test_04 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) AND sc.test_05 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_06' = ANY(tm_agg.slots) AND sc.test_06 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_07' = ANY(tm_agg.slots) AND sc.test_07 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_08' = ANY(tm_agg.slots) AND sc.test_08 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_09' = ANY(tm_agg.slots) AND sc.test_09 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_10' = ANY(tm_agg.slots) AND sc.test_10 IS NOT NULL THEN 1 ELSE 0 END
        ) AS sx_subtests_entered,
        CASE WHEN 'test_01' = ANY(tm_agg.slots) THEN sc.test_01 ELSE NULL END AS sx_s1,
        CASE WHEN 'test_02' = ANY(tm_agg.slots) THEN sc.test_02 ELSE NULL END AS sx_s2,
        CASE WHEN 'test_03' = ANY(tm_agg.slots) THEN sc.test_03 ELSE NULL END AS sx_s3,
        CASE WHEN 'test_04' = ANY(tm_agg.slots) THEN sc.test_04 ELSE NULL END AS sx_s4,
        CASE WHEN 'test_05' = ANY(tm_agg.slots) THEN sc.test_05 ELSE NULL END AS sx_s5,
        CASE WHEN 'test_06' = ANY(tm_agg.slots) THEN sc.test_06 ELSE NULL END AS sx_s6,
        CASE WHEN 'test_07' = ANY(tm_agg.slots) THEN sc.test_07 ELSE NULL END AS sx_s7,
        CASE WHEN 'test_08' = ANY(tm_agg.slots) THEN sc.test_08 ELSE NULL END AS sx_s8,
        CASE WHEN 'test_09' = ANY(tm_agg.slots) THEN sc.test_09 ELSE NULL END AS sx_s9,
        CASE WHEN 'test_10' = ANY(tm_agg.slots) THEN sc.test_10 ELSE NULL END AS sx_s10
    FROM student_master sm
    LEFT JOIN scores_sx sc ON sc.prn = sm.prn
    CROSS JOIN LATERAL (
        SELECT array_agg(column_slot) AS slots, COUNT(*) AS n_configured, SUM(max_marks) AS raw_max
        FROM test_mapping WHERE batch_name = sm.batch_id AND category_code = 'SX' AND is_active = TRUE
    ) tm_agg
    WHERE sm.is_active = TRUE
),
-- ── PS ───────────────────────────────────────────────────────────────────────
ps_scores AS (
    SELECT
        sm.prn,
        tm_agg.n_configured,
        tm_agg.raw_max,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) THEN COALESCE(sc.test_01, 0) ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) THEN COALESCE(sc.test_02, 0) ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) THEN COALESCE(sc.test_03, 0) ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) THEN COALESCE(sc.test_04, 0) ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) THEN COALESCE(sc.test_05, 0) ELSE 0 END +
         CASE WHEN 'test_06' = ANY(tm_agg.slots) THEN COALESCE(sc.test_06, 0) ELSE 0 END +
         CASE WHEN 'test_07' = ANY(tm_agg.slots) THEN COALESCE(sc.test_07, 0) ELSE 0 END +
         CASE WHEN 'test_08' = ANY(tm_agg.slots) THEN COALESCE(sc.test_08, 0) ELSE 0 END +
         CASE WHEN 'test_09' = ANY(tm_agg.slots) THEN COALESCE(sc.test_09, 0) ELSE 0 END +
         CASE WHEN 'test_10' = ANY(tm_agg.slots) THEN COALESCE(sc.test_10, 0) ELSE 0 END
        ) AS ps_raw_sum,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) AND sc.test_01 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) AND sc.test_02 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) AND sc.test_03 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) AND sc.test_04 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) AND sc.test_05 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_06' = ANY(tm_agg.slots) AND sc.test_06 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_07' = ANY(tm_agg.slots) AND sc.test_07 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_08' = ANY(tm_agg.slots) AND sc.test_08 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_09' = ANY(tm_agg.slots) AND sc.test_09 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_10' = ANY(tm_agg.slots) AND sc.test_10 IS NOT NULL THEN 1 ELSE 0 END
        ) AS ps_subtests_entered
    FROM student_master sm
    LEFT JOIN scores_ps sc ON sc.prn = sm.prn
    CROSS JOIN LATERAL (
        SELECT array_agg(column_slot) AS slots, COUNT(*) AS n_configured, SUM(max_marks) AS raw_max
        FROM test_mapping WHERE batch_name = sm.batch_id AND category_code = 'PS' AND is_active = TRUE
    ) tm_agg
    WHERE sm.is_active = TRUE
),
-- ── GR ───────────────────────────────────────────────────────────────────────
gr_scores AS (
    SELECT
        sm.prn,
        tm_agg.n_configured,
        tm_agg.raw_max,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) THEN COALESCE(sc.test_01, 0) ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) THEN COALESCE(sc.test_02, 0) ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) THEN COALESCE(sc.test_03, 0) ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) THEN COALESCE(sc.test_04, 0) ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) THEN COALESCE(sc.test_05, 0) ELSE 0 END +
         CASE WHEN 'test_06' = ANY(tm_agg.slots) THEN COALESCE(sc.test_06, 0) ELSE 0 END +
         CASE WHEN 'test_07' = ANY(tm_agg.slots) THEN COALESCE(sc.test_07, 0) ELSE 0 END +
         CASE WHEN 'test_08' = ANY(tm_agg.slots) THEN COALESCE(sc.test_08, 0) ELSE 0 END +
         CASE WHEN 'test_09' = ANY(tm_agg.slots) THEN COALESCE(sc.test_09, 0) ELSE 0 END +
         CASE WHEN 'test_10' = ANY(tm_agg.slots) THEN COALESCE(sc.test_10, 0) ELSE 0 END
        ) AS gr_raw_sum,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) AND sc.test_01 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) AND sc.test_02 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) AND sc.test_03 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) AND sc.test_04 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) AND sc.test_05 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_06' = ANY(tm_agg.slots) AND sc.test_06 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_07' = ANY(tm_agg.slots) AND sc.test_07 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_08' = ANY(tm_agg.slots) AND sc.test_08 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_09' = ANY(tm_agg.slots) AND sc.test_09 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_10' = ANY(tm_agg.slots) AND sc.test_10 IS NOT NULL THEN 1 ELSE 0 END
        ) AS gr_subtests_entered
    FROM student_master sm
    LEFT JOIN scores_gr sc ON sc.prn = sm.prn
    CROSS JOIN LATERAL (
        SELECT array_agg(column_slot) AS slots, COUNT(*) AS n_configured, SUM(max_marks) AS raw_max
        FROM test_mapping WHERE batch_name = sm.batch_id AND category_code = 'GR' AND is_active = TRUE
    ) tm_agg
    WHERE sm.is_active = TRUE
),
-- ── TA ───────────────────────────────────────────────────────────────────────
ta_scores AS (
    SELECT
        sm.prn,
        tm_agg.n_configured,
        tm_agg.raw_max,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) THEN COALESCE(sc.test_01, 0) ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) THEN COALESCE(sc.test_02, 0) ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) THEN COALESCE(sc.test_03, 0) ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) THEN COALESCE(sc.test_04, 0) ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) THEN COALESCE(sc.test_05, 0) ELSE 0 END
        ) AS ta_raw_sum,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) AND sc.test_01 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) AND sc.test_02 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) AND sc.test_03 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) AND sc.test_04 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) AND sc.test_05 IS NOT NULL THEN 1 ELSE 0 END
        ) AS ta_subtests_entered,
        CASE WHEN 'test_01' = ANY(tm_agg.slots) THEN sc.test_01 ELSE NULL END AS ta_s1,
        CASE WHEN 'test_02' = ANY(tm_agg.slots) THEN sc.test_02 ELSE NULL END AS ta_s2,
        CASE WHEN 'test_03' = ANY(tm_agg.slots) THEN sc.test_03 ELSE NULL END AS ta_s3,
        CASE WHEN 'test_04' = ANY(tm_agg.slots) THEN sc.test_04 ELSE NULL END AS ta_s4,
        CASE WHEN 'test_05' = ANY(tm_agg.slots) THEN sc.test_05 ELSE NULL END AS ta_s5
    FROM student_master sm
    LEFT JOIN scores_ta sc ON sc.prn = sm.prn
    CROSS JOIN LATERAL (
        SELECT array_agg(column_slot) AS slots, COUNT(*) AS n_configured, SUM(max_marks) AS raw_max
        FROM test_mapping WHERE batch_name = sm.batch_id AND category_code = 'TA' AND is_active = TRUE
    ) tm_agg
    WHERE sm.is_active = TRUE
),
-- ── NA ───────────────────────────────────────────────────────────────────────
na_scores AS (
    SELECT
        sm.prn,
        tm_agg.n_configured,
        tm_agg.raw_max,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) THEN COALESCE(sc.test_01, 0) ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) THEN COALESCE(sc.test_02, 0) ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) THEN COALESCE(sc.test_03, 0) ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) THEN COALESCE(sc.test_04, 0) ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) THEN COALESCE(sc.test_05, 0) ELSE 0 END
        ) AS na_raw_sum,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) AND sc.test_01 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) AND sc.test_02 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) AND sc.test_03 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) AND sc.test_04 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) AND sc.test_05 IS NOT NULL THEN 1 ELSE 0 END
        ) AS na_subtests_entered,
        CASE WHEN 'test_01' = ANY(tm_agg.slots) THEN sc.test_01 ELSE NULL END AS na_s1,
        CASE WHEN 'test_02' = ANY(tm_agg.slots) THEN sc.test_02 ELSE NULL END AS na_s2,
        CASE WHEN 'test_03' = ANY(tm_agg.slots) THEN sc.test_03 ELSE NULL END AS na_s3,
        CASE WHEN 'test_04' = ANY(tm_agg.slots) THEN sc.test_04 ELSE NULL END AS na_s4,
        CASE WHEN 'test_05' = ANY(tm_agg.slots) THEN sc.test_05 ELSE NULL END AS na_s5
    FROM student_master sm
    LEFT JOIN scores_na sc ON sc.prn = sm.prn
    CROSS JOIN LATERAL (
        SELECT array_agg(column_slot) AS slots, COUNT(*) AS n_configured, SUM(max_marks) AS raw_max
        FROM test_mapping WHERE batch_name = sm.batch_id AND category_code = 'NA' AND is_active = TRUE
    ) tm_agg
    WHERE sm.is_active = TRUE
),
-- ── IN ───────────────────────────────────────────────────────────────────────
in_scores AS (
    SELECT
        sm.prn,
        tm_agg.n_configured,
        tm_agg.raw_max,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) THEN COALESCE(sc.test_01, 0) ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) THEN COALESCE(sc.test_02, 0) ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) THEN COALESCE(sc.test_03, 0) ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) THEN COALESCE(sc.test_04, 0) ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) THEN COALESCE(sc.test_05, 0) ELSE 0 END
        ) AS in_raw_sum,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) AND sc.test_01 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) AND sc.test_02 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) AND sc.test_03 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) AND sc.test_04 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) AND sc.test_05 IS NOT NULL THEN 1 ELSE 0 END
        ) AS in_subtests_entered,
        CASE WHEN 'test_01' = ANY(tm_agg.slots) THEN sc.test_01 ELSE NULL END AS in_s1,
        CASE WHEN 'test_02' = ANY(tm_agg.slots) THEN sc.test_02 ELSE NULL END AS in_s2,
        CASE WHEN 'test_03' = ANY(tm_agg.slots) THEN sc.test_03 ELSE NULL END AS in_s3,
        CASE WHEN 'test_04' = ANY(tm_agg.slots) THEN sc.test_04 ELSE NULL END AS in_s4,
        CASE WHEN 'test_05' = ANY(tm_agg.slots) THEN sc.test_05 ELSE NULL END AS in_s5
    FROM student_master sm
    LEFT JOIN scores_in sc ON sc.prn = sm.prn
    CROSS JOIN LATERAL (
        SELECT array_agg(column_slot) AS slots, COUNT(*) AS n_configured, SUM(max_marks) AS raw_max
        FROM test_mapping WHERE batch_name = sm.batch_id AND category_code = 'IN' AND is_active = TRUE
    ) tm_agg
    WHERE sm.is_active = TRUE
),
-- ── AS ───────────────────────────────────────────────────────────────────────
as_scores AS (
    SELECT
        sm.prn,
        tm_agg.n_configured,
        tm_agg.raw_max,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) THEN COALESCE(sc.test_01, 0) ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) THEN COALESCE(sc.test_02, 0) ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) THEN COALESCE(sc.test_03, 0) ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) THEN COALESCE(sc.test_04, 0) ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) THEN COALESCE(sc.test_05, 0) ELSE 0 END +
         CASE WHEN 'test_06' = ANY(tm_agg.slots) THEN COALESCE(sc.test_06, 0) ELSE 0 END +
         CASE WHEN 'test_07' = ANY(tm_agg.slots) THEN COALESCE(sc.test_07, 0) ELSE 0 END +
         CASE WHEN 'test_08' = ANY(tm_agg.slots) THEN COALESCE(sc.test_08, 0) ELSE 0 END +
         CASE WHEN 'test_09' = ANY(tm_agg.slots) THEN COALESCE(sc.test_09, 0) ELSE 0 END +
         CASE WHEN 'test_10' = ANY(tm_agg.slots) THEN COALESCE(sc.test_10, 0) ELSE 0 END +
         CASE WHEN 'test_11' = ANY(tm_agg.slots) THEN COALESCE(sc.test_11, 0) ELSE 0 END +
         CASE WHEN 'test_12' = ANY(tm_agg.slots) THEN COALESCE(sc.test_12, 0) ELSE 0 END +
         CASE WHEN 'test_13' = ANY(tm_agg.slots) THEN COALESCE(sc.test_13, 0) ELSE 0 END +
         CASE WHEN 'test_14' = ANY(tm_agg.slots) THEN COALESCE(sc.test_14, 0) ELSE 0 END +
         CASE WHEN 'test_15' = ANY(tm_agg.slots) THEN COALESCE(sc.test_15, 0) ELSE 0 END +
         CASE WHEN 'test_16' = ANY(tm_agg.slots) THEN COALESCE(sc.test_16, 0) ELSE 0 END +
         CASE WHEN 'test_17' = ANY(tm_agg.slots) THEN COALESCE(sc.test_17, 0) ELSE 0 END +
         CASE WHEN 'test_18' = ANY(tm_agg.slots) THEN COALESCE(sc.test_18, 0) ELSE 0 END +
         CASE WHEN 'test_19' = ANY(tm_agg.slots) THEN COALESCE(sc.test_19, 0) ELSE 0 END +
         CASE WHEN 'test_20' = ANY(tm_agg.slots) THEN COALESCE(sc.test_20, 0) ELSE 0 END +
         CASE WHEN 'test_21' = ANY(tm_agg.slots) THEN COALESCE(sc.test_21, 0) ELSE 0 END +
         CASE WHEN 'test_22' = ANY(tm_agg.slots) THEN COALESCE(sc.test_22, 0) ELSE 0 END +
         CASE WHEN 'test_23' = ANY(tm_agg.slots) THEN COALESCE(sc.test_23, 0) ELSE 0 END +
         CASE WHEN 'test_24' = ANY(tm_agg.slots) THEN COALESCE(sc.test_24, 0) ELSE 0 END +
         CASE WHEN 'test_25' = ANY(tm_agg.slots) THEN COALESCE(sc.test_25, 0) ELSE 0 END +
         CASE WHEN 'test_26' = ANY(tm_agg.slots) THEN COALESCE(sc.test_26, 0) ELSE 0 END +
         CASE WHEN 'test_27' = ANY(tm_agg.slots) THEN COALESCE(sc.test_27, 0) ELSE 0 END +
         CASE WHEN 'test_28' = ANY(tm_agg.slots) THEN COALESCE(sc.test_28, 0) ELSE 0 END +
         CASE WHEN 'test_29' = ANY(tm_agg.slots) THEN COALESCE(sc.test_29, 0) ELSE 0 END +
         CASE WHEN 'test_30' = ANY(tm_agg.slots) THEN COALESCE(sc.test_30, 0) ELSE 0 END
        ) AS as_raw_sum,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) AND sc.test_01 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) AND sc.test_02 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) AND sc.test_03 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) AND sc.test_04 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) AND sc.test_05 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_06' = ANY(tm_agg.slots) AND sc.test_06 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_07' = ANY(tm_agg.slots) AND sc.test_07 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_08' = ANY(tm_agg.slots) AND sc.test_08 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_09' = ANY(tm_agg.slots) AND sc.test_09 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_10' = ANY(tm_agg.slots) AND sc.test_10 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_11' = ANY(tm_agg.slots) AND sc.test_11 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_12' = ANY(tm_agg.slots) AND sc.test_12 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_13' = ANY(tm_agg.slots) AND sc.test_13 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_14' = ANY(tm_agg.slots) AND sc.test_14 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_15' = ANY(tm_agg.slots) AND sc.test_15 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_16' = ANY(tm_agg.slots) AND sc.test_16 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_17' = ANY(tm_agg.slots) AND sc.test_17 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_18' = ANY(tm_agg.slots) AND sc.test_18 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_19' = ANY(tm_agg.slots) AND sc.test_19 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_20' = ANY(tm_agg.slots) AND sc.test_20 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_21' = ANY(tm_agg.slots) AND sc.test_21 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_22' = ANY(tm_agg.slots) AND sc.test_22 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_23' = ANY(tm_agg.slots) AND sc.test_23 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_24' = ANY(tm_agg.slots) AND sc.test_24 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_25' = ANY(tm_agg.slots) AND sc.test_25 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_26' = ANY(tm_agg.slots) AND sc.test_26 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_27' = ANY(tm_agg.slots) AND sc.test_27 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_28' = ANY(tm_agg.slots) AND sc.test_28 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_29' = ANY(tm_agg.slots) AND sc.test_29 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_30' = ANY(tm_agg.slots) AND sc.test_30 IS NOT NULL THEN 1 ELSE 0 END
        ) AS as_subtests_entered
    FROM student_master sm
    LEFT JOIN scores_as sc ON sc.prn = sm.prn
    CROSS JOIN LATERAL (
        SELECT array_agg(column_slot) AS slots, COUNT(*) AS n_configured, SUM(max_marks) AS raw_max
        FROM test_mapping WHERE batch_name = sm.batch_id AND category_code = 'AS' AND is_active = TRUE
    ) tm_agg
    WHERE sm.is_active = TRUE
),
-- ── PQ ───────────────────────────────────────────────────────────────────────
pq_scores AS (
    SELECT
        sm.prn,
        tm_agg.n_configured,
        tm_agg.raw_max,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) THEN COALESCE(sc.test_01, 0) ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) THEN COALESCE(sc.test_02, 0) ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) THEN COALESCE(sc.test_03, 0) ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) THEN COALESCE(sc.test_04, 0) ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) THEN COALESCE(sc.test_05, 0) ELSE 0 END +
         CASE WHEN 'test_06' = ANY(tm_agg.slots) THEN COALESCE(sc.test_06, 0) ELSE 0 END +
         CASE WHEN 'test_07' = ANY(tm_agg.slots) THEN COALESCE(sc.test_07, 0) ELSE 0 END +
         CASE WHEN 'test_08' = ANY(tm_agg.slots) THEN COALESCE(sc.test_08, 0) ELSE 0 END +
         CASE WHEN 'test_09' = ANY(tm_agg.slots) THEN COALESCE(sc.test_09, 0) ELSE 0 END +
         CASE WHEN 'test_10' = ANY(tm_agg.slots) THEN COALESCE(sc.test_10, 0) ELSE 0 END +
         CASE WHEN 'test_11' = ANY(tm_agg.slots) THEN COALESCE(sc.test_11, 0) ELSE 0 END +
         CASE WHEN 'test_12' = ANY(tm_agg.slots) THEN COALESCE(sc.test_12, 0) ELSE 0 END +
         CASE WHEN 'test_13' = ANY(tm_agg.slots) THEN COALESCE(sc.test_13, 0) ELSE 0 END +
         CASE WHEN 'test_14' = ANY(tm_agg.slots) THEN COALESCE(sc.test_14, 0) ELSE 0 END +
         CASE WHEN 'test_15' = ANY(tm_agg.slots) THEN COALESCE(sc.test_15, 0) ELSE 0 END +
         CASE WHEN 'test_16' = ANY(tm_agg.slots) THEN COALESCE(sc.test_16, 0) ELSE 0 END +
         CASE WHEN 'test_17' = ANY(tm_agg.slots) THEN COALESCE(sc.test_17, 0) ELSE 0 END +
         CASE WHEN 'test_18' = ANY(tm_agg.slots) THEN COALESCE(sc.test_18, 0) ELSE 0 END +
         CASE WHEN 'test_19' = ANY(tm_agg.slots) THEN COALESCE(sc.test_19, 0) ELSE 0 END +
         CASE WHEN 'test_20' = ANY(tm_agg.slots) THEN COALESCE(sc.test_20, 0) ELSE 0 END +
         CASE WHEN 'test_21' = ANY(tm_agg.slots) THEN COALESCE(sc.test_21, 0) ELSE 0 END +
         CASE WHEN 'test_22' = ANY(tm_agg.slots) THEN COALESCE(sc.test_22, 0) ELSE 0 END +
         CASE WHEN 'test_23' = ANY(tm_agg.slots) THEN COALESCE(sc.test_23, 0) ELSE 0 END +
         CASE WHEN 'test_24' = ANY(tm_agg.slots) THEN COALESCE(sc.test_24, 0) ELSE 0 END +
         CASE WHEN 'test_25' = ANY(tm_agg.slots) THEN COALESCE(sc.test_25, 0) ELSE 0 END +
         CASE WHEN 'test_26' = ANY(tm_agg.slots) THEN COALESCE(sc.test_26, 0) ELSE 0 END +
         CASE WHEN 'test_27' = ANY(tm_agg.slots) THEN COALESCE(sc.test_27, 0) ELSE 0 END +
         CASE WHEN 'test_28' = ANY(tm_agg.slots) THEN COALESCE(sc.test_28, 0) ELSE 0 END +
         CASE WHEN 'test_29' = ANY(tm_agg.slots) THEN COALESCE(sc.test_29, 0) ELSE 0 END +
         CASE WHEN 'test_30' = ANY(tm_agg.slots) THEN COALESCE(sc.test_30, 0) ELSE 0 END
        ) AS pq_raw_sum,
        (CASE WHEN 'test_01' = ANY(tm_agg.slots) AND sc.test_01 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_02' = ANY(tm_agg.slots) AND sc.test_02 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_03' = ANY(tm_agg.slots) AND sc.test_03 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_04' = ANY(tm_agg.slots) AND sc.test_04 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_05' = ANY(tm_agg.slots) AND sc.test_05 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_06' = ANY(tm_agg.slots) AND sc.test_06 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_07' = ANY(tm_agg.slots) AND sc.test_07 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_08' = ANY(tm_agg.slots) AND sc.test_08 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_09' = ANY(tm_agg.slots) AND sc.test_09 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_10' = ANY(tm_agg.slots) AND sc.test_10 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_11' = ANY(tm_agg.slots) AND sc.test_11 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_12' = ANY(tm_agg.slots) AND sc.test_12 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_13' = ANY(tm_agg.slots) AND sc.test_13 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_14' = ANY(tm_agg.slots) AND sc.test_14 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_15' = ANY(tm_agg.slots) AND sc.test_15 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_16' = ANY(tm_agg.slots) AND sc.test_16 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_17' = ANY(tm_agg.slots) AND sc.test_17 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_18' = ANY(tm_agg.slots) AND sc.test_18 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_19' = ANY(tm_agg.slots) AND sc.test_19 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_20' = ANY(tm_agg.slots) AND sc.test_20 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_21' = ANY(tm_agg.slots) AND sc.test_21 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_22' = ANY(tm_agg.slots) AND sc.test_22 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_23' = ANY(tm_agg.slots) AND sc.test_23 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_24' = ANY(tm_agg.slots) AND sc.test_24 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_25' = ANY(tm_agg.slots) AND sc.test_25 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_26' = ANY(tm_agg.slots) AND sc.test_26 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_27' = ANY(tm_agg.slots) AND sc.test_27 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_28' = ANY(tm_agg.slots) AND sc.test_28 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_29' = ANY(tm_agg.slots) AND sc.test_29 IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN 'test_30' = ANY(tm_agg.slots) AND sc.test_30 IS NOT NULL THEN 1 ELSE 0 END
        ) AS pq_subtests_entered
    FROM student_master sm
    LEFT JOIN scores_pq sc ON sc.prn = sm.prn
    CROSS JOIN LATERAL (
        SELECT array_agg(column_slot) AS slots, COUNT(*) AS n_configured, SUM(max_marks) AS raw_max
        FROM test_mapping WHERE batch_name = sm.batch_id AND category_code = 'PQ' AND is_active = TRUE
    ) tm_agg
    WHERE sm.is_active = TRUE
),
-- ── SCALING ───────────────────────────────────────────────────────────────────
scaled AS (
    SELECT
        sm.prn, sm.student_full_name, sm.batch_id AS batch_name, sm.course_id AS course_code, sm.centre_id AS centre_code,
        cc.cc_raw_sum AS cc_scored, (cc.n_configured * 40) AS cc_max, cc.cc_s1, cc.cc_s2, cc.cc_s3, cc.cc_s4, cc.cc_s5, cc.cc_s6, cc.cc_s7, cc.cc_s8, cc.cc_subtests_entered,
        ia.ia_raw_sum AS ia_scored, (ia.n_configured * 60) AS ia_max, ia.ia_s1, ia.ia_s2, ia.ia_s3, ia.ia_s4, ia.ia_s5, ia.ia_s6, ia.ia_s7, ia.ia_s8, ia.ia_subtests_entered,
        CASE WHEN ap.n_configured > 0 THEN ROUND(ap.ap_raw_sum / NULLIF(ap.n_configured * 60.0, 0) * 200, 2) ELSE 0 END AS ap_scored,
        CASE WHEN ap.n_configured > 0 THEN ROUND(ap.n_configured::numeric / 20 * 200, 2) ELSE 0 END AS ap_max,
        ap.ap_s1, ap.ap_s2, ap.ap_s3, ap.ap_s4, ap.ap_s5, ap.ap_s6, ap.ap_s7, ap.ap_s8, ap.ap_s9, ap.ap_s10,
        ap.ap_s11, ap.ap_s12, ap.ap_s13, ap.ap_s14, ap.ap_s15, ap.ap_s16, ap.ap_s17, ap.ap_s18, ap.ap_s19, ap.ap_s20,
        ap.ap_subtests_entered, ap.n_configured AS ap_n_configured,
        CASE WHEN sx.n_configured > 0 THEN ROUND(sx.sx_raw_sum / NULLIF(sx.n_configured * 60.0, 0) * 100, 2) ELSE 0 END AS sx_scored,
        CASE WHEN sx.n_configured > 0 THEN ROUND(sx.n_configured::numeric / 10 * 100, 2) ELSE 0 END AS sx_max,
        sx.sx_s1, sx.sx_s2, sx.sx_s3, sx.sx_s4, sx.sx_s5, sx.sx_s6, sx.sx_s7, sx.sx_s8, sx.sx_s9, sx.sx_s10,
        sx.sx_subtests_entered, sx.n_configured AS sx_n_configured,
        ps.ps_raw_sum AS ps_scored, (ps.n_configured * 10) AS ps_max, ps.ps_subtests_entered,
        gr.gr_raw_sum AS gr_scored, (gr.n_configured * 10) AS gr_max, gr.gr_subtests_entered,
        CASE WHEN ta.n_configured > 0 THEN ROUND(ta.ta_raw_sum / NULLIF(ta.n_configured * 10.0, 0) * 100, 2) ELSE 0 END AS ta_scored,
        CASE WHEN ta.n_configured > 0 THEN ROUND(ta.n_configured::numeric / 5 * 100, 2) ELSE 0 END AS ta_max,
        ta.ta_s1, ta.ta_s2, ta.ta_s3, ta.ta_s4, ta.ta_s5, ta.ta_subtests_entered, ta.n_configured AS ta_n_configured,
        CASE WHEN na.n_configured > 0 THEN ROUND(na.na_raw_sum / NULLIF(na.n_configured * 10.0, 0) * 100, 2) ELSE 0 END AS na_scored,
        CASE WHEN na.n_configured > 0 THEN ROUND(na.n_configured::numeric / 5 * 100, 2) ELSE 0 END AS na_max,
        na.na_s1, na.na_s2, na.na_s3, na.na_s4, na.na_s5, na.na_subtests_entered, na.n_configured AS na_n_configured,
        in_.in_raw_sum AS in_scored, (in_.n_configured * 10) AS in_max,
        in_.in_s1, in_.in_s2, in_.in_s3, in_.in_s4, in_.in_s5, in_.in_subtests_entered, in_.n_configured AS in_n_configured,
        as_.as_raw_sum AS as_scored, (as_.n_configured * 10) AS as_max, as_.as_subtests_entered, as_.n_configured AS as_n_configured,
        pq.pq_raw_sum AS pq_scored, (pq.n_configured * 10) AS pq_max, pq.pq_subtests_entered, pq.n_configured AS pq_n_configured
    FROM student_master sm
    JOIN cc_scores cc ON cc.prn = sm.prn
    JOIN ia_scores ia ON ia.prn = sm.prn
    JOIN ap_scores ap ON ap.prn = sm.prn
    JOIN sx_scores sx ON sx.prn = sm.prn
    JOIN ps_scores ps ON ps.prn = sm.prn
    JOIN gr_scores gr ON gr.prn = sm.prn
    JOIN ta_scores ta ON ta.prn = sm.prn
    JOIN na_scores na ON na.prn = sm.prn
    JOIN in_scores in_ ON in_.prn = sm.prn
    JOIN as_scores as_ ON as_.prn = sm.prn
    JOIN pq_scores pq ON pq.prn = sm.prn
    WHERE sm.is_active = TRUE
),
-- ── CUTOFFS ──────────────────────────────────────────────────────────────────
cutoffs AS (
    SELECT
        prn,
        CASE WHEN cc_max = 0 THEN FALSE
             WHEN ((cc_s1 IS NOT NULL AND cc_s1 < 16) OR (cc_s2 IS NOT NULL AND cc_s2 < 16) OR (cc_s3 IS NOT NULL AND cc_s3 < 16) OR (cc_s4 IS NOT NULL AND cc_s4 < 16) OR
                   (cc_s5 IS NOT NULL AND cc_s5 < 16) OR (cc_s6 IS NOT NULL AND cc_s6 < 16) OR (cc_s7 IS NOT NULL AND cc_s7 < 16) OR (cc_s8 IS NOT NULL AND cc_s8 < 16)
                  ) THEN FALSE
             WHEN ROUND(cc_scored * 100.0 / NULLIF(cc_max, 0), 2) >= 65 THEN TRUE
             ELSE FALSE
        END AS cc_cutoff_met,
        CASE WHEN ia_max = 0 THEN FALSE
             WHEN ((ia_s1 IS NOT NULL AND ia_s1 < 24) OR (ia_s2 IS NOT NULL AND ia_s2 < 24) OR (ia_s3 IS NOT NULL AND ia_s3 < 24) OR (ia_s4 IS NOT NULL AND ia_s4 < 24) OR
                   (ia_s5 IS NOT NULL AND ia_s5 < 24) OR (ia_s6 IS NOT NULL AND ia_s6 < 24) OR (ia_s7 IS NOT NULL AND ia_s7 < 24) OR (ia_s8 IS NOT NULL AND ia_s8 < 24)
                  ) THEN FALSE
             WHEN ROUND(ia_scored * 100.0 / NULLIF(ia_max, 0), 2) >= 65 THEN TRUE
             ELSE FALSE
        END AS ia_cutoff_met,
        CASE WHEN ap_n_configured = 0 THEN NULL
             WHEN ((ap_s1 IS NOT NULL AND ap_s1 < 48) OR (ap_s2 IS NOT NULL AND ap_s2 < 48) OR (ap_s3 IS NOT NULL AND ap_s3 < 48) OR (ap_s4 IS NOT NULL AND ap_s4 < 48) OR (ap_s5 IS NOT NULL AND ap_s5 < 48) OR
                   (ap_s6 IS NOT NULL AND ap_s6 < 48) OR (ap_s7 IS NOT NULL AND ap_s7 < 48) OR (ap_s8 IS NOT NULL AND ap_s8 < 48) OR (ap_s9 IS NOT NULL AND ap_s9 < 48) OR (ap_s10 IS NOT NULL AND ap_s10 < 48) OR
                   (ap_s11 IS NOT NULL AND ap_s11 < 48) OR (ap_s12 IS NOT NULL AND ap_s12 < 48) OR (ap_s13 IS NOT NULL AND ap_s13 < 48) OR (ap_s14 IS NOT NULL AND ap_s14 < 48) OR (ap_s15 IS NOT NULL AND ap_s15 < 48) OR
                   (ap_s16 IS NOT NULL AND ap_s16 < 48) OR (ap_s17 IS NOT NULL AND ap_s17 < 48) OR (ap_s18 IS NOT NULL AND ap_s18 < 48) OR (ap_s19 IS NOT NULL AND ap_s19 < 48) OR (ap_s20 IS NOT NULL AND ap_s20 < 48)
                  ) THEN FALSE
             ELSE TRUE
        END AS ap_cutoff_met,
        CASE WHEN sx_n_configured = 0 THEN NULL
             WHEN ((sx_s1 IS NOT NULL AND sx_s1 < 30) OR (sx_s2 IS NOT NULL AND sx_s2 < 30) OR (sx_s3 IS NOT NULL AND sx_s3 < 30) OR (sx_s4 IS NOT NULL AND sx_s4 < 30) OR (sx_s5 IS NOT NULL AND sx_s5 < 30) OR
                   (sx_s6 IS NOT NULL AND sx_s6 < 30) OR (sx_s7 IS NOT NULL AND sx_s7 < 30) OR (sx_s8 IS NOT NULL AND sx_s8 < 30) OR (sx_s9 IS NOT NULL AND sx_s9 < 30) OR (sx_s10 IS NOT NULL AND sx_s10 < 30)
                  ) THEN FALSE
             ELSE TRUE
        END AS sx_cutoff_met,
        CASE WHEN ps_max = 0 THEN NULL WHEN ROUND(ps_scored * 100.0 / NULLIF(ps_max, 0), 2) >= 50 THEN TRUE ELSE FALSE END AS ps_cutoff_met,
        CASE WHEN gr_max = 0 THEN NULL WHEN ROUND(gr_scored * 100.0 / NULLIF(gr_max, 0), 2) >= 50 THEN TRUE ELSE FALSE END AS gr_cutoff_met,
        CASE WHEN ta_n_configured = 0 THEN NULL
             WHEN ((ta_s1 IS NOT NULL AND ta_s1 < 4) OR (ta_s2 IS NOT NULL AND ta_s2 < 4) OR (ta_s3 IS NOT NULL AND ta_s3 < 4) OR (ta_s4 IS NOT NULL AND ta_s4 < 4) OR (ta_s5 IS NOT NULL AND ta_s5 < 4)
                  ) THEN FALSE
             WHEN ROUND(ta_scored * 100.0 / NULLIF(ta_max, 0), 2) >= 40 THEN TRUE
             ELSE FALSE
        END AS ta_cutoff_met,
        CASE WHEN na_n_configured = 0 THEN NULL
             WHEN ((na_s1 IS NOT NULL AND na_s1 < 4) OR (na_s2 IS NOT NULL AND na_s2 < 4) OR (na_s3 IS NOT NULL AND na_s3 < 4) OR (na_s4 IS NOT NULL AND na_s4 < 4) OR (na_s5 IS NOT NULL AND na_s5 < 4)
                  ) THEN FALSE
             WHEN ROUND(na_scored * 100.0 / NULLIF(na_max, 0), 2) >= 40 THEN TRUE
             ELSE FALSE
        END AS na_cutoff_met,
        CASE WHEN in_n_configured < 5 THEN NULL WHEN in_subtests_entered < 5 THEN NULL
             WHEN ((in_s1 IS NOT NULL AND in_s1 < 8) OR (in_s2 IS NOT NULL AND in_s2 < 8) OR (in_s3 IS NOT NULL AND in_s3 < 8) OR (in_s4 IS NOT NULL AND in_s4 < 8) OR (in_s5 IS NOT NULL AND in_s5 < 8)
                  ) THEN FALSE
             ELSE TRUE
        END AS in_cutoff_met,
        CASE WHEN as_subtests_entered < 25 THEN NULL ELSE TRUE END AS as_cutoff_met, -- Placeholder, logic in Python
        CASE WHEN pq_n_configured < 30 OR pq_subtests_entered < 30 THEN NULL ELSE TRUE END AS pq_cutoff_met -- Placeholder, logic in Python
    FROM scaled
),
-- ── FINAL RESULTS ────────────────────────────────────────────────────────────
results AS (
    SELECT
        s.*,
        c.cc_cutoff_met, c.ia_cutoff_met, c.ap_cutoff_met, c.sx_cutoff_met, c.ps_cutoff_met, c.gr_cutoff_met,
        c.ta_cutoff_met, c.na_cutoff_met, c.in_cutoff_met, c.as_cutoff_met, c.pq_cutoff_met,
        (s.cc_scored + s.ia_scored + s.ap_scored + s.sx_scored + s.ps_scored + s.gr_scored + s.ta_scored + s.na_scored + s.in_scored + s.as_scored + s.pq_scored) AS grand_total_scored,
        (s.cc_max + s.ia_max + s.ap_max + s.sx_max + s.ps_max + s.gr_max + s.ta_max + s.na_max + s.in_max + s.as_max + s.pq_max) AS grand_total_max,
        CASE
            WHEN (s.cc_s1 IS NOT NULL AND s.cc_s1 < 16) OR (s.cc_s2 IS NOT NULL AND s.cc_s2 < 16) OR (s.cc_s3 IS NOT NULL AND s.cc_s3 < 16) OR (s.cc_s4 IS NOT NULL AND s.cc_s4 < 16) OR
                 (s.cc_s5 IS NOT NULL AND s.cc_s5 < 16) OR (s.cc_s6 IS NOT NULL AND s.cc_s6 < 16) OR (s.cc_s7 IS NOT NULL AND s.cc_s7 < 16) OR (s.cc_s8 IS NOT NULL AND s.cc_s8 < 16) THEN 'Fail'
            WHEN (s.ia_s1 IS NOT NULL AND s.ia_s1 < 24) OR (s.ia_s2 IS NOT NULL AND s.ia_s2 < 24) OR (s.ia_s3 IS NOT NULL AND s.ia_s3 < 24) OR (s.ia_s4 IS NOT NULL AND s.ia_s4 < 24) OR
                 (s.ia_s5 IS NOT NULL AND s.ia_s5 < 24) OR (s.ia_s6 IS NOT NULL AND s.ia_s6 < 24) OR (s.ia_s7 IS NOT NULL AND s.ia_s7 < 24) OR (s.ia_s8 IS NOT NULL AND s.ia_s8 < 24) THEN 'Fail'
            WHEN (s.cc_s1 = 0 OR s.cc_s2 = 0 OR s.cc_s3 = 0 OR s.cc_s4 = 0 OR s.cc_s5 = 0 OR s.cc_s6 = 0 OR s.cc_s7 = 0 OR s.cc_s8 = 0 OR
                  s.ia_s1 = 0 OR s.ia_s2 = 0 OR s.ia_s3 = 0 OR s.ia_s4 = 0 OR s.ia_s5 = 0 OR s.ia_s6 = 0 OR s.ia_s7 = 0 OR s.ia_s8 = 0 OR
                  s.ap_s1 = 0 OR s.ap_s2 = 0 OR s.sx_s1 = 0 OR s.sx_s2 = 0 OR s.ta_s1 = 0 OR s.ta_s2 = 0 OR s.na_s1 = 0 OR s.na_s2 = 0 OR s.in_s1 = 0 OR s.in_s2 = 0
                 ) THEN 'Fail'
            ELSE 'Pass'
        END AS pass_fail
    FROM scaled s
    JOIN cutoffs c ON c.prn = s.prn
)
SELECT
    prn, student_full_name, batch_name, course_code, centre_code,
    cc_scored, cc_max, ROUND(cc_scored * 100.0 / NULLIF(cc_max, 0), 2) AS cc_pct, cc_cutoff_met, cc_subtests_entered,
    ia_scored, ia_max, ROUND(ia_scored * 100.0 / NULLIF(ia_max, 0), 2) AS ia_pct, ia_cutoff_met, ia_subtests_entered,
    ap_scored, ap_max, ROUND(ap_scored * 100.0 / NULLIF(ap_max, 0), 2) AS ap_pct, ap_cutoff_met, ap_subtests_entered,
    sx_scored, sx_max, ROUND(sx_scored * 100.0 / NULLIF(sx_max, 0), 2) AS sx_pct, sx_cutoff_met, sx_subtests_entered,
    ps_scored, ps_max, ROUND(ps_scored * 100.0 / NULLIF(ps_max, 0), 2) AS ps_pct, ps_cutoff_met, ps_subtests_entered,
    gr_scored, gr_max, ROUND(gr_scored * 100.0 / NULLIF(gr_max, 0), 2) AS gr_pct, gr_cutoff_met, gr_subtests_entered,
    ta_scored, ta_max, ROUND(ta_scored * 100.0 / NULLIF(ta_max, 0), 2) AS ta_pct, ta_cutoff_met, ta_subtests_entered,
    na_scored, na_max, ROUND(na_scored * 100.0 / NULLIF(na_max, 0), 2) AS na_pct, na_cutoff_met, na_subtests_entered,
    in_scored, in_max, ROUND(in_scored * 100.0 / NULLIF(in_max, 0), 2) AS in_pct, in_cutoff_met, in_subtests_entered,
    as_scored, as_max, ROUND(as_scored * 100.0 / NULLIF(as_max, 0), 2) AS as_pct, as_cutoff_met, as_subtests_entered,
    pq_scored, pq_max, ROUND(pq_scored * 100.0 / NULLIF(pq_max, 0), 2) AS pq_pct, pq_cutoff_met, pq_subtests_entered,
    grand_total_scored, grand_total_max, ROUND(grand_total_scored * 100.0 / NULLIF(grand_total_max, 0), 2) AS grand_total_pct,
    pass_fail,
    CASE
        WHEN ROUND(grand_total_scored * 100.0 / NULLIF(grand_total_max, 0), 2) >= 80 THEN 'Placement ready'
        WHEN pass_fail = 'Fail' THEN 'Not Placement ready'
        WHEN pass_fail = 'Pass' AND (cc_cutoff_met IS FALSE OR ia_cutoff_met IS FALSE OR (ap_cutoff_met IS FALSE) OR (sx_cutoff_met IS FALSE) OR (ps_cutoff_met IS FALSE) OR (gr_cutoff_met IS FALSE) OR (ta_cutoff_met IS FALSE) OR (na_cutoff_met IS FALSE) OR (in_cutoff_met IS FALSE) OR (as_cutoff_met IS FALSE) OR (pq_cutoff_met IS FALSE)) THEN 'Can Improve'
        WHEN pass_fail = 'Pass' THEN 'Placement ready'
        ELSE 'Not Placement ready'
    END::text AS placement_status
FROM results;

-- =============================================================================
-- VIEW 6: v_ccee_ia_modules
-- Purpose: Per-module (per-slot) breakdown for CCEE and IA
-- =============================================================================

CREATE OR REPLACE VIEW v_ccee_ia_modules AS
SELECT
    sm.prn,
    sm.student_full_name,
    sm.batch_id AS batch_name,
    sm.course_id AS course_code,
    sc_cc.test_01 AS cc_t01, sc_cc.test_02 AS cc_t02, sc_cc.test_03 AS cc_t03, sc_cc.test_04 AS cc_t04,
    sc_cc.test_05 AS cc_t05, sc_cc.test_06 AS cc_t06, sc_cc.test_07 AS cc_t07, sc_cc.test_08 AS cc_t08,
    sc_ia.test_01 AS ia_t01, sc_ia.test_02 AS ia_t02, sc_ia.test_03 AS ia_t03, sc_ia.test_04 AS ia_t04,
    sc_ia.test_05 AS ia_t05, sc_ia.test_06 AS ia_t06, sc_ia.test_07 AS ia_t07, sc_ia.test_08 AS ia_t08
FROM student_master sm
LEFT JOIN scores_cc sc_cc ON sc_cc.prn = sm.prn
LEFT JOIN scores_ia sc_ia ON sc_ia.prn = sm.prn
WHERE sm.is_active = TRUE;

