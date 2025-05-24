/**
 * Message Formatter Utilities
 * Handles message formatting, sanitization, and display utilities
 */

export class MessageFormatter {
    constructor() {
        this.translations = {
            en: {
                typing: 'Mazungumzo is typing...',
                sendButton: 'Send',
                placeholder: 'Type your message...',
                crisisTitle: '⚠️ Crisis Support Detected',
                crisisMessage: 'I see you might need immediate help. Please contact:',
                errorMessage: 'Sorry, there was a technical issue. Please try again.',
                welcomeMessage: 'Hello! I\'m Mazungumzo, your mental health companion. I can help you in English or Swahili. How are you feeling today?'
            },
            sw: {
                typing: 'Mazungumzo anaandika...',
                sendButton: 'Tuma',
                placeholder: 'Andika ujumbe wako...',
                crisisTitle: '⚠️ Msaada wa Haraka Umegundulika',
                crisisMessage: 'Naona unaweza kuhitaji msaada wa haraka. Tafadhali wasiliana na:',
                errorMessage: 'Pole sana, kuna tatizo la kiufundi. Tafadhali jaribu tena.',
                welcomeMessage: 'Hujambo! Mimi ni Mazungumzo, rafiki yako wa kusaidia katika mambo ya afya ya akili. Naweza kukusaidia kwa lugha ya Kiingereza au Kiswahili. Unahisije leo?'
            }
        };
    }

    /**
     * Sanitize HTML content to prevent XSS
     * @param {string} content - Raw content
     * @returns {string} Sanitized content
     */
    sanitizeHTML(content) {
        const div = document.createElement('div');
        div.textContent = content;
        return div.innerHTML;
    }

    /**
     * Format message content for display
     * @param {string} content - Message content
     * @param {boolean} allowHTML - Whether to allow basic HTML formatting
     * @returns {string} Formatted content
     */
    formatMessage(content, allowHTML = false) {
        if (!content) return '';

        // Sanitize content first
        let formatted = allowHTML ? content : this.sanitizeHTML(content);

        // Convert newlines to <br> tags
        formatted = formatted.replace(/\n/g, '<br>');

        // Convert URLs to links (basic implementation)
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        formatted = formatted.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');

        // Convert phone numbers to tel links (Kenyan format)
        const phoneRegex = /(\+254\d{9}|\d{10})/g;
        formatted = formatted.replace(phoneRegex, '<a href="tel:$1">$1</a>');

        return formatted;
    }

    /**
     * Get translated text based on current language
     * @param {string} key - Translation key
     * @param {string} language - Language code (en/sw)
     * @returns {string} Translated text
     */
    translate(key, language = 'en') {
        return this.translations[language]?.[key] || this.translations.en[key] || key;
    }

    /**
     * Format timestamp for display
     * @param {Date|string} timestamp - Timestamp
     * @param {string} language - Language code
     * @returns {string} Formatted timestamp
     */
    formatTimestamp(timestamp, language = 'en') {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) {
            return language === 'sw' ? 'Sasa hivi' : 'Just now';
        } else if (diffMins < 60) {
            return language === 'sw' ? `Dakika ${diffMins} zilizopita` : `${diffMins}m ago`;
        } else if (diffHours < 24) {
            return language === 'sw' ? `Saa ${diffHours} zilizopita` : `${diffHours}h ago`;
        } else if (diffDays < 7) {
            return language === 'sw' ? `Siku ${diffDays} zilizopita` : `${diffDays}d ago`;
        } else {
            const options = { 
                month: 'short', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            };
            return date.toLocaleDateString(language === 'sw' ? 'sw-KE' : 'en-US', options);
        }
    }

    /**
     * Generate a unique message ID
     * @returns {string} Unique message ID
     */
    generateMessageId() {
        return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Detect if message contains crisis indicators
     * @param {string} message - Message content
     * @returns {boolean} Whether message might indicate crisis
     */
    detectCrisisIndicators(message) {
        const crisisKeywords = [
            // English
            'suicide', 'kill myself', 'end it all', 'don\'t want to live',
            'cutting', 'self harm', 'overdose', 'emergency',
            
            // Swahili
            'kujiua', 'kufa', 'maumivu', 'tatizo kubwa',
            'msaada wa haraka', 'emergency', 'hospitali'
        ];

        const messageLower = message.toLowerCase();
        return crisisKeywords.some(keyword => messageLower.includes(keyword));
    }

    /**
     * Format crisis resources for display
     * @param {Array} resources - Array of crisis resources
     * @param {string} language - Language code
     * @returns {string} Formatted HTML for resources
     */
    formatCrisisResources(resources, language = 'en') {
        if (!resources || resources.length === 0) {
            return '';
        }

        const title = this.translate('crisisMessage', language);
        let html = `<p><strong>${title}</strong></p><div class="resources">`;

        resources.forEach(resource => {
            html += `<div class="resource-item">${this.formatMessage(resource, true)}</div>`;
        });

        html += '</div>';
        return html;
    }

    /**
     * Truncate text to specified length
     * @param {string} text - Text to truncate
     * @param {number} maxLength - Maximum length
     * @returns {string} Truncated text
     */
    truncateText(text, maxLength = 100) {
        if (!text || text.length <= maxLength) {
            return text;
        }
        return text.substr(0, maxLength - 3) + '...';
    }

    /**
     * Format user input before sending
     * @param {string} input - Raw user input
     * @returns {string} Cleaned input
     */
    formatUserInput(input) {
        if (!input) return '';
        
        // Trim whitespace
        let formatted = input.trim();
        
        // Remove excessive whitespace
        formatted = formatted.replace(/\s+/g, ' ');
        
        // Limit length (reasonable chat message limit)
        formatted = formatted.substr(0, 1000);
        
        return formatted;
    }
}

// Export singleton instance
export const messageFormatter = new MessageFormatter();
