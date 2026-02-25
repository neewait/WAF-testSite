// Простой API-клиент для приложения
const API = {
    async request(endpoint, options = {}) {
        const response = await fetch(`/api${endpoint}`, {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    },
    
    // Пример: получение чувствительных данных (для тестирования)
    async getSensitiveData(id) {
        return this.request(`/sensitive/${id}`);
    },
    
    // Пример: поиск пользователей (уязвимый endpoint)
    async searchUsers(username) {
        const formData = new FormData();
        formData.append('username', username);
        const response = await fetch('/api/users/search', {
            method: 'POST',
            body: formData
        });
        return response.json();
    }
};