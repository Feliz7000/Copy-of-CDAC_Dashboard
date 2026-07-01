import axios from "axios";
import { getSession } from "next-auth/react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  async (config) => {
    // We try to get the session from NextAuth
    const session = await getSession();
    
    if (session?.accessToken) {
      config.headers.Authorization = `Bearer ${session.accessToken}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors (like 401s)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const session = await getSession();
    
    // If we get a 401 or if the session has a refresh error
    if (error.response?.status === 401 || session?.error === "RefreshAccessTokenError") {
      console.error("Authentication error: Session expired. Redirecting to login...");
      
      // Only redirect on the client side
      if (typeof window !== "undefined") {
        const { signOut } = await import("next-auth/react");
        signOut({ callbackUrl: "/login", redirect: true });
      }
    }
    
    return Promise.reject(error);
  }
);

// ============= PHASE 3 API FUNCTIONS =============

// LOOKUPS
export const getLookups = async () => {
  try {
    const [centres, courses, batches, categories] = await Promise.all([
      api.get('/assessments/centres/'),
      api.get('/assessments/courses/'),
      api.get('/assessments/batches/'),
      api.get('/assessments/main-categories/')
    ]);
    return {
      centres: centres.data.results || centres.data,
      courses: courses.data.results || courses.data,
      batches: batches.data.results || batches.data,
      categories: categories.data.results || categories.data
    };
  } catch (error) {
    console.error('Error fetching lookups:', error);
    throw error;
  }
};

// MAIN CATEGORIES
export const getMainCategories = async (filters?: Record<string, any>) => {
  const response = await api.get('/assessments/main-categories/', { params: filters });
  return response.data.results || response.data;
};

export const createMainCategory = async (data: any) => {
  const response = await api.post('/assessments/main-categories/', data);
  return response.data;
};

export const updateMainCategory = async (categoryCode: string, data: any) => {
  const response = await api.put(`/assessments/main-categories/${categoryCode}/`, data);
  return response.data;
};

export const deleteMainCategory = async (categoryCode: string) => {
  await api.delete(`/assessments/main-categories/${categoryCode}/`);
};

// BATCHES CRUD
export const getBatches = async (filters?: Record<string, any>) => {
  const response = await api.get('/assessments/batches/', { params: filters });
  return response.data.results || response.data;
};

export const createBatch = async (data: any) => {
  const response = await api.post('/assessments/batches/', data);
  return response.data;
};

export const updateBatch = async (batchName: string, data: any) => {
  const response = await api.put(`/assessments/batches/${encodeURIComponent(batchName)}/`, data);
  return response.data;
};

export const deleteBatch = async (batchName: string) => {
  await api.delete(`/assessments/batches/${encodeURIComponent(batchName)}/`);
};

// SUBTESTS
export const getSubTests = async (filters?: Record<string, any>) => {
  const response = await api.get('/assessments/subtests/', { params: filters });
  return response.data.results || response.data;
};

export const uploadSubTests = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/assessments/bulk-upload/subtests/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

// STUDENT MASTER
export const getStudents = async (filters?: Record<string, any>) => {
  const response = await api.get('/assessments/student-master/', { params: filters });
  return response.data.results || response.data;
};

export const createStudent = async (data: any) => {
  const response = await api.post('/assessments/student-master/', data);
  return response.data;
};

export const updateStudent = async (prn: string, data: any) => {
  const response = await api.put(`/assessments/student-master/${prn}/`, data);
  return response.data;
};

export const deleteStudent = async (prn: string) => {
  await api.delete(`/assessments/student-master/${prn}/`);
};

export const uploadStudents = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/assessments/bulk-upload/student-master/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const uploadScores = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/assessments/bulk-upload/marks/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

// EXAM SCHEDULE
export const getExamSchedules = async (filters?: Record<string, any>) => {
  const response = await api.get('/assessments/exam-schedules/', { params: filters });
  return response.data.results || response.data;
};

export const createExamSchedule = async (data: any) => {
  const response = await api.post('/assessments/exam-schedules/', data);
  return response.data;
};

export const deleteExamSchedule = async (id: number) => {
  await api.delete(`/assessments/exam-schedules/${id}/`);
};

// ============= HORIZONTAL SCORING ENDPOINTS =============

export const getTestMappings = async (batchName: string, categoryCode: string) => {
  const response = await api.get(`/assessments/test-mappings/${batchName}/${categoryCode}/`);
  return response.data;
};

export const getCategoriesForCourse = async (courseCode: string) => {
  const response = await api.get(`/assessments/categories/for-course/${courseCode}/`);
  return response.data;
};

export const getBatchScores = async (categoryCode: string, courseCode: string, batchName: string) => {
  const response = await api.get(`/assessments/scores/batch/${categoryCode}/${courseCode}/${batchName}/`);
  return response.data;
};

export const updateStudentScore = async (categoryCode: string, prn: string, scores: Record<string, any>) => {
  const response = await api.put(`/assessments/scores/${categoryCode}/${prn}/`, { scores });
  return response.data;
};

export const downloadScoreTemplate = async (categoryCode: string, courseCode: string, batchName: string) => {
  const response = await api.get(`/assessments/scores/template/${categoryCode}/${courseCode}/${batchName}/`, {
    responseType: 'blob'
  });
  return response.data;
};

// TEST MAPPINGS (CRUD)
export const getAllTestMappings = async (filters?: Record<string, any>) => {
  const response = await api.get('/assessments/test-mappings/', { params: filters });
  return response.data.results || response.data;
};

export const createTestMapping = async (data: any) => {
  const response = await api.post('/assessments/test-mappings/', data);
  return response.data;
};

export const updateTestMapping = async (id: number, data: any) => {
  const response = await api.put(`/assessments/test-mappings/${id}/`, data);
  return response.data;
};

export const deleteTestMapping = async (id: number) => {
  await api.delete(`/assessments/test-mappings/${id}/`);
};

// BULK ACTIONS
export const clearCategoryScores = async (categoryCode: string, courseCode: string, batchName: string) => {
  const response = await api.post('/assessments/bulk-actions/clear-scores/', {
    category_code: categoryCode,
    course_code: courseCode,
    batch_name: batchName
  });
  return response.data;
};

export const downloadStudentTemplate = async () => {
  const response = await api.get('/assessments/bulk-upload/student-template/', {
    responseType: 'blob'
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', 'student_master_template.xlsx');
  document.body.appendChild(link);
  link.click();
  link.remove();
};

export const uploadTestMappings = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/assessments/bulk-upload/test-mappings/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const downloadTestMappingTemplate = async () => {
  const response = await api.get('/assessments/bulk-upload/test-mapping-template/', {
    responseType: 'blob'
  });
  return response.data;
};

export const bulkDeleteTestMappings = async (ids: number[]) => {
  const response = await api.delete('/assessments/test-mappings/bulk-delete/', { data: { ids } });
  return response.data;
};

// ============= PLACEMENT REPORT API =============

export const getPlacementReport = async (
  batchName: string,
  courseCode?: string,
  centreCode?: string
) => {
  const response = await api.get('/assessments/reports/placement/', {
    params: {
      batch_name: batchName,
      ...(courseCode ? { course_code: courseCode } : {}),
      ...(centreCode ? { centre_code: centreCode } : {}),
    },
  });
  return response.data;
};

export const getCCEEIAModuleReport = async (
  batchName: string,
  courseCode?: string
) => {
  const response = await api.get('/assessments/reports/ccee-ia-modules/', {
    params: {
      batch_name: batchName,
      ...(courseCode ? { course_code: courseCode } : {}),
    },
  });
  return response.data;
};

export const downloadPlacementReportCSV = async (
  batchName: string,
  courseCode?: string,
  centreCode?: string
) => {
  const response = await api.get('/assessments/reports/placement/', {
    params: {
      batch_name: batchName,
      format: 'csv',
      ...(courseCode ? { course_code: courseCode } : {}),
      ...(centreCode ? { centre_code: centreCode } : {}),
    },
    responseType: 'blob',
  });

  return response.data;
};

export const downloadCCEIAModuleCSV = async (
  batchName: string,
  courseCode?: string
) => {
  const response = await api.get('/assessments/reports/ccee-ia-modules/', {
    params: {
      batch_name: batchName,
      format: 'csv',
      ...(courseCode ? { course_code: courseCode } : {}),
    },
    responseType: 'blob',
  });

  return response.data;
};

// ============= ANALYTICS / DASHBOARD API =============

export const getSystemOverview = async () => {
  const response = await api.get('/analytics/system_overview/');
  return response.data;
};

export const getActivityTrend = async () => {
  const response = await api.get('/analytics/activity-trend/');
  return response.data as { name: string; score: number }[];
};

export const getStudentSummary = async (prn: string) => {
  const response = await api.get('/analytics/student_summary/', { params: { prn } });
  return response.data;
};

export const getRoleDashboard = async () => {
  const response = await api.get('/analytics/role-dashboard/');
  return response.data;
};

export const getGrandTotals = async (params?: Record<string, string>) => {
  const response = await api.get('/analytics/grand-totals/', { params });
  return response.data.results ?? response.data;
};

export const getStudentScoresByDate = async (prn: string) => {
  const response = await api.get('/analytics/scores-by-date/', { params: { prn } });
  return response.data.results ?? response.data;
};

export const getUserProfile = async () => {
  const response = await api.get('/users/profile/');
  return response.data;
};

export const changePassword = async (data: {
  old_password: string;
  new_password: string;
  new_password2: string;
}) => {
  const response = await api.post('/users/change_password/', data);
  return response.data;
};

export type PowerBIEmbedConfig = {
  success: boolean;
  configured?: boolean;
  message?: string;
  embed_token?: string;
  embed_url?: string;
  report_id?: string;
  expiration?: string;
};

export const getPowerBIEmbedConfig = async (): Promise<PowerBIEmbedConfig> => {
  const response = await api.get('/powerbi/embed-config/');
  return response.data;
};
