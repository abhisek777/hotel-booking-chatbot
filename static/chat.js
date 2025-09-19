/**
 * Hotel Booking Chat Application
 * Handles client-side chat functionality, API communication, and UI management
 * Uses vanilla JavaScript (no external libraries required)
 */

class HotelBookingChat {
    constructor() {
        // Get or create session ID from localStorage
        this.sessionId = this.getOrCreateSessionId();
        this.isLoading = false;

        // DOM element references
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatForm = document.getElementById('chatForm');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        this.bookingModal = document.getElementById('bookingModal');
        this.inputHint = document.getElementById('inputHint');
        this.errorToast = document.getElementById('errorToast');
        this.errorMessage = document.getElementById('errorMessage');

        // Initialize event listeners and UI
        this.initializeEventListeners();
        this.focusInput();

        // API endpoint configuration (change this if backend URL differs)
        this.apiEndpoint = '/api/chat';
    }

    /**
     * Get existing session ID from localStorage or create a new one
     * @returns {string} Session UUID
     */
    getOrCreateSessionId() {
        let sessionId = localStorage.getItem('hotel_chat_session_id');
        if (!sessionId) {
            sessionId = this.generateUUID();
            localStorage.setItem('hotel_chat_session_id', sessionId);
        }
        return sessionId;
    }

    /**
     * Generate a simple UUID for session identification
     * @returns {string} UUID string
     */
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * Set up all event listeners for the application
     */
    initializeEventListeners() {
        // Form submission handler
        this.chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        // Input validation and real-time hints
        this.messageInput.addEventListener('input', (e) => {
            this.validateAndHintInput(e.target.value);
        });

        // Enhanced keyboard handling
        this.messageInput.addEventListener('keydown', (e) => {
            // Send on Enter (not Shift+Enter for potential line breaks)
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
            // Clear hint on Escape
            else if (e.key === 'Escape') {
                this.hideInputHint();
            }
        });

        // Modal event listeners
        document.getElementById('closeModal').addEventListener('click', () => {
            this.closeBookingModal();
        });

        document.getElementById('newBookingBtn').addEventListener('click', () => {
            this.startNewBooking();
        });

        // Close modal on overlay click
        this.bookingModal.addEventListener('click', (e) => {
            if (e.target === this.bookingModal) {
                this.closeBookingModal();
            }
        });

        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Close modal on Escape
            if (e.key === 'Escape' && this.bookingModal.style.display !== 'none') {
                this.closeBookingModal();
            }
            // Focus input on any alphanumeric key (if not in modal)
            else if (this.bookingModal.style.display === 'none' &&
                     !this.isLoading &&
                     e.target !== this.messageInput &&
                     /^[a-zA-Z0-9]$/.test(e.key)) {
                this.messageInput.focus();
            }
        });

        // Error toast dismissal
        const dismissError = document.getElementById('dismissError');
        if (dismissError) {
            dismissError.addEventListener('click', () => {
                this.hideErrorToast();
            });
        }
    }

    /**
     * Focus the message input field
     */
    focusInput() {
        if (this.messageInput && !this.isLoading) {
            this.messageInput.focus();
        }
    }

    /**
     * Validate input and show contextual hints
     * @param {string} value - Current input value
     */
    validateAndHintInput(value) {
        const trimmedValue = value.trim();

        // Clear existing hints
        this.hideInputHint();

        // Don't show hints for very short input
        if (trimmedValue.length < 2) return;

        // Detect potential date input and show helpful format hints
        const dateWords = [
            'tomorrow', 'today', 'next week', 'monday', 'tuesday', 'wednesday',
            'thursday', 'friday', 'saturday', 'sunday', 'january', 'february',
            'march', 'april', 'may', 'june', 'july', 'august', 'september',
            'october', 'november', 'december'
        ];

        const hasDateWord = dateWords.some(word =>
            trimmedValue.toLowerCase().includes(word)
        );

        const hasDatePattern = /\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}/.test(trimmedValue) ||
                              /\d{4}-\d{1,2}-\d{1,2}/.test(trimmedValue) ||
                              /\b\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/i.test(trimmedValue);

        if (hasDateWord || hasDatePattern) {
            this.showInputHint('💡 Date formats: "tomorrow", "2024-01-15", "January 15th", etc.', 'info');
        }

        // Detect potential guest count input
        const hasNumbers = /\d+/.test(trimmedValue);
        const hasGuestWords = /\b(guest|people|person|visitor)\b/i.test(trimmedValue);

        if (hasNumbers && hasGuestWords) {
            this.showInputHint('👥 Guest count: Use numbers like "2", "three people", or "just me"', 'info');
        }
    }

    /**
     * Show input validation hint
     * @param {string} message - Hint message to display
     * @param {string} type - Hint type: 'info', 'warning', 'error'
     */
    showInputHint(message, type = 'info') {
        if (!this.inputHint) return;

        this.inputHint.textContent = message;
        this.inputHint.style.display = 'block';

        // Style based on type
        switch (type) {
            case 'error':
                this.inputHint.style.background = '#f8d7da';
                this.inputHint.style.color = '#721c24';
                this.inputHint.style.borderColor = '#f5c6cb';
                break;
            case 'warning':
                this.inputHint.style.background = '#fff3cd';
                this.inputHint.style.color = '#856404';
                this.inputHint.style.borderColor = '#ffeaa7';
                break;
            default: // info
                this.inputHint.style.background = '#d1ecf1';
                this.inputHint.style.color = '#0c5460';
                this.inputHint.style.borderColor = '#bee5eb';
        }
    }

    /**
     * Hide input validation hint
     */
    hideInputHint() {
        if (this.inputHint) {
            this.inputHint.style.display = 'none';
        }
    }

    /**
     * Send message to the backend API
     */
    async sendMessage() {
        const message = this.messageInput.value.trim();

        // Client-side validation
        if (!message) {
            this.showInputHint('⚠️ Please enter a message', 'error');
            this.messageInput.focus();
            return;
        }

        if (message.length > 500) {
            this.showInputHint('⚠️ Message too long (max 500 characters)', 'error');
            return;
        }

        if (this.isLoading) {
            return; // Prevent multiple simultaneous requests
        }

        // Clear input and add user message to chat
        this.messageInput.value = '';
        this.hideInputHint();
        this.addMessage(message, 'user');
        this.setLoadingState(true);

        try {
            // Send request to backend API
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });

            let data;
            try {
                data = await response.json();
            } catch (parseError) {
                throw new Error('Invalid response from server');
            }

            // Handle HTTP errors
            if (!response.ok) {
                throw new Error(data.error || `Server error: ${response.status}`);
            }

            // Update session ID if provided by server
            if (data.session_id) {
                this.sessionId = data.session_id;
                localStorage.setItem('hotel_chat_session_id', this.sessionId);
            }

            // Add bot response to chat
            if (data.reply) {
                this.addMessage(data.reply, 'bot');
            }

            // Handle booking completion
            if (data.complete && data.booking) {
                setTimeout(() => {
                    this.showBookingConfirmation(data.booking);
                }, 800); // Small delay for better UX
            }

        } catch (error) {
            console.error('Chat API error:', error);

            // Show user-friendly error message
            this.addMessage(
                `Sorry, I encountered an error: ${error.message}. Please try again.`,
                'bot'
            );
            this.showErrorToast(error.message);

        } finally {
            this.setLoadingState(false);
            this.focusInput();
        }
    }

    /**
     * Set loading state for the application
     * @param {boolean} loading - Whether the app is in loading state
     */
    setLoadingState(loading) {
        this.isLoading = loading;

        // Update button and input states
        this.sendButton.disabled = loading;
        this.messageInput.disabled = loading;

        // Show/hide loading indicator
        if (loading) {
            this.loadingIndicator.style.display = 'flex';
            this.loadingIndicator.setAttribute('aria-hidden', 'false');
        } else {
            this.loadingIndicator.style.display = 'none';
            this.loadingIndicator.setAttribute('aria-hidden', 'true');
        }

        // Auto-scroll to show loading indicator
        if (loading) {
            this.scrollToBottom();
        }
    }

    /**
     * Add a message to the chat interface
     * @param {string} content - Message content
     * @param {string} type - Message type: 'user' or 'bot'
     */
    addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.setAttribute('role', 'article');

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        // Handle multi-line content (preserve formatting for bot confirmations)
        if (content.includes('\n')) {
            const pre = document.createElement('pre');
            pre.textContent = content;
            messageContent.appendChild(pre);
        } else {
            const p = document.createElement('p');
            p.textContent = content;
            messageContent.appendChild(p);
        }

        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        const timestamp = this.formatTime(new Date());
        messageTime.textContent = timestamp;
        messageTime.setAttribute('aria-label', `Message sent at ${timestamp}`);

        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);
        this.chatMessages.appendChild(messageDiv);

        this.scrollToBottom();

        // Announce bot messages to screen readers
        if (type === 'bot') {
            this.announceToScreenReader(`Assistant: ${content}`);
        }
    }

    /**
     * Announce message to screen readers
     * @param {string} message - Message to announce
     */
    announceToScreenReader(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;

        document.body.appendChild(announcement);

        // Clean up after announcement
        setTimeout(() => {
            if (document.body.contains(announcement)) {
                document.body.removeChild(announcement);
            }
        }, 1000);
    }

    /**
     * Format timestamp for display
     * @param {Date} date - Date to format
     * @returns {string} Formatted time string
     */
    formatTime(date) {
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
    }

    /**
     * Scroll chat container to bottom
     */
    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }

    /**
     * Show booking confirmation modal
     * @param {Object} booking - Booking data from server
     */
    showBookingConfirmation(booking) {
        const bookingDetails = document.getElementById('bookingDetails');
        if (!bookingDetails) return;

        // Create booking summary HTML with proper escaping
        const summaryHtml = `
            <div class="booking-summary">
                <h3>Reservation Details</h3>
                <div class="booking-detail">
                    <span class="label">Name:</span>
                    <span class="value">${this.escapeHtml(booking.name)}</span>
                </div>
                <div class="booking-detail">
                    <span class="label">Check-in:</span>
                    <span class="value">${this.escapeHtml(booking.checkin)}</span>
                </div>
                <div class="booking-detail">
                    <span class="label">Check-out:</span>
                    <span class="value">${this.escapeHtml(booking.checkout)}</span>
                </div>
                <div class="booking-detail">
                    <span class="label">Guests:</span>
                    <span class="value">${booking.guests}</span>
                </div>
                <div class="booking-detail">
                    <span class="label">Breakfast:</span>
                    <span class="value">${booking.breakfast ? 'Yes' : 'No'}</span>
                </div>
                <div class="booking-detail">
                    <span class="label">Payment:</span>
                    <span class="value">${this.escapeHtml(booking.payment_method)}</span>
                </div>
            </div>
            <div class="booking-id">
                <p><strong>Booking ID: #${booking.id}</strong></p>
                <p><small>Created: ${this.formatDate(booking.created_at)}</small></p>
            </div>
        `;

        bookingDetails.innerHTML = summaryHtml;

        // Show modal with proper accessibility
        this.bookingModal.style.display = 'flex';
        this.bookingModal.setAttribute('aria-hidden', 'false');

        // Focus close button for keyboard navigation
        const closeButton = document.getElementById('closeModal');
        if (closeButton) {
            closeButton.focus();
        }

        // Announce to screen readers
        this.announceToScreenReader('Booking confirmed! Details are displayed in a dialog.');
    }

    /**
     * Close booking confirmation modal
     */
    closeBookingModal() {
        this.bookingModal.style.display = 'none';
        this.bookingModal.setAttribute('aria-hidden', 'true');
        this.focusInput();
    }

    /**
     * Start a new booking session
     */
    startNewBooking() {
        // Clear session storage and generate new session
        localStorage.removeItem('hotel_chat_session_id');
        this.sessionId = this.generateUUID();
        localStorage.setItem('hotel_chat_session_id', this.sessionId);

        // Clear chat messages and show initial bot message
        this.chatMessages.innerHTML = `
            <div class="message bot-message" role="article">
                <div class="message-content">
                    <p>Hello! Welcome to our hotel booking service. Let's get started!</p>
                    <p>What's your name?</p>
                </div>
                <div class="message-time" aria-label="Message time">${this.formatTime(new Date())}</div>
            </div>
        `;

        this.closeBookingModal();
        this.focusInput();

        // Announce new session to screen readers
        this.announceToScreenReader('New booking session started. Please provide your name.');
    }

    /**
     * Show error toast notification
     * @param {string} message - Error message to display
     */
    showErrorToast(message) {
        if (!this.errorToast || !this.errorMessage) return;

        this.errorMessage.textContent = message;
        this.errorToast.style.display = 'flex';

        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.hideErrorToast();
        }, 5000);
    }

    /**
     * Hide error toast notification
     */
    hideErrorToast() {
        if (this.errorToast) {
            this.errorToast.style.display = 'none';
        }
    }

    /**
     * Format date for display
     * @param {string} dateString - ISO date string
     * @returns {string} Formatted date string
     */
    formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return dateString; // Fallback to original string
        }
    }

    /**
     * Escape HTML to prevent XSS attacks
     * @param {string} text - Text to escape
     * @returns {string} HTML-escaped text
     */
    escapeHtml(text) {
        if (typeof text !== 'string') return text;

        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };

        return text.replace(/[&<>"']/g, function(match) {
            return map[match];
        });
    }
}

/**
 * Initialize the chat application when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
    // Check for required DOM elements
    const requiredElements = [
        'chatMessages', 'messageInput', 'sendButton', 'chatForm',
        'loadingIndicator', 'bookingModal'
    ];

    const missingElements = requiredElements.filter(id => !document.getElementById(id));

    if (missingElements.length > 0) {
        console.error('Missing required DOM elements:', missingElements);
        return;
    }

    // Initialize chat application
    try {
        window.hotelChat = new HotelBookingChat();
        console.log('Hotel booking chat initialized successfully');
    } catch (error) {
        console.error('Failed to initialize chat application:', error);

        // Show basic error message to user
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = `
                <div class="message bot-message" role="article">
                    <div class="message-content">
                        <p>Sorry, there was an error loading the chat application. Please refresh the page and try again.</p>
                    </div>
                </div>
            `;
        }
    }
});