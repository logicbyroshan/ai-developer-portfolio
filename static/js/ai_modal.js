// AI Modal Functionality

document.addEventListener('DOMContentLoaded', function () {
    const openModalBtn = document.getElementById('open-ai-modal');
    const closeModalBtn = document.getElementById('close-ai-modal');
    const modal = document.getElementById('ai-chat-modal');
    const modalOverlay = document.getElementById('ai-modal-overlay');

    // Conversation history for multi-turn context (Gemini format)
    let conversationHistory = [];

    // Open modal
    function openModal() {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden'; // Prevent background scrolling

        // Hide hero stats cards to prevent overlap
        const heroStats = document.querySelectorAll('.hero-stat-card');
        heroStats.forEach(stat => stat.style.visibility = 'hidden');

        // Focus on textarea when modal opens
        setTimeout(() => {
            const textarea = modal.querySelector('textarea[name="question"]');
            if (textarea) {
                textarea.focus();
            }
        }, 300);
    }

    // Close modal
    function closeModal() {
        modal.classList.remove('active');
        document.body.style.overflow = ''; // Restore scrolling

        // Show hero stats cards again
        const heroStats = document.querySelectorAll('.hero-stat-card');
        heroStats.forEach(stat => stat.style.visibility = 'visible');
    }

    // Event listeners
    if (openModalBtn) {
        openModalBtn.addEventListener('click', openModal);
    }

    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeModal);
    }

    if (modalOverlay) {
        modalOverlay.addEventListener('click', closeModal);
    }

    // Close modal on Escape key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeModal();
        }
    });

    // Character counter functionality
    const textarea = modal.querySelector('textarea[name="question"]');
    const charCounter = modal.querySelector('#char-counter');

    if (textarea && charCounter) {
        textarea.addEventListener('input', function () {
            const count = this.value.length;
            charCounter.textContent = count;

            // Auto-resize textarea
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });

        // Add Ctrl+Enter functionality (Ctrl+Enter on Windows/Linux, Cmd+Enter on Mac)
        textarea.addEventListener('keydown', function (e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault(); // Prevent default Enter behavior

                // Find the form and trigger submit
                const form = this.closest('form');
                if (form) {
                    const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
                    form.dispatchEvent(submitEvent);
                }
            }
        });
    }



    // Form submission handling
    const aiForm = modal.querySelector('#ai-form');
    if (aiForm) {
        aiForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const submitBtn = this.querySelector('.submit-btn');
            const textarea = this.querySelector('textarea[name="question"]');
            const charCounter = modal.querySelector('#char-counter');
            const originalContent = submitBtn.innerHTML;

            // Get the question before clearing
            const question = textarea.value.trim();

            // Validate question
            if (!question) {
                alert('Please enter a question before submitting.');
                return;
            }

            // Show loading state
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            submitBtn.disabled = true;

            // Add user message to chat
            addMessageToChat('user', question);

            // Add typing indicator
            addTypingIndicator();

            // Create FormData BEFORE clearing the textarea
            const formData = new FormData(this);

            // Append conversation history for multi-turn context
            if (conversationHistory.length > 0) {
                formData.append('conversation_history', JSON.stringify(conversationHistory));
            }

            // Now clear the textarea after FormData is created
            textarea.value = '';
            if (charCounter) {
                charCounter.textContent = '0';
            }
            textarea.style.height = 'auto';

            // Submit form data
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
                .then(response => response.json())
                .then(data => {
                    removeTypingIndicator();

                    if (data.success) {
                        addMessageToChat('ai', data.response);
                        // Track both user and model turns in history
                        conversationHistory.push({ role: 'user', parts: [question] });
                        conversationHistory.push({ role: 'model', parts: [data.response] });
                    } else {
                        addMessageToChat('ai', 'Sorry, I encountered an error. Please try again.');
                    }
                })
                .catch(error => {
                    removeTypingIndicator();
                    addMessageToChat('ai', 'Sorry, I encountered an error. Please try again.');
                })
                .finally(() => {
                    // Restore button
                    submitBtn.innerHTML = originalContent;
                    submitBtn.disabled = false;
                });
        });
    }

    function formatAIMessage(message) {
        // Convert markdown-like formatting to HTML (WhatsApp style)
        let formatted = message;

        // Convert **bold** to <strong>
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Convert *italic* to <em>
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

        // Convert bullet points • to proper HTML
        formatted = formatted.replace(/^• (.*$)/gim, '• $1<br>');

        // Convert line breaks to <br>
        formatted = formatted.replace(/\n/g, '<br>');

        // Convert multiple spaces to single space but preserve intentional formatting
        formatted = formatted.replace(/  +/g, ' ');

        return formatted;
    }

    function addMessageToChat(type, message) {
        const messagesContainer = modal.querySelector('#ai-chat-messages');
        if (!messagesContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `${type}-message`;

        if (type === 'user') {
            messageDiv.innerHTML = `
                <div class="message-bubble">${message}</div>
            `;
        } else {
            const formattedMessage = formatAIMessage(message);
            messageDiv.innerHTML = `
                <div class="ai-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-bubble">${formattedMessage}</div>
            `;
        }

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function addTypingIndicator() {
        const messagesContainer = modal.querySelector('#ai-chat-messages');
        if (!messagesContainer) return;

        const typingDiv = document.createElement('div');
        typingDiv.className = 'ai-message typing-indicator-message';
        typingDiv.innerHTML = `
            <div class="ai-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="typing-indicator">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;

        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function removeTypingIndicator() {
        const typingIndicator = modal.querySelector('.typing-indicator-message');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
});
