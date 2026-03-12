import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
    timeout: 100000,
    withCredentials: true,
});

export const api = {
    // login
    login: async (credentials) => {
        return apiClient.post('/api/v1/login', credentials);
    },

    // register
    register: async (userData) => {
        return apiClient.post('/api/v1/register', userData);
    },

    // verify email
    verifyEmail: async (token) => {
        return apiClient.post('/api/v1/verify-email', {token});
    },

    // resend email verification
    resendEmailVerification: async (credentials) => {
        return apiClient.post('/api/v1/resend-email-verification', credentials);
    },

    // logout
    logout: async () => {
        return apiClient.post('/api/v1/logout', {});
    },

    // check current user
    getCurrentUser: async () => {
        return apiClient.get('/api/v1/users/me');
    },

    // get news feed
    // getFeed: async (page = 1, limit = 10) => {
    //     return apiClient.get(`/api/v1/news/feed?page=${page}&limit=${limit}`);
    // },

    //get articles feed with optional category filter
    getFeed: async (page = 1, limit = 10, category /* 可选 */) => {
        const params = new URLSearchParams({page, limit});
        if (category) params.set("field", category);
        return apiClient.get(`/api/v1/articles/?${params.toString()}`);
    },

    // get article detail  
    getArticle: async (articleSlug) => {
        return apiClient.get(`/api/v1/articles/${articleSlug}`);
    },

    // search articles
    searchArticles: async (query, page = 1, limit = 10) => {
        return apiClient.get(`/api/v1/articles/?q=${encodeURIComponent(query)}&page=${page}&limit=${limit}`);
    },

    // bookmark management
    bookmarkArticle: async (articleId) => {
        return apiClient.post('/api/v1/bookmarks/', {article_id: articleId});
    },

    unbookmarkArticle: async (articleId) => {
        return apiClient.delete(`/api/v1/bookmarks/by-article/${articleId}`);
    },

    getBookmarks: async () => {
        return apiClient.get('/api/v1/bookmarks/');
    },

    // get fields and subfields
    getFields: () => apiClient.get('/api/v1/fields/'),

    // retrieve user interests
    getInterests: () => apiClient.get('/api/v1/interests/'),

    // add interest (field or subfield)
    addInterest: (fieldId) =>
        apiClient.post('/api/v1/interests/', {field_id: fieldId}),

    // remove interest (field or subfield)
    removeInterest: (fieldId) =>
        apiClient.delete('/api/v1/interests/', {data: {field_id: fieldId}}),

    // submit feedback
    submitFeedback: async (feedbackData) => {
        return apiClient.post('/api/v1/feedbacks/', feedbackData);
    },

};

// Export helper function for feedback submission
export const submitFeedback = async (feedbackData) => {
    try {
        const response = await api.submitFeedback(feedbackData);
        return response.data;
    } catch (error) {
        if (error.response?.data?.message) {
            throw new Error(error.response.data.message);
        }
        throw new Error('Failed to submit feedback');
    }
};
