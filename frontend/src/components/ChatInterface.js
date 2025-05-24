/**
 * ChatInterface Component
 * Main chat interface that orchestrates all other components
 */

import { apiService } from '../services/api.js';
import { messageFormatter } from '../services/messageFormatter.js';

export default class ChatInterface {
    constructor(container) {
        this.container = container;
        this.currentLanguage = 'en';
        this.userId = this.generateUserId();
        this.isTyping = false;
        this.messageHistory = [];
        
        // Component references
        this.components = {
            messages: null,
            input: null,
            statsBar: null,
            languageToggle: null,
            crisisAlert: null
        };
        
        this.init();
    }

    /**
     * Initialize the chat interface
     */
    init() {
        this.render();
        this.bindEvents();
        this.loadInitialData();
    }

    /**
     * Generate unique user ID
     */
    generateUserId() {
        return `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Render the main chat interface
     */
    render() {
        this.container.innerHTML = `
            <div class="header">
                <h1>🤝 Mazungumzo AI</h1>
                <p>Your Mental Health Companion • Rafiki wa Afya ya Akili</p>
                
                <div class="language-selector" id="languageSelector">
                    <span>Language:</span>
                    <button class="language-btn active" data-lang="en" aria-label="Switch to English">English</button>
                    <button class="language-btn" data-lang="sw" aria-label="Switch to Kiswahili">Kiswahili</button>
                </div>
            </div>

            <div class="stats-bar" id="statsBar">
                <div class="stat-item">
                    <div class="stat-value" id="activeUsers">0</div>
                    <div class="stat-label">Active Users</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="totalConversations">0</div>
                    <div class="stat-label">Conversations</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="resourcesAvailable">0</div>
                    <div class="stat-label">Resources</div>
                </div>
            </div>

            <div class="chat-container">
                <div class="messages" id="messages" role="log" aria-live="polite" aria-label="Chat messages">
                    <div class="demo-note">
                        <strong>🚀 Hackathon Demo:</strong> This is a working prototype of Mazungumzo AI, built for the Cerebras + OpenRouter + Qwen3 hackathon. Try asking about mental health support in English or Swahili!
                    </div>
                    
                    <div class="message bot">
                        <div class="message-bubble">
                            Hujambo! Mimi ni Mazungumzo, rafiki yako wa kusaidia katika mambo ya afya ya akili. Naweza kukusaidia kwa lugha ya Kiingereza au Kiswahili. Unahisije leo?<br><br>
                            Hello! I'm Mazungumzo, your mental health companion. I can help you in English or Swahili. How are you feeling today?
                        </div>
                    </div>
                </div>

                <div class="typing-indicator" id="typingIndicator" aria-live="polite">
                    <span class="typing-text">Mazungumzo is typing</span><span class="typing-dots"></span>
                </div>

                <div class="crisis-alert" id="crisisAlert" role="alert" aria-live="assertive">
                    <button class="close-btn" onclick="this.parentElement.classList.remove('show')" aria-label="Close crisis alert">×</button>
                    <strong>⚠️ Crisis Support Detected</strong>
                    <p>I see you might need immediate help. Please contact:</p>
                    <div class="resources" id="crisisResources"></div>
                </div>

                <div class="input-area">
                    <textarea 
                        class="form-control message-input" 
                        id="messageInput"
                        placeholder="Type your message... / Andika ujumbe wako..."
                        rows="1"
                        aria-label="Type your message"
                    ></textarea>
                    <button class="btn btn-primary send-button" id="sendButton" aria-label="Send message">
                        <span class="btn-text">Send</span>
                        <span class="icon">→</span>
                    </button>
                </div>
            </div>
        `;
        
        // Cache component references
        this.components = {
            messages: document.getElementById('messages'),
            input: document.getElementById('messageInput'),
            sendButton: document.getElementById('sendButton'),
            statsBar: document.getElementById('statsBar'),
            languageSelector: document.getElementById('languageSelector'),
            crisisAlert: document.getElementById('crisisAlert'),
            typingIndicator: document.getElementById('typingIndicator')
        };
    }

    /**
     * Bind event handlers
     */
    bindEvents() {
        // Send button click
        this.components.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter key press (with Shift+Enter for new line)
        this.components.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.components.input.addEventListener('input', () => this.autoResizeTextarea());

        // Language selection
        this.components.languageSelector.addEventListener('click', (e) => {
            if (e.target.classList.contains('language-btn')) {
                this.switchLanguage(e.target.dataset.lang);
            }
        });

        // Demo keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'd') {
                e.preventDefault();
                this.loadDemoConversation();
            }
            if (e.ctrlKey && e.key === 'r') {
                e.preventDefault();
                this.updateStats();
            }
        });
    }

    /**
     * Auto-resize textarea based on content
     */
    autoResizeTextarea() {
        const textarea = this.components.input;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    /**
     * Switch language
     */
    switchLanguage(lang) {
        this.currentLanguage = lang;
        
        // Update active button
        this.components.languageSelector.querySelectorAll('.language-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.lang === lang);
        });

        // Update UI text
        this.updateUILanguage();
        
        // Update welcome message if it's the first message
        if (this.messageHistory.length <= 1) {
            this.clearChat();
            this.addMessage('assistant', messageFormatter.translate('welcomeMessage', this.currentLanguage));
        }
    }

    /**
     * Update UI text based on current language
     */
    updateUILanguage() {
        const texts = {
            en: {
                placeholder: 'Type your message...',
                send: 'Send',
                typing: 'Mazungumzo is typing'
            },
            sw: {
                placeholder: 'Andika ujumbe wako...',
                send: 'Tuma',
                typing: 'Mazungumzo anaandika'
            }
        };

        const currentTexts = texts[this.currentLanguage] || texts.en;
        
        this.components.input.placeholder = currentTexts.placeholder;
        this.components.sendButton.querySelector('.btn-text').textContent = currentTexts.send;
        this.components.typingIndicator.querySelector('.typing-text').textContent = currentTexts.typing;
    }

    /**
     * Load initial data
     */
    async loadInitialData() {
        await this.updateStats();
        
        // Add welcome message to history
        this.messageHistory.push({
            type: 'bot',
            content: messageFormatter.translate('welcomeMessage', this.currentLanguage),
            timestamp: new Date(),
            id: messageFormatter.generateMessageId()
        });
    }

    /**
     * Send a message
     */
    async sendMessage() {
        const message = messageFormatter.formatUserInput(this.components.input.value);
        
        if (!message || this.isTyping) return;

        // Add user message
        this.addMessage(message, 'user');
        this.components.input.value = '';
        this.autoResizeTextarea();
        
        // Show typing indicator
        this.showTyping(true);
        
        try {
            // Send to API
            const response = await apiService.sendMessage(
                message, 
                this.userId, 
                this.currentLanguage, 
                'web'
            );
            
            // Hide typing indicator
            this.showTyping(false);
            
            // Add bot response
            const messageClass = response.is_crisis ? 'crisis' : 'bot';
            this.addMessage(response.response, messageClass, {
                isCrisis: response.is_crisis,
                confidence: response.confidence,
                resources: response.resources
            });
            
            // Show crisis alert if needed
            if (response.is_crisis && response.resources) {
                this.showCrisisAlert(response.resources);
            }
            
            // Update stats
            this.updateStats();
            
        } catch (error) {
            this.showTyping(false);
            const errorMsg = messageFormatter.translate('errorMessage', this.currentLanguage);
            this.addMessage(errorMsg, 'bot');
            console.error('Chat error:', error);
        }
    }

    /**
     * Add a message to the chat
     */
    addMessage(content, type, metadata = {}) {
        const messageId = messageFormatter.generateMessageId();
        const timestamp = new Date();
        
        // Create message element
        const messageEl = document.createElement('div');
        messageEl.className = `message ${type}`;
        messageEl.dataset.messageId = messageId;
        
        messageEl.innerHTML = `
            <div class="message-bubble">
                ${messageFormatter.formatMessage(content, true)}
            </div>
        `;
        
        // Add to DOM
        this.components.messages.appendChild(messageEl);
        this.scrollToBottom();
        
        // Add to history
        this.messageHistory.push({
            id: messageId,
            type,
            content,
            timestamp,
            metadata
        });
        
        // Animate in
        messageEl.classList.add('fade-in');
    }

    /**
     * Show/hide typing indicator
     */
    showTyping(show) {
        this.isTyping = show;
        this.components.typingIndicator.classList.toggle('show', show);
        this.components.sendButton.disabled = show;
        
        if (show) {
            this.scrollToBottom();
        }
    }

    /**
     * Show crisis alert
     */
    showCrisisAlert(resources) {
        const resourcesHtml = messageFormatter.formatCrisisResources(resources, this.currentLanguage);
        this.components.crisisAlert.querySelector('#crisisResources').innerHTML = resourcesHtml;
        this.components.crisisAlert.classList.add('show');
        
        // Auto-hide after 15 seconds
        setTimeout(() => {
            this.components.crisisAlert.classList.remove('show');
        }, 15000);
    }

    /**
     * Update statistics
     */
    async updateStats() {
        try {
            const stats = await apiService.getStats();
            
            document.getElementById('activeUsers').textContent = stats.active_users || 0;
            document.getElementById('totalConversations').textContent = stats.total_conversations || 0;
            document.getElementById('resourcesAvailable').textContent = stats.resources_available || 0;
            
        } catch (error) {
            console.error('Failed to update stats:', error);
        }
    }

    /**
     * Scroll to bottom of messages
     */
    scrollToBottom() {
        setTimeout(() => {
            this.components.messages.scrollTop = this.components.messages.scrollHeight;
        }, 100);
    }

    /**
     * Load demo conversation for presentations
     */
    loadDemoConversation() {
        setTimeout(() => {
            this.addMessage("Nimehisi vibaya sana wiki hii... (I've been feeling really bad this week...)", 'user');
        }, 1000);
        
        setTimeout(() => {
            this.showTyping(true);
        }, 2000);
        
        setTimeout(() => {
            this.showTyping(false);
            this.addMessage("Pole sana kwa hali yako. Ni muhimu sana kuongea kuhusu hisia zako. Je, unaweza kuniambia ni nini kimekufanya uhisi hivyo? Mimi nipo hapa kukusikiliza bila kuhukumu. (I'm sorry about how you're feeling. It's very important to talk about your feelings. Can you tell me what has made you feel this way? I'm here to listen without judgment.)", 'bot');
        }, 4000);
    }

    /**
     * Clear chat history
     */
    clearChat() {
        this.messageHistory = [];
        this.components.messages.innerHTML = `
            <div class="message bot">
                <div class="message-bubble">
                    ${messageFormatter.translate('welcomeMessage', this.currentLanguage)}
                </div>
            </div>
        `;
    }

    /**
     * Get current chat state
     */
    getChatState() {
        return {
            userId: this.userId,
            language: this.currentLanguage,
            messageHistory: this.messageHistory,
            isTyping: this.isTyping
        };
    }
}
