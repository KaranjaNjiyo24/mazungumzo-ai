/**
 * Crisis Alert Component
 * Displays emergency alerts and resources when crisis keywords are detected
 */

export class CrisisAlert {
    constructor() {
        this.isVisible = false;
        this.alertElement = null;
        this.init();
    }

    init() {
        this.createAlertElement();
        this.setupEventListeners();
    }

    createAlertElement() {
        this.alertElement = document.createElement('div');
        this.alertElement.className = 'crisis-alert';
        this.alertElement.innerHTML = `
            <div class="crisis-alert-content">
                <div class="crisis-header">
                    <div class="crisis-icon">⚠️</div>
                    <h3>Immediate Support Available</h3>
                    <button class="crisis-close" aria-label="Close alert">&times;</button>
                </div>
                <div class="crisis-body">
                    <p>If you're experiencing a mental health crisis, you're not alone. Help is available 24/7.</p>
                    <div class="crisis-actions">
                        <div class="crisis-resources">
                            <h4>Emergency Contacts:</h4>
                            <div class="emergency-contacts">
                                <div class="contact-item">
                                    <span class="contact-label">Kenya Red Cross:</span>
                                    <a href="tel:1199" class="contact-link">1199</a>
                                </div>
                                <div class="contact-item">
                                    <span class="contact-label">Befrienders Kenya:</span>
                                    <a href="tel:+254722178177" class="contact-link">+254 722 178 177</a>
                                </div>
                                <div class="contact-item">
                                    <span class="contact-label">Emergency Services:</span>
                                    <a href="tel:999" class="contact-link">999</a>
                                </div>
                            </div>
                        </div>
                        <div class="crisis-buttons">
                            <button class="btn-crisis-primary" data-action="call-emergency">
                                📞 Call Emergency Line
                            </button>
                            <button class="btn-crisis-secondary" data-action="find-resources">
                                🏥 Find Local Resources
                            </button>
                            <button class="btn-crisis-secondary" data-action="safety-plan">
                                📋 Safety Planning
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            <div class="crisis-overlay"></div>
        `;
        
        document.body.appendChild(this.alertElement);
    }

    setupEventListeners() {
        // Close alert
        const closeBtn = this.alertElement.querySelector('.crisis-close');
        const overlay = this.alertElement.querySelector('.crisis-overlay');
        
        closeBtn?.addEventListener('click', () => this.hide());
        overlay?.addEventListener('click', () => this.hide());

        // Action buttons
        const actionButtons = this.alertElement.querySelectorAll('[data-action]');
        actionButtons.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleAction(e.target.dataset.action));
        });

        // Emergency contacts
        const emergencyBtn = this.alertElement.querySelector('.btn-crisis-primary');
        emergencyBtn?.addEventListener('click', () => this.callEmergency());
    }

    show(crisisData = {}) {
        if (this.isVisible) return;
        
        this.isVisible = true;
        this.alertElement.style.display = 'flex';
        
        // Update content based on crisis data
        if (crisisData.resources) {
            this.updateResources(crisisData.resources);
        }
        
        // Add show animation
        requestAnimationFrame(() => {
            this.alertElement.classList.add('crisis-alert-visible');
        });

        // Focus management for accessibility
        const firstButton = this.alertElement.querySelector('.btn-crisis-primary');
        firstButton?.focus();

        // Dispatch custom event
        this.dispatchEvent('crisis-alert-shown', { crisisData });
    }

    hide() {
        if (!this.isVisible) return;
        
        this.alertElement.classList.remove('crisis-alert-visible');
        
        setTimeout(() => {
            this.alertElement.style.display = 'none';
            this.isVisible = false;
            this.dispatchEvent('crisis-alert-hidden');
        }, 300);
    }

    updateResources(resources) {
        const resourcesContainer = this.alertElement.querySelector('.emergency-contacts');
        if (!resourcesContainer || !resources.crisis_hotlines) return;

        const contactsHTML = resources.crisis_hotlines.map(hotline => `
            <div class="contact-item">
                <span class="contact-label">${hotline.name}:</span>
                <a href="tel:${hotline.phone}" class="contact-link">${hotline.phone}</a>
                ${hotline.hours ? `<span class="contact-hours">${hotline.hours}</span>` : ''}
            </div>
        `).join('');

        resourcesContainer.innerHTML = contactsHTML;
    }

    handleAction(action) {
        switch (action) {
            case 'call-emergency':
                this.callEmergency();
                break;
            case 'find-resources':
                this.findResources();
                break;
            case 'safety-plan':
                this.showSafetyPlan();
                break;
        }
    }

    callEmergency() {
        // Show confirmation before calling
        if (confirm('This will call the Kenya Red Cross emergency line (1199). Continue?')) {
            window.location.href = 'tel:1199';
            this.dispatchEvent('crisis-action', { action: 'emergency-call' });
        }
    }

    findResources() {
        // This could open a modal with local mental health resources
        this.dispatchEvent('crisis-action', { action: 'find-resources' });
        
        // For now, show an alert with resources
        alert('Local mental health resources:\n\n' +
              '• Kenya Association of Professional Counsellors\n' +
              '• Nairobi Women\'s Hospital - Mental Health\n' +
              '• Chiromo Lane Medical Centre\n' +
              '• Talk to someone you trust\n\n' +
              'For immediate help, call 1199');
    }

    showSafetyPlan() {
        this.dispatchEvent('crisis-action', { action: 'safety-plan' });
        
        // Basic safety planning guidance
        const safetyTips = `
Safety Planning Steps:

1. Remove immediate dangers
2. Call someone you trust
3. Go to a safe place
4. Use coping strategies that work for you
5. Call emergency services if needed

Remember: This feeling is temporary and you matter.
        `.trim();
        
        alert(safetyTips);
    }

    dispatchEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, {
            detail,
            bubbles: true
        });
        this.alertElement.dispatchEvent(event);
    }

    // Static method to create and show alert
    static show(crisisData) {
        const existingAlert = document.querySelector('.crisis-alert');
        if (existingAlert) {
            existingAlert.crisisAlertInstance?.show(crisisData);
            return;
        }

        const alert = new CrisisAlert();
        existingAlert.crisisAlertInstance = alert;
        alert.show(crisisData);
    }

    destroy() {
        if (this.alertElement) {
            this.alertElement.remove();
        }
        this.isVisible = false;
    }
}

// Auto-initialize when imported
export default CrisisAlert;
