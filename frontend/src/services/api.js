import axios from 'axios'
const BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8080'
const api = axios.create({ baseURL: BASE, timeout: 5000 })
export default api