// Import components
import ChatInterface from './components/ChatInterface.js';

// Initialize chat interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('app');
    if (container) {
        new ChatInterface(container);
    } else {
        console.error('Could not find app container element');
    }
}); 