"""
Django admin configuration for assessments app (reformed schema)
Registers both new managed models and legacy read-only models.
"""
from django.contrib import admin
from apps.assessments.models import (
    # New managed models
    Centre, Course, Batch,
    MainCategory, CategoryCourseMapping,
    SubTest, StudentMaster, StudentTestScore,
    ExamSchedule, GradeScale, TestMapping, SystemConfig,
    # Legacy models (managed=False — read-only)
    CentreCourseBatch, Student,
)


# ==================== LOOKUP TABLE ADMINS ====================

@admin.register(Centre)
class CentreAdmin(admin.ModelAdmin):
    """Admin for Centre"""
    list_display = ('centre_code', 'centre_name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('centre_code', 'centre_name')
    ordering = ('centre_code',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Admin for Course"""
    list_display = ('course_code', 'course_name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('course_code', 'course_name')
    ordering = ('course_code',)


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    """Admin for Batch"""
    list_display = ('batch_name', 'batch_month', 'batch_year', 'is_active')
    list_filter = ('batch_month', 'batch_year', 'is_active')
    search_fields = ('batch_name',)
    ordering = ('batch_year', 'batch_month')


# ==================== CATEGORY ADMINS ====================

@admin.register(MainCategory)
class MainCategoryAdmin(admin.ModelAdmin):
    """Admin for MainCategory"""
    list_display = ('category_code', 'category_name', 'no_of_subtests', 'scaled_marks', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('category_code', 'category_name')
    fieldsets = (
        ('Category', {
            'fields': ('category_code', 'category_name', 'description')
        }),
        ('Subtests Configuration', {
            'fields': ('no_of_subtests', 'max_marks_per_subtest', 'scaled_marks')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(CategoryCourseMapping)
class CategoryCourseMappingAdmin(admin.ModelAdmin):
    """Admin for CategoryCourseMapping"""
    list_display = ('category', 'course', 'is_active')
    list_filter = ('is_active', 'course')
    search_fields = ('category__category_code', 'course__course_code')
    ordering = ('category', 'course')


# ==================== SUBTEST ADMIN ====================

@admin.register(SubTest)
class SubTestAdmin(admin.ModelAdmin):
    """Admin for SubTest"""
    list_display = ('tprn', 'subtest_name', 'category_code', 'centre_code', 'batch_name', 'max_marks', 'is_active')
    list_filter = ('category_code', 'centre_code', 'course_code', 'is_active')
    search_fields = ('tprn', 'subtest_name')
    fieldsets = (
        ('Test Information', {
            'fields': ('tprn', 'subtest_name', 'max_marks', 'test_date')
        }),
        ('Category', {
            'fields': ('category_code',)
        }),
        ('Centre, Course & Batch', {
            'fields': ('centre_code', 'course_code', 'batch_name')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    ordering = ('tprn',)


# ==================== STUDENT ADMINS ====================

@admin.register(StudentMaster)
class StudentMasterAdmin(admin.ModelAdmin):
    """Admin for StudentMaster (new managed model)"""
    list_display = ('prn', 'student_full_name', 'centre_id', 'course_id', 'batch_id', 'is_active')
    list_filter = ('centre_id', 'course_id', 'batch_id', 'is_active')
    search_fields = ('prn', 'student_full_name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Student Information', {
            'fields': ('prn', 'student_full_name')
        }),
        ('Assignments', {
            'fields': ('centre', 'course', 'batch')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )
    ordering = ('prn',)



# ==================== SCORE / EXAM ADMINS ====================

@admin.register(StudentTestScore)
class StudentTestScoreAdmin(admin.ModelAdmin):
    """Admin for StudentTestScore"""
    list_display = ('score_id', 'prn', 'tprn', 'score', 'is_absent', 'exam_date', 'is_active')
    list_filter = ('is_absent', 'exam_date', 'is_active', 'category_code')
    search_fields = ('prn__prn', 'prn__student_full_name', 'tprn__tprn')
    readonly_fields = ('score_id', 'created_at', 'updated_at')
    fieldsets = (
        ('Score', {
            'fields': ('score_id', 'prn', 'tprn', 'score')
        }),
        ('Exam Details', {
            'fields': ('exam_date', 'is_absent', 'subtest_name', 'category_code', 'batch_name')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )
    date_hierarchy = 'exam_date'
    ordering = ('-exam_date',)


@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    """Admin for ExamSchedule"""
    list_display = ('schedule_id', 'tprn', 'scheduled_date', 'venue', 'is_confirmed')
    list_filter = ('is_confirmed', 'scheduled_date', 'scheduled_month')
    search_fields = ('tprn__tprn', 'tprn__subtest_name', 'venue')
    readonly_fields = ('schedule_id', 'scheduled_month')
    fieldsets = (
        ('Schedule', {
            'fields': ('schedule_id', 'tprn', 'scheduled_date', 'scheduled_month')
        }),
        ('Details', {
            'fields': ('venue', 'notes', 'is_confirmed')
        }),
    )
    date_hierarchy = 'scheduled_date'
    ordering = ('scheduled_date',)


@admin.register(GradeScale)
class GradeScaleAdmin(admin.ModelAdmin):
    """Admin for GradeScale"""
    list_display = ('grade', 'description', 'min_marks', 'max_marks')
    readonly_fields = ('grade',)
    ordering = ('grade',)


@admin.register(TestMapping)
class TestMappingAdmin(admin.ModelAdmin):
    """Admin for TestMapping"""
    list_display = ['batch_name', 'category_code', 'logical_name', 'column_slot', 'max_marks', 'is_active']
    list_filter = ['batch_name', 'category_code', 'is_active']
    search_fields = ['logical_name']
    ordering = ('batch_name', 'category_code', 'sequence')

@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    """Admin for SystemConfig — manage the active batch and other system flags"""
    list_display = ['key', 'value']


# ==================== LEGACY MODEL ADMINS (Read-Only) ====================

@admin.register(CentreCourseBatch)
class CentreCourseBatchAdmin(admin.ModelAdmin):
    """Admin for CentreCourseBatch (legacy, managed=False — READ ONLY)"""
    list_display = ('centre_code', 'centre_name', 'course_code', 'course_name', 'batch_label', 'max_students')
    list_filter = ('centre_code', 'course_code', 'enroll_year', 'batch_month')
    search_fields = ('centre_code', 'centre_name', 'course_code', 'course_name')
    readonly_fields = ('centre_code', 'centre_name', 'course_code', 'course_name',
                       'max_students', 'enroll_year', 'batch_month', 'batch_label')
    ordering = ('centre_code', 'course_code', 'enroll_year')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Admin for Student (legacy, managed=False — READ ONLY)"""
    list_display = ('prn', 'full_name', 'centre_code', 'course_code', 'batch_month', 'is_active')
    list_filter = ('centre_code', 'course_code', 'enroll_year', 'batch_month', 'is_active')
    search_fields = ('prn', 'full_name', 'centre_code', 'course_code')
    readonly_fields = ('prn', 'full_name', 'centre_code', 'course_code',
                       'enroll_year', 'batch_month', 'serial_no', 'is_active')
    ordering = ('prn',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
