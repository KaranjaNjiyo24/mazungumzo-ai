/**
 * Stats Bar Component
 * Displays conversation statistics and system status
 */

export class StatsBar {
    constructor(options = {}) {
        this.apiService = options.apiService;
        this.updateInterval = options.updateInterval || 30000; // 30 seconds
        this.container = null;
        this.stats = {
            totalMessages: 0,
            activeSessions: 0,
            averageResponseTime: 0,
            systemStatus: 'unknown',
            uptime: 0,
            lastUpdated: null
        };
        this.updateTimer = null;
        this.isVisible = options.isVisible !== false; // Default to visible
        this.init();
    }

    init() {
        this.createStatsElement();
        this.setupEventListeners();
        this.startAutoUpdate();
        this.loadInitialStats();
    }

    createStatsElement() {
        this.container = document.createElement('div');
        this.container.className = `stats-bar ${this.isVisible ? 'visible' : 'hidden'}`;
        this.container.innerHTML = `
            <div class="stats-bar-content">
                <div class="stats-toggle">
                    <button class="stats-toggle-btn" aria-label="Toggle statistics visibility">
                        <span class="stats-toggle-icon">📊</span>
                        <span class="stats-toggle-text">Stats</span>
                    </button>
                </div>
                
                <div class="stats-container">
                    <div class="stats-section system-status">
                        <div class="stat-item">
                            <div class="stat-icon status-indicator">
                                <div class="status-dot"></div>
                            </div>
                            <div class="stat-content">
                                <div class="stat-label">System</div>
                                <div class="stat-value" data-stat="systemStatus">
                                    <span class="status-text">Checking...</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="stats-section conversation-stats">
                        <div class="stat-item">
                            <div class="stat-icon">💬</div>
                            <div class="stat-content">
                                <div class="stat-label">Messages</div>
                                <div class="stat-value" data-stat="totalMessages">
                                    <span class="stat-number">0</span>
                                </div>
                            </div>
                        </div>

                        <div class="stat-item">
                            <div class="stat-icon">👥</div>
                            <div class="stat-content">
                                <div class="stat-label">Active Sessions</div>
                                <div class="stat-value" data-stat="activeSessions">
                                    <span class="stat-number">0</span>
                                </div>
                            </div>
                        </div>

                        <div class="stat-item">
                            <div class="stat-icon">⚡</div>
                            <div class="stat-content">
                                <div class="stat-label">Avg Response</div>
                                <div class="stat-value" data-stat="averageResponseTime">
                                    <span class="stat-number">0</span>
                                    <span class="stat-unit">ms</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="stats-section system-info">
                        <div class="stat-item">
                            <div class="stat-icon">⏱️</div>
                            <div class="stat-content">
                                <div class="stat-label">Uptime</div>
                                <div class="stat-value" data-stat="uptime">
                                    <span class="uptime-text">--:--:--</span>
                                </div>
                            </div>
                        </div>

                        <div class="stat-item">
                            <div class="stat-icon">🔄</div>
                            <div class="stat-content">
                                <div class="stat-label">Last Updated</div>
                                <div class="stat-value" data-stat="lastUpdated">
                                    <span class="update-text">Never</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="stats-actions">
                    <button class="stats-refresh-btn" aria-label="Refresh statistics">
                        <span class="refresh-icon">🔄</span>
                    </button>
                </div>
            </div>
        `;
    }

    setupEventListeners() {
        // Toggle visibility
        const toggleBtn = this.container.querySelector('.stats-toggle-btn');
        toggleBtn?.addEventListener('click', () => this.toggleVisibility());

        // Manual refresh
        const refreshBtn = this.container.querySelector('.stats-refresh-btn');
        refreshBtn?.addEventListener('click', () => this.refreshStats());

        // Handle clicks on stats items for details
        const statItems = this.container.querySelectorAll('.stat-item');
        statItems.forEach(item => {
            item.addEventListener('click', (e) => this.handleStatClick(e));
        });
    }

    async loadInitialStats() {
        await this.fetchStats();
        this.updateDisplay();
    }

    async fetchStats() {
        if (!this.apiService) {
            console.warn('StatsBar: No API service provided');
            return;
        }

        try {
            // Show loading state
            this.setLoadingState(true);

            // Fetch stats from multiple endpoints
            const [healthData, statsData] = await Promise.allSettled([
                this.apiService.checkHealth(),
                this.apiService.getStats()
            ]);

            // Process health data
            if (healthData.status === 'fulfilled') {
                this.stats.systemStatus = healthData.value.status || 'healthy';
                this.stats.uptime = healthData.value.uptime || 0;
            } else {
                this.stats.systemStatus = 'error';
                console.error('Health check failed:', healthData.reason);
            }

            // Process stats data
            if (statsData.status === 'fulfilled') {
                const data = statsData.value;
                this.stats.totalMessages = data.total_messages || 0;
                this.stats.activeSessions = data.active_sessions || 0;
                this.stats.averageResponseTime = data.average_response_time || 0;
            } else {
                console.error('Stats fetch failed:', statsData.reason);
            }

            this.stats.lastUpdated = new Date();

        } catch (error) {
            console.error('Error fetching stats:', error);
            this.stats.systemStatus = 'error';
        } finally {
            this.setLoadingState(false);
        }
    }

    updateDisplay() {
        // Update system status
        this.updateSystemStatus();
        
        // Update numerical stats
        this.updateStatValue('totalMessages', this.formatNumber(this.stats.totalMessages));
        this.updateStatValue('activeSessions', this.formatNumber(this.stats.activeSessions));
        this.updateStatValue('averageResponseTime', this.formatNumber(this.stats.averageResponseTime));
        
        // Update uptime
        this.updateUptime();
        
        // Update last updated time
        this.updateLastUpdated();
    }

    updateSystemStatus() {
        const statusElement = this.container.querySelector('[data-stat="systemStatus"]');
        const statusDot = this.container.querySelector('.status-dot');
        const statusText = statusElement?.querySelector('.status-text');

        if (!statusElement || !statusDot || !statusText) return;

        // Remove existing status classes
        statusDot.className = 'status-dot';
        
        // Add appropriate status class and text
        switch (this.stats.systemStatus) {
            case 'healthy':
                statusDot.classList.add('status-healthy');
                statusText.textContent = 'Online';
                break;
            case 'degraded':
                statusDot.classList.add('status-warning');
                statusText.textContent = 'Degraded';
                break;
            case 'error':
                statusDot.classList.add('status-error');
                statusText.textContent = 'Error';
                break;
            default:
                statusDot.classList.add('status-unknown');
                statusText.textContent = 'Unknown';
        }
    }

    updateStatValue(statName, value) {
        const element = this.container.querySelector(`[data-stat="${statName}"] .stat-number`);
        if (element) {
            // Animate number change if different
            const currentValue = element.textContent;
            if (currentValue !== value.toString()) {
                element.classList.add('stat-updating');
                setTimeout(() => {
                    element.textContent = value;
                    element.classList.remove('stat-updating');
                }, 150);
            }
        }
    }

    updateUptime() {
        const uptimeElement = this.container.querySelector('[data-stat="uptime"] .uptime-text');
        if (uptimeElement && this.stats.uptime > 0) {
            uptimeElement.textContent = this.formatUptime(this.stats.uptime);
        }
    }

    updateLastUpdated() {
        const updateElement = this.container.querySelector('[data-stat="lastUpdated"] .update-text');
        if (updateElement && this.stats.lastUpdated) {
            updateElement.textContent = this.formatRelativeTime(this.stats.lastUpdated);
        }
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);

        if (days > 0) {
            return `${days}d ${hours}h ${minutes}m`;
        } else if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else {
            return `${minutes}m`;
        }
    }

    formatRelativeTime(date) {
        const now = new Date();
        const diff = (now - date) / 1000; // seconds

        if (diff < 60) {
            return 'Just now';
        } else if (diff < 3600) {
            return `${Math.floor(diff / 60)}m ago`;
        } else {
            return `${Math.floor(diff / 3600)}h ago`;
        }
    }

    setLoadingState(isLoading) {
        this.container.classList.toggle('loading', isLoading);
        
        const refreshBtn = this.container.querySelector('.stats-refresh-btn .refresh-icon');
        if (refreshBtn) {
            refreshBtn.style.animation = isLoading ? 'spin 1s linear infinite' : '';
        }
    }

    toggleVisibility() {
        this.isVisible = !this.isVisible;
        this.container.classList.toggle('visible', this.isVisible);
        this.container.classList.toggle('hidden', !this.isVisible);

        // Store preference
        try {
            localStorage.setItem('mazungumzo-stats-visible', this.isVisible.toString());
        } catch (e) {
            console.warn('Could not save stats visibility preference:', e);
        }

        this.dispatchEvent('stats-visibility-changed', { isVisible: this.isVisible });
    }

    async refreshStats() {
        await this.fetchStats();
        this.updateDisplay();
        this.dispatchEvent('stats-refreshed', { stats: this.stats });
    }

    handleStatClick(e) {
        const statItem = e.currentTarget;
        const statContent = statItem.querySelector('.stat-content');
        const label = statContent?.querySelector('.stat-label')?.textContent;
        
        // Show detailed information in a tooltip or modal
        this.showStatDetails(label, statItem);
    }

    showStatDetails(label, element) {
        // Simple implementation - could be enhanced with a proper modal
        let details = '';
        
        switch (label) {
            case 'System':
                details = `System Status: ${this.stats.systemStatus}\nLast checked: ${this.stats.lastUpdated?.toLocaleTimeString() || 'Never'}`;
                break;
            case 'Messages':
                details = `Total messages processed: ${this.stats.totalMessages}\nAcross all conversations`;
                break;
            case 'Active Sessions':
                details = `Currently active chat sessions: ${this.stats.activeSessions}`;
                break;
            case 'Avg Response':
                details = `Average AI response time: ${this.stats.averageResponseTime}ms`;
                break;
            case 'Uptime':
                details = `System uptime: ${this.formatUptime(this.stats.uptime)}`;
                break;
        }

        if (details) {
            // Create temporary tooltip
            const tooltip = document.createElement('div');
            tooltip.className = 'stats-tooltip';
            tooltip.textContent = details;
            document.body.appendChild(tooltip);

            // Position tooltip
            const rect = element.getBoundingClientRect();
            tooltip.style.left = `${rect.left}px`;
            tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;

            // Remove after delay
            setTimeout(() => tooltip.remove(), 3000);
        }
    }

    startAutoUpdate() {
        this.stopAutoUpdate();
        this.updateTimer = setInterval(() => {
            this.fetchStats().then(() => this.updateDisplay());
        }, this.updateInterval);
    }

    stopAutoUpdate() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
            this.updateTimer = null;
        }
    }

    dispatchEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, {
            detail,
            bubbles: true
        });
        this.container.dispatchEvent(event);
    }

    getElement() {
        return this.container;
    }

    getStats() {
        return { ...this.stats };
    }

    static getStoredVisibility() {
        try {
            return localStorage.getItem('mazungumzo-stats-visible') !== 'false';
        } catch (e) {
            return true; // Default to visible
        }
    }

    static create(options = {}) {
        const storedVisibility = StatsBar.getStoredVisibility();
        return new StatsBar({
            isVisible: storedVisibility,
            ...options
        });
    }

    destroy() {
        this.stopAutoUpdate();
        if (this.container) {
            this.container.remove();
        }
    }
}

export default StatsBar;
