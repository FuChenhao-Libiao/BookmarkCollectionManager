/**
 * API 服务层 - 统一处理后端请求
 */

const API_BASE = 'http://localhost:8000';

const api = {
    /**
     * 通用请求方法
     */
    async request(url, options = {}) {
        try {
            const response = await fetch(`${API_BASE}${url}`, {
                headers: { 'Content-Type': 'application/json' },
                ...options,
            });

            // 文件流响应（音频文件）
            if (response.headers.get('content-type')?.includes('audio/')) {
                return response;
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `请求失败 (${response.status})`);
            }

            return data;
        } catch (error) {
            if (error.message === 'Failed to fetch') {
                throw new Error('无法连接后端服务，请确认服务已启动');
            }
            throw error;
        }
    },

    /**
     * 获取服务状态
     */
    async getStatus() {
        return this.request('/api/status');
    },

    /**
     * 获取预设风格列表
     */
    async getStyles() {
        return this.request('/api/styles');
    },

    /**
     * 生成音乐
     */
    async generateMusic(params) {
        return this.request('/api/generate', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    },

    /**
     * 获取音频文件 URL
     */
    getMusicUrl(id) {
        return `${API_BASE}/api/music/${id}`;
    },

    /**
     * 获取生成历史
     */
    async getHistory(page = 1, pageSize = 12, style = null) {
        let url = `/api/history?page=${page}&page_size=${pageSize}`;
        if (style) url += `&style=${style}`;
        return this.request(url);
    },

    /**
     * 删除历史记录
     */
    async deleteHistory(id) {
        return this.request(`/api/history/${id}`, { method: 'DELETE' });
    },
};
