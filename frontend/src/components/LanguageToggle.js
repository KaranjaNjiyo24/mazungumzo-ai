/**
 * Language Toggle Component
 * Handles language switching between English and Swahili
 */

export class LanguageToggle {
    constructor(options = {}) {
        this.currentLanguage = options.defaultLanguage || 'en';
        this.onLanguageChange = options.onLanguageChange || (() => {});
        this.container = null;
        this.translations = {
            en: {
                english: 'English',
                swahili: 'Kiswahili',
                switchTo: 'Switch to',
                languageChanged: 'Language changed to'
            },
            sw: {
                english: 'Kiingereza',
                swahili: 'Kiswahili',
                switchTo: 'Badili kwenda',
                languageChanged: 'Lugha imebadilishwa kwenda'
            }
        };
        this.init();
    }

    init() {
        this.createToggleElement();
        this.setupEventListeners();
        this.updateUI();
    }

    createToggleElement() {
        this.container = document.createElement('div');
        this.container.className = 'language-toggle';
        this.container.innerHTML = `
            <div class="language-toggle-wrapper">
                <label class="language-toggle-label" for="language-select">
                    🌍 <span class="language-label-text">Language</span>
                </label>
                <div class="language-toggle-control">
                    <select id="language-select" class="language-select" aria-label="Select language">
                        <option value="en">🇬🇧 English</option>
                        <option value="sw">🇰🇪 Kiswahili</option>
                    </select>
                    <div class="language-toggle-visual">
                        <div class="language-option" data-lang="en">
                            <span class="language-flag">🇬🇧</span>
                            <span class="language-name">EN</span>
                        </div>
                        <div class="language-divider">|</div>
                        <div class="language-option" data-lang="sw">
                            <span class="language-flag">🇰🇪</span>
                            <span class="language-name">SW</span>
                        </div>
                        <div class="language-indicator"></div>
                    </div>
                </div>
            </div>
        `;
    }

    setupEventListeners() {
        const select = this.container.querySelector('.language-select');
        const options = this.container.querySelectorAll('.language-option');

        // Handle select change
        select?.addEventListener('change', (e) => {
            this.setLanguage(e.target.value);
        });

        // Handle visual toggle clicks
        options.forEach(option => {
            option.addEventListener('click', () => {
                const lang = option.dataset.lang;
                this.setLanguage(lang);
            });

            // Keyboard support
            option.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const lang = option.dataset.lang;
                    this.setLanguage(lang);
                }
            });
        });

        // Keyboard navigation
        this.container.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                // Handle tab navigation between options
                this.handleTabNavigation(e);
            }
        });
    }

    setLanguage(language) {
        if (language === this.currentLanguage) return;

        const previousLanguage = this.currentLanguage;
        this.currentLanguage = language;

        // Update UI
        this.updateUI();

        // Update select value
        const select = this.container.querySelector('.language-select');
        if (select) {
            select.value = language;
        }

        // Store preference
        this.saveLanguagePreference(language);

        // Notify listeners
        this.onLanguageChange(language, previousLanguage);

        // Dispatch custom event
        this.dispatchEvent('language-changed', {
            newLanguage: language,
            previousLanguage: previousLanguage
        });

        // Show feedback
        this.showLanguageChangeMessage(language);
    }

    updateUI() {
        const options = this.container.querySelectorAll('.language-option');
        const indicator = this.container.querySelector('.language-indicator');
        const labelText = this.container.querySelector('.language-label-text');

        // Update active state
        options.forEach(option => {
            const isActive = option.dataset.lang === this.currentLanguage;
            option.classList.toggle('active', isActive);
            option.setAttribute('aria-selected', isActive);
            
            if (isActive) {
                option.setAttribute('tabindex', '0');
            } else {
                option.setAttribute('tabindex', '-1');
            }
        });

        // Move indicator
        const activeOption = this.container.querySelector(`[data-lang="${this.currentLanguage}"]`);
        if (activeOption && indicator) {
            const rect = activeOption.getBoundingClientRect();
            const containerRect = this.container.querySelector('.language-toggle-visual').getBoundingClientRect();
            const offset = rect.left - containerRect.left;
            indicator.style.transform = `translateX(${offset}px)`;
        }

        // Update label text
        if (labelText) {
            const t = this.translations[this.currentLanguage];
            labelText.textContent = this.currentLanguage === 'en' ? 'Language' : 'Lugha';
        }
    }

    showLanguageChangeMessage(language) {
        const t = this.translations[language];
        const languageName = language === 'en' ? t.english : t.swahili;
        const message = `${t.languageChanged} ${languageName}`;

        // Create temporary notification
        const notification = document.createElement('div');
        notification.className = 'language-change-notification';
        notification.textContent = message;
        notification.setAttribute('role', 'status');
        notification.setAttribute('aria-live', 'polite');

        document.body.appendChild(notification);

        // Remove after animation
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    saveLanguagePreference(language) {
        try {
            localStorage.setItem('mazungumzo-language', language);
        } catch (e) {
            console.warn('Could not save language preference:', e);
        }
    }

    static getStoredLanguage() {
        try {
            return localStorage.getItem('mazungumzo-language') || 'en';
        } catch (e) {
            return 'en';
        }
    }

    handleTabNavigation(e) {
        const options = Array.from(this.container.querySelectorAll('.language-option'));
        const currentIndex = options.findIndex(opt => opt === document.activeElement);
        
        if (currentIndex === -1) return;

        let nextIndex;
        if (e.shiftKey) {
            // Shift+Tab - go backwards
            nextIndex = currentIndex === 0 ? options.length - 1 : currentIndex - 1;
        } else {
            // Tab - go forwards
            nextIndex = currentIndex === options.length - 1 ? 0 : currentIndex + 1;
        }

        e.preventDefault();
        options[nextIndex].focus();
    }

    dispatchEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, {
            detail,
            bubbles: true
        });
        this.container.dispatchEvent(event);
    }

    getCurrentLanguage() {
        return this.currentLanguage;
    }

    getTranslation(key, language = this.currentLanguage) {
        return this.translations[language]?.[key] || key;
    }

    // Method to get the toggle element for insertion into DOM
    getElement() {
        return this.container;
    }

    // Static method to create and initialize
    static create(options = {}) {
        const storedLanguage = LanguageToggle.getStoredLanguage();
        return new LanguageToggle({
            defaultLanguage: storedLanguage,
            ...options
        });
    }

    destroy() {
        if (this.container) {
            this.container.remove();
        }
    }
}

export default LanguageToggle;
