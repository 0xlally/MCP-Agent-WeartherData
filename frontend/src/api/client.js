import axios from 'axios';

const instance = axios.create({
  baseURL: '/api',
  timeout: 20000
});

instance.interceptors.request.use(
  (config) => {
    const token = window.localStorage.getItem('token');
    const apiKey = window.localStorage.getItem('api_key');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (apiKey) {
      config.headers['X-API-KEY'] = apiKey;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

instance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      window.localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default instance;
