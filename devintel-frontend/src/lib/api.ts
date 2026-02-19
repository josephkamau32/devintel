import apiClient from './api-client';

export const sendChatMessage = async (message: string) => {
    return apiClient.post('/chat', { message });
};

export const getChatHistory = async () => {
    return apiClient.get('/chat/history');
};
