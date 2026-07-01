"""
Assessment models for Student Analytics Platform (REFORMED)
Includes: Centre, Course, Batch (lookup tables), MainCategory, SubTest, StudentMaster, StudentTestScore
All use managed=False (database-managed, no migrations)
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


# ==================== LOOKUP TABLES ====================

class Centre(models.Model):
    """Centre/Location master table"""
    
    centre_code = models.CharField(
        max_length=3,
        primary_key=True,
        help_text="Centre code (e.g., '001', '002')"
    )
    centre_name = models.CharField(
        max_length=100,
        help_text="Centre name (e.g., 'Mumbai', 'Delhi')"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this centre active?"
    )
    
    class Meta:
        managed = True
        db_table = 'centres'
        verbose_name = 'Centre'
        verbose_name_plural = 'Centres'
    
    def __str__(self):
        return f"{self.centre_code} - {self.centre_name}"


class Course(models.Model):
    """Course/Program master table"""
    
    course_code = models.CharField(
        max_length=2,
        primary_key=True,
        help_text="Course code (e.g., '28' for BCA, '14' for MCA)"
    )
    course_name = models.CharField(
        max_length=100,
        help_text="Course name (e.g., 'Bachelor of Computer Applications')"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this course active?"
    )
    
    class Meta:
        managed = True
        db_table = 'courses'
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
    
    def __str__(self):
        return f"{self.course_code} - {self.course_name}"


class Batch(models.Model):
    """Batch master table (e.g., Feb/2024, Aug/2024)"""
    
    batch_name = models.CharField(
        max_length=10,
        primary_key=True,
        help_text="Batch name (e.g., 'Feb/24', 'Aug/24')"
    )
    batch_month = models.CharField(
        max_length=2,
        choices=[('02', 'February'), ('08', 'August')],
        help_text="Batch month code (02 or 08)"
    )
    batch_year = models.SmallIntegerField(
        help_text="Year (e.g., 2024)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this batch active?"
    )
    
    class Meta:
        managed = True
        db_table = 'batches'
        verbose_name = 'Batch'
        verbose_name_plural = 'Batches'
        unique_together = ('batch_month', 'batch_year')
    
    def __str__(self):
        return self.batch_name


class CentreCourseBatch(models.Model):
    """Legacy table - kept for backward compatibility"""
    
    centre_code = models.CharField(
        max_length=3,
        primary_key=True,
        help_text="Centre code (e.g., '001')"
    )
    centre_name = models.CharField(
        max_length=100,
        help_text="Centre name"
    )
    course_code = models.CharField(
        max_length=2,
        help_text="Course code (e.g., '28' for BCA)"
    )
    course_name = models.CharField(
        max_length=100,
        help_text="Course name"
    )
    max_students = models.SmallIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Maximum students in batch"
    )
    enroll_year = models.SmallIntegerField(
        help_text="Year of enrollment (e.g., 2023)"
    )
    batch_month = models.CharField(
        max_length=2,
        choices=[('02', 'February'), ('08', 'August')],
        help_text="Batch month (Feb or Aug)"
    )
    batch_label = models.CharField(
        max_length=10,
        editable=False,
        help_text="Generated field: e.g., 'F23' for Feb 2023"
    )
    
    class Meta:
        managed = False
        db_table = 'centres_courses_batches'
        unique_together = ('centre_code', 'course_code', 'enroll_year', 'batch_month')
        verbose_name = 'Centre Course Batch (Legacy)'
        verbose_name_plural = 'Centre Course Batches (Legacy)'
        indexes = [
            models.Index(fields=['centre_code', 'course_code']),
            models.Index(fields=['enroll_year', 'batch_month']),
        ]
    
    def __str__(self):
        return f"{self.centre_code}-{self.course_code}-{self.batch_label}"


# ==================== MAIN MODELS ====================

class MainCategory(models.Model):
    """Assessment categories (e.g., MSE, ESE, Assignments)"""
    
    category_code = models.CharField(
        max_length=5,
        primary_key=True,
        help_text="Category code (e.g., 'MSE', 'ESE', 'APT')"
    )
    category_name = models.CharField(
        max_length=100,
        help_text="Category name (e.g., 'Mid Semester Exam')"
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Category description"
    )
    max_marks_per_subtest = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Max marks per subtest (reference only, NOT connected to other tables)"
    )
    no_of_subtests = models.SmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Maximum number of subtests allowed in this category"
    )
    scaled_marks = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Scaled marks after all subtests are aggregated"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this category active? (soft delete via this flag)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="When this category was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,
        help_text="When this category was last updated"
    )
    
    class Meta:
        managed = True
        db_table = 'main_categories'
        verbose_name = 'Main Category'
        verbose_name_plural = 'Main Categories'
        indexes = [
            models.Index(fields=['category_code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.category_code} - {self.category_name}"


class CategoryCourseMapping(models.Model):
    """Mapping between Categories and Courses (which categories apply to which course)"""
    category = models.ForeignKey(
        MainCategory,
        on_delete=models.CASCADE,
        to_field='category_code',
        db_column='category_code'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        to_field='course_code',
        db_column='course_code'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'category_course_mapping'
        unique_together = ('category', 'course')

    def __str__(self):
        return f"{self.category.category_code} -> {self.course.course_code}"


class SubTest(models.Model):
    """Individual tests/assessments within categories"""
    
    tprn = models.CharField(
        max_length=20,
        primary_key=True,
        help_text="Test Permanent Registration Number (CATEGORY_CODE-SEQ, e.g., 'MSE-001')"
    )
    category_code = models.ForeignKey(
        MainCategory,
        on_delete=models.PROTECT,
        to_field='category_code',
        db_column='category_code',
        help_text="Assessment category"
    )
    subtest_name = models.CharField(
        max_length=100,
        help_text="Name of the test"
    )
    centre_code = models.ForeignKey(
        Centre,
        on_delete=models.PROTECT,
        to_field='centre_code',
        db_column='centre_code',
        help_text="Centre code"
    )
    course_code = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        to_field='course_code',
        db_column='course_code',
        help_text="Course code"
    )
    batch_name = models.ForeignKey(
        Batch,
        on_delete=models.PROTECT,
        to_field='batch_name',
        db_column='batch_name',
        help_text="Batch (e.g., 'Feb/24')"
    )
    max_marks = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Maximum marks for this test"
    )
    test_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of the test (can be filled later)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this subtest active? (soft delete via this flag)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="When this subtest was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,
        help_text="When this subtest was last updated"
    )
    
    class Meta:
        managed = True
        db_table = 'sub_tests'
        verbose_name = 'SubTest'
        verbose_name_plural = 'SubTests'
        unique_together = ('tprn', 'centre_code', 'course_code', 'batch_name')
        indexes = [
            models.Index(fields=['category_code', 'is_active']),
            models.Index(fields=['centre_code', 'course_code', 'batch_name']),
            models.Index(fields=['tprn', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.tprn} - {self.subtest_name}"


class StudentMaster(models.Model):
    """Student master data.
    Access FK values via:
      student.centre_id       → centre code string (FK column value)
      student.centre.centre_name  → centre name (FK traversal)
      student.course_id       → course code string
      student.course.course_name  → course name
      student.batch_id        → batch name string
    """

    prn = models.CharField(
        max_length=20,
        primary_key=True,
        help_text="Permanent Registration Number"
    )
    student_full_name = models.CharField(
        max_length=150,
        help_text="Full name of student"
    )
    centre = models.ForeignKey(
        Centre,
        on_delete=models.PROTECT,
        to_field='centre_code',
        help_text="Centre (stored for data integrity; not used in filtering)"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        to_field='course_code',
        help_text="Course"
    )
    batch = models.ForeignKey(
        Batch,
        on_delete=models.PROTECT,
        to_field='batch_name',
        help_text="Batch (e.g., 'Feb/24')"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is student active? (soft delete via this flag)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="When this student was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,
        help_text="When this student was last updated"
    )

    class Meta:
        managed = True
        db_table = 'student_master'
        verbose_name = 'Student Master'
        verbose_name_plural = 'Student Masters'
        indexes = [
            models.Index(fields=['prn', 'is_active']),
            # FK columns: centre_id maps to centre_code in DB,
            #             course_id maps to course_code,
            #             batch_id  maps to batch_name
            models.Index(fields=['centre_id']),
            models.Index(fields=['course_id']),
            models.Index(fields=['batch_id']),
        ]

    def __str__(self):
        return f"{self.prn} - {self.student_full_name}"



class Student(models.Model):
    """Legacy Student table - kept for backward compatibility"""
    
    prn = models.CharField(
        max_length=12,
        primary_key=True,
        help_text="Permanent Registration Number (12 digits)"
    )
    full_name = models.CharField(
        max_length=150,
        help_text="Full name of student"
    )
    centre_code = models.CharField(
        max_length=3,
        help_text="Centre code (links to CentreCourseBatch)"
    )
    course_code = models.CharField(
        max_length=2,
        help_text="Course code (links to CentreCourseBatch)"
    )
    enroll_year = models.SmallIntegerField(
        editable=False,
        help_text="Generated: Year of enrollment"
    )
    batch_month = models.CharField(
        max_length=2,
        editable=False,
        help_text="Generated: Batch month (02 or 08)"
    )
    serial_no = models.SmallIntegerField(
        editable=False,
        help_text="Generated: Serial number in batch"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is student active?"
    )
    
    class Meta:
        managed = False
        db_table = 'students'
        verbose_name = 'Student (Legacy)'
        verbose_name_plural = 'Students (Legacy)'
        indexes = [
            models.Index(fields=['centre_code', 'course_code']),
            models.Index(fields=['enroll_year']),
            models.Index(fields=['batch_month']),
        ]
    
    def __str__(self):
        return f"{self.prn} - {self.full_name}"


class StudentTestScore(models.Model):
    """Actual exam scores for students"""
    
    score_id = models.BigAutoField(primary_key=True)
    tprn = models.ForeignKey(
        SubTest,
        on_delete=models.PROTECT,
        to_field='tprn',
        db_column='tprn',
        help_text="Reference to test"
    )
    prn = models.ForeignKey(
        StudentMaster,
        on_delete=models.PROTECT,
        to_field='prn',
        db_column='prn',
        help_text="Reference to student"
    )
    subtest_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Subtest name (denormalized for reporting)"
    )
    category_code = models.CharField(
        max_length=5,
        null=True,
        blank=True,
        help_text="Category code (denormalized for reporting)"
    )
    batch_name = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Batch name (denormalized for reporting)"
    )
    score = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Actual score obtained (null if absent)"
    )
    is_absent = models.BooleanField(
        default=False,
        help_text="Was student absent?"
    )
    exam_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of exam (can be filled later)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this score record active? (soft delete via this flag)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="When this score was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,
        help_text="When this score was last updated"
    )
    
    class Meta:
        managed = True
        db_table = 'student_test_scores'
        verbose_name = 'Student Test Score'
        verbose_name_plural = 'Student Test Scores'
        unique_together = ('tprn', 'prn')
        indexes = [
            models.Index(fields=['prn', 'is_active']),
            models.Index(fields=['tprn', 'is_active']),
            models.Index(fields=['exam_date']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.prn}-{self.tprn}: {self.score if self.score else 'Absent'}"
    
    def clean(self):
        """Validate score is within valid range"""
        if not self.is_absent and self.score is not None:
            if self.score < 0:
                raise ValueError("Score cannot be negative")
            if self.score > self.tprn.max_marks:
                raise ValueError(f"Score cannot exceed {self.tprn.max_marks}")
        if self.is_absent and self.score is not None:
            raise ValueError("Cannot have both absence flag and score")


class ExamSchedule(models.Model):
    """Exam scheduling information"""
    
    schedule_id = models.AutoField(primary_key=True)
    tprn = models.ForeignKey(
        SubTest,
        on_delete=models.PROTECT,
        to_field='tprn',
        db_column='tprn',
        help_text="Reference to test"
    )
    scheduled_date = models.DateField(
        help_text="Scheduled date of exam"
    )
    scheduled_month = models.DateField(
        editable=False,
        help_text="Generated: First day of scheduled month"
    )
    venue = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        help_text="Exam venue"
    )
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Additional notes"
    )
    is_confirmed = models.BooleanField(
        default=False,
        help_text="Is schedule confirmed?"
    )
    
    class Meta:
        managed = True
        db_table = 'exam_schedule'
        verbose_name = 'Exam Schedule'
        verbose_name_plural = 'Exam Schedules'
        unique_together = ('tprn', 'scheduled_date')
        indexes = [
            models.Index(fields=['tprn']),
            models.Index(fields=['scheduled_date']),
        ]
    
    def __str__(self):
        return f"{self.tprn} - {self.scheduled_date}"


class GradeScale(models.Model):
    """Grade scale lookup (7 grades: A+ to F)"""
    
    grade = models.CharField(
        max_length=2,
        primary_key=True,
        help_text="Grade (A+, A, B+, B, C+, C, F)"
    )
    min_marks = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        help_text="Minimum marks for this grade"
    )
    max_marks = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        help_text="Maximum marks for this grade"
    )
    description = models.CharField(
        max_length=50,
        help_text="Grade description"
    )
    
    class Meta:
        managed = True
        db_table = 'grade_scale'
        verbose_name = 'Grade Scale'
        verbose_name_plural = 'Grade Scales'
    
    def __str__(self):
        return f"{self.grade}: {self.description} ({self.min_marks}-{self.max_marks})"


class TestMapping(models.Model):
    """Mapping for horizontal subtests (Excel column slot to logical test).
    No centre_code — single-centre system, centre plays no role here."""

    batch_name = models.ForeignKey(
        Batch,
        on_delete=models.PROTECT,
        to_field='batch_name',
        db_column='batch_name',
        help_text="Batch (e.g., 'Feb/24')"
    )
    category_code = models.ForeignKey(
        MainCategory,
        on_delete=models.PROTECT,
        to_field='category_code',
        db_column='category_code',
        help_text="Assessment category"
    )
    logical_name = models.CharField(
        max_length=100,
        help_text="Logical name for the test (e.g., 'Aptitude 1')"
    )
    column_slot = models.CharField(
        max_length=50,
        help_text="Excel column slot reference (e.g., 'test_01')"
    )
    max_marks = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Maximum marks for this logical test"
    )
    sequence = models.SmallIntegerField(
        default=1,
        help_text="Sequence order in UI/Reports"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this mapping active?"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        null=True
    )

    class Meta:
        managed = True
        db_table = 'test_mapping'
        verbose_name = 'Test Mapping'
        verbose_name_plural = 'Test Mappings'
        constraints = [
            models.UniqueConstraint(
                fields=['batch_name', 'category_code', 'column_slot'],
                name='uq_tm_batch_category_slot'
            ),
            models.UniqueConstraint(
                fields=['batch_name', 'category_code', 'logical_name'],
                name='uq_tm_batch_category_name'
            ),
        ]
        indexes = [
            models.Index(fields=['batch_name', 'category_code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.batch_name} | {self.category_code} → {self.logical_name} ({self.column_slot})"


# ==================== PARTITIONED SCORE MODELS ====================

def _score_field():
    """Shorthand for a nullable decimal score column"""
    return models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)


class BaseScoreModel(models.Model):
    """Abstract base — shared columns only (prn + timestamp).
    Each subclass declares its own score columns matching its actual DB table."""
    prn = models.ForeignKey(
        StudentMaster,
        on_delete=models.PROTECT,
        to_field='prn',
        db_column='prn',
        help_text="Student PRN"
    )
    # updated_at Python attr maps to last_updated DB column
    updated_at = models.DateTimeField(auto_now=True, db_column='last_updated')

    class Meta:
        abstract = True


class ScoreAP(BaseScoreModel):
    """scores_ap — 20 subtests"""
    test_01 = _score_field(); test_02 = _score_field(); test_03 = _score_field()
    test_04 = _score_field(); test_05 = _score_field(); test_06 = _score_field()
    test_07 = _score_field(); test_08 = _score_field(); test_09 = _score_field()
    test_10 = _score_field(); test_11 = _score_field(); test_12 = _score_field()
    test_13 = _score_field(); test_14 = _score_field(); test_15 = _score_field()
    test_16 = _score_field(); test_17 = _score_field(); test_18 = _score_field()
    test_19 = _score_field(); test_20 = _score_field()
    class Meta:
        managed = False
        db_table = 'scores_ap'
        verbose_name = 'Scores - Aptitude'

class ScoreAS(BaseScoreModel):
    """scores_as — 30 subtests"""
    test_01 = _score_field(); test_02 = _score_field(); test_03 = _score_field()
    test_04 = _score_field(); test_05 = _score_field(); test_06 = _score_field()
    test_07 = _score_field(); test_08 = _score_field(); test_09 = _score_field()
    test_10 = _score_field(); test_11 = _score_field(); test_12 = _score_field()
    test_13 = _score_field(); test_14 = _score_field(); test_15 = _score_field()
    test_16 = _score_field(); test_17 = _score_field(); test_18 = _score_field()
    test_19 = _score_field(); test_20 = _score_field(); test_21 = _score_field()
    test_22 = _score_field(); test_23 = _score_field(); test_24 = _score_field()
    test_25 = _score_field(); test_26 = _score_field(); test_27 = _score_field()
    test_28 = _score_field(); test_29 = _score_field(); test_30 = _score_field()
    class Meta:
        managed = False
        db_table = 'scores_as'
        verbose_name = 'Scores - Advanced Systems'

class ScoreCC(BaseScoreModel):
    """scores_cc — 8 subtests"""
    test_01 = _score_field(); test_02 = _score_field(); test_03 = _score_field()
    test_04 = _score_field(); test_05 = _score_field(); test_06 = _score_field()
    test_07 = _score_field(); test_08 = _score_field()
    class Meta:
        managed = False
        db_table = 'scores_cc'
        verbose_name = 'Scores - C/C++ Programming'

class ScoreGR(BaseScoreModel):
    """scores_gr — 10 subtests"""
    test_01 = _score_field(); test_02 = _score_field(); test_03 = _score_field()
    test_04 = _score_field(); test_05 = _score_field(); test_06 = _score_field()
    test_07 = _score_field(); test_08 = _score_field(); test_09 = _score_field()
    test_10 = _score_field()
    class Meta:
        managed = False
        db_table = 'scores_gr'
        verbose_name = 'Scores - Graphics'


class ScoreGAC(BaseScoreModel):
    """scores_gac — 5 subtests"""
    test_01 = _score_field(); test_02 = _score_field(); test_03 = _score_field()
    test_04 = _score_field(); test_05 = _score_field()
    class Meta:
        managed = False
        db_table = 'scores_gac'
        verbose_name = 'Scores - GAC Grade'

class ScoreIN(BaseScoreModel):
    """scores_in — 5 subtests"""
    test_01 = _score_field(); test_02 = _score_field(); test_03 = _score_field()
    test_04 = _score_field(); test_05 = _score_field()
    class Meta:
        managed = False
        db_table = 'scores_in'
        verbose_name = 'Scores - Internet'

class ScoreIA(BaseScoreModel):
    """scores_ia — 8 subtests"""
    test_01 = _score_field(); test_02 = _score_field(); test_03 = _score_field()
    test_04 = _score_field(); test_05 = _score_field(); test_06 = _score_field()
    test_07 = _score_field(); test_08 = _score_field()
    class Meta:
        managed = False
        db_table = 'scores_ia'
        verbose_name = 'Scores - IA / Module'

class ScoreNA(BaseScoreModel):
    """scores_na — 5 subtests"""
    test_01 = _score_field(); test_02 = _score_field(); test_03 = _score_field()
    test_04 = _score_field(); test_05 = _score_field()
    class Meta:
        managed = False
        db_table = 'scores_na'
        verbose_name = 'Scores - Networking'

class ScorePQ(BaseScoreModel):
    """scores_pq — 30 subtests"""
    test_01 = _score_field(); test_02 = _score_field(); test_03 = _score_field()
    test_04 = _score_field(); test_05 = _score_field(); test_06 = _score_field()
    test_07 = _score_field(); test_08 = _score_field(); test_09 = _score_field()
    test_10 = _score_field(); test_11 = _score_field(); test_12 = _score_field()
    test_13 = _score_field(); test_14 = _score_field(); test_15 = _score_field()
    test_16 = _score_field(); test_17 = _score_field(); test_18 = _score_field()
    test_19 = _score_field(); test_20 = _score_field(); test_21 = _score_field()
    test_22 = _score_field(); test_23 = _score_field(); test_24 = _score_field()
    test_25 = _score_field(); test_26 = _score_field(); test_27 = _score_field()
    test_28 = _score_field(); test_29 = _score_field(); test_30 = _score_field()
    class Meta:
        managed = False
        db_table = 'scores_pq'
        verbose_name = 'Scores - Programming (Advanced)'

class ScorePS(BaseScoreModel):
    """scores_ps — 10 subtests"""
    test_01 = _score_field(); test_02 = _score_field(); test_03 = _score_field()
    test_04 = _score_field(); test_05 = _score_field(); test_06 = _score_field()
    test_07 = _score_field(); test_08 = _score_field(); test_09 = _score_field()
    test_10 = _score_field()
    class Meta:
        managed = False
        db_table = 'scores_ps'
        verbose_name = 'Scores - Programming (Systems)'


class ScorePRJ(BaseScoreModel):
    """scores_prj — 1 subtest"""
    test_01 = _score_field()
    class Meta:
        managed = False
        db_table = 'scores_prj'
        verbose_name = 'Scores - Project Grade'

class ScoreSX(BaseScoreModel):
    """scores_sx — 10 subtests"""
    test_01 = _score_field(); test_02 = _score_field(); test_03 = _score_field()
    test_04 = _score_field(); test_05 = _score_field(); test_06 = _score_field()
    test_07 = _score_field(); test_08 = _score_field(); test_09 = _score_field()
    test_10 = _score_field()
    class Meta:
        managed = False
        db_table = 'scores_sx'
        verbose_name = 'Scores - Software Extras'

class ScoreTA(BaseScoreModel):
    """scores_ta — 5 subtests"""
    test_01 = _score_field(); test_02 = _score_field(); test_03 = _score_field()
    test_04 = _score_field(); test_05 = _score_field()
    class Meta:
        managed = False
        db_table = 'scores_ta'
        verbose_name = 'Scores - Technical Aptitude'


# ==================== SYSTEM CONFIGURATION ====================

class SystemConfig(models.Model):
    """
    Key-value store for system-wide configuration.
    The canonical record is key='active_batch', value='Feb/24' (or similar).
    """
    key   = models.CharField(max_length=50, primary_key=True)
    value = models.CharField(max_length=100)

    class Meta:
        managed  = True
        db_table = 'system_config'
        verbose_name = 'System Config'
        verbose_name_plural = 'System Config'

    def __str__(self):
        return f"{self.key} = {self.value}"

    @classmethod
    def get_active_batch(cls) -> str:
        """
        Returns the currently active batch_name string.
        Raises SystemConfig.DoesNotExist if the 'active_batch' key is not set.
        Raises ValueError with a clear message if the batch doesn't exist in DB.
        """
        config = cls.objects.get(key='active_batch')
        # Late import to avoid circular references
        if not Batch.objects.filter(batch_name=config.value).exists():
            raise ValueError(
                f"Active batch '{config.value}' in SystemConfig does not "
                f"exist in the batches table. Run the seed command to fix."
            )
        return config.value

    @classmethod
    def set_active_batch(cls, batch_name: str) -> None:
        """
        Sets the active batch. Validates the batch exists first.
        Usage: SystemConfig.set_active_batch('Feb/24')
        """
        if not Batch.objects.filter(batch_name=batch_name).exists():
            raise ValueError(f"Batch '{batch_name}' does not exist.")
        cls.objects.update_or_create(
            key='active_batch',
            defaults={'value': batch_name}
        )


# ==================== MAPPING REGISTRY ====================

CATEGORY_SCORE_MODEL_MAP = {
    'AP': ScoreAP,
    'AS': ScoreAS,
    'CC': ScoreCC,
    'GAC': ScoreGAC,
    'GR': ScoreGR,
    'IN': ScoreIN,
    'IA': ScoreIA,
    'NA': ScoreNA,
    'PQ': ScorePQ,
    'PRJ': ScorePRJ,
    'PS': ScorePS,
    'SX': ScoreSX,
    'TA': ScoreTA,
}
