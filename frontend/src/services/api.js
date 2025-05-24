/**
 * API Service for Mazungumzo AI
 * Handles all communication with the backend
 */

export class APIService {
    constructor() {
        this.baseURL = 'http://localhost:8000';
        this.endpoints = {
            chat: '/api/v1/chat',
            stats: '/api/v1/stats', 
            resources: '/api/v1/resources',
            health: '/api/v1/health'
        };
    }

    /**
     * Send chat message to backend
     * @param {string} message - User message
     * @param {string} userId - User identifier
     * @param {string} language - Language code (en/sw)
     * @param {string} platform - Platform identifier
     * @returns {Promise<Object>} Chat response
     */
    async sendMessage(message, userId, language = 'en', platform = 'web') {
        try {
            const response = await fetch(`${this.baseURL}${this.endpoints.chat}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    message: message,
                    language: language,
                    platform: platform
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Chat API error:', error);
            throw new Error('Failed to send message. Please try again.');
        }
    }

    /**
     * Get application statistics
     * @returns {Promise<Object>} Stats data
     */
    async getStats() {
        try {
            const response = await fetch(`${this.baseURL}${this.endpoints.stats}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Stats API error:', error);
            // Return default stats if API fails
            return {
                active_users: 0,
                total_conversations: 0,
                resources_available: 0
            };
        }
    }

    /**
     * Get mental health resources
     * @returns {Promise<Object>} Resources data
     */
    async getResources() {
        try {
            const response = await fetch(`${this.baseURL}${this.endpoints.resources}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Resources API error:', error);
            throw new Error('Failed to load resources');
        }
    }

    /**
     * Check API health status
     * @returns {Promise<Object>} Health status
     */
    async checkHealth() {
        try {
            const response = await fetch(`${this.baseURL}${this.endpoints.health}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Health check error:', error);
            return { status: 'unhealthy', error: error.message };
        }
    }

    /**
     * Send feedback about a conversation
     * @param {string} userId - User identifier
     * @param {string} messageId - Message identifier
     * @param {string} feedback - Feedback type (helpful/not_helpful)
     * @returns {Promise<Object>} Feedback response
     */
    async sendFeedback(userId, messageId, feedback) {
        try {
            const response = await fetch(`${this.baseURL}${this.endpoints.chat}/feedback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    message_id: messageId,
                    feedback: feedback
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Feedback API error:', error);
            throw new Error('Failed to send feedback');
        }
    }
}

// Export singleton instance
export const apiService = new APIService();
