// Mormon Express - Scripture Conversations
// Main JavaScript Application

(function() {
    'use strict';

    // State Management
    const state = {
        currentCharacter: null,
        characters: {},
        conversationHistory: [],
        isAuthenticated: false,
        user: null,
        scriptureMode: false,
        scriptureSource: 'all',
        isLoading: false
    };

    // DOM Elements
    const elements = {
        // Chat
        chatMessages: document.getElementById('chat-messages'),
        messageInput: document.getElementById('message-input'),
        sendBtn: document.getElementById('send-btn'),
        typingIndicator: document.getElementById('typing-indicator'),

        // Header
        characterName: document.getElementById('character-name'),
        characterTitle: document.getElementById('character-title'),
        avatarImg: document.getElementById('avatar-img'),
        currentAvatar: document.getElementById('current-avatar'),

        // Buttons
        settingsBtn: document.getElementById('settings-btn'),
        charactersBtn: document.getElementById('characters-btn'),
        historyBtn: document.getElementById('history-btn'),
        donateBtn: document.getElementById('donate-btn'),

        // Modals
        authModal: document.getElementById('auth-modal'),
        settingsModal: document.getElementById('settings-modal'),
        characterModal: document.getElementById('character-modal'),
        historyModal: document.getElementById('history-modal'),
        recommendationModal: document.getElementById('recommendation-modal'),

        // Auth
        loginForm: document.getElementById('login-form'),
        registerForm: document.getElementById('register-form'),
        loginError: document.getElementById('login-error'),
        registerError: document.getElementById('register-error'),
        continueGuest: document.getElementById('continue-guest'),
        authTabs: document.querySelectorAll('.auth-tab'),

        // Settings
        scriptureModeToggle: document.getElementById('scripture-mode-toggle'),
        scriptureSource: document.getElementById('scripture-source'),
        scriptureSourceSection: document.getElementById('scripture-source-section'),
        logoutBtn: document.getElementById('logout-btn'),
        showAuthBtn: document.getElementById('show-auth-btn'),
        accountInfo: document.getElementById('account-info'),
        userStats: document.getElementById('user-stats'),

        // Characters
        charactersGrid: document.getElementById('characters-grid'),
        sectionTabs: document.querySelectorAll('.section-tab'),

        // History
        conversationsList: document.getElementById('conversations-list'),

        // Recommendation
        recCharacterName: document.getElementById('rec-character-name'),
        recBtnName: document.getElementById('rec-btn-name'),
        recommendationReason: document.getElementById('recommendation-reason'),
        acceptRecommendation: document.getElementById('accept-recommendation'),
        declineRecommendation: document.getElementById('decline-recommendation'),

        // Close buttons
        closeSettings: document.getElementById('close-settings'),
        closeCharacters: document.getElementById('close-characters'),
        closeHistory: document.getElementById('close-history')
    };

    // API Helpers
    async function api(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : endpoint;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            credentials: 'include',
            ...options
        };

        if (options.body && typeof options.body === 'object') {
            config.body = JSON.stringify(options.body);
        }

        const response = await fetch(url, config);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'API request failed');
        }

        return data;
    }

    // Character Functions
    async function loadCharacters() {
        try {
            const sections = await api('/api/chatbot/characters');
            state.characters = {};

            for (const [sectionId, section] of Object.entries(sections)) {
                for (const char of section.characters) {
                    state.characters[char.id] = {
                        ...char,
                        section: sectionId,
                        sectionName: section.name
                    };
                }
            }

            renderCharacters('book_of_mormon');

            // Set initial character
            if (!state.currentCharacter) {
                await selectCharacter('nephi');
            }
        } catch (error) {
            console.error('Failed to load characters:', error);
        }
    }

    function renderCharacters(section) {
        const grid = elements.charactersGrid;
        grid.innerHTML = '';

        const sectionCharacters = Object.values(state.characters).filter(c => c.section === section);

        sectionCharacters.forEach(char => {
            const card = document.createElement('div');
            card.className = `character-card ${state.currentCharacter?.id === char.id ? 'active' : ''}`;
            card.innerHTML = `
                <img src="/images/${char.id}.svg" alt="${char.name}" onerror="this.src='/images/default-avatar.svg'">
                <h4>${char.name}</h4>
                <p>${char.title}</p>
            `;
            card.addEventListener('click', () => {
                selectCharacter(char.id);
                closeModal(elements.characterModal);
            });
            grid.appendChild(card);
        });
    }

    async function selectCharacter(characterId) {
        try {
            const charInfo = await api(`/api/chatbot/character/${characterId}`);
            state.currentCharacter = charInfo;

            // Update header
            elements.characterName.textContent = charInfo.name;
            elements.characterTitle.textContent = charInfo.title;
            elements.avatarImg.src = `/images/${characterId}.svg`;
            elements.avatarImg.onerror = () => { elements.avatarImg.src = '/images/default-avatar.svg'; };

            // Update avatar border color based on section
            const colors = {
                'book_of_mormon': 'var(--bom-color)',
                'old_testament': 'var(--ot-color)',
                'new_testament': 'var(--nt-color)'
            };
            elements.currentAvatar.style.borderColor = colors[charInfo.section] || 'var(--primary-color)';

            // Load conversation history if authenticated
            if (state.isAuthenticated) {
                await loadConversation(characterId);
            } else {
                // Clear and show initial message
                state.conversationHistory = [];
                elements.chatMessages.innerHTML = '';
                addMessage(charInfo.initial_message, 'character');
            }

            // Update character cards if modal is open
            document.querySelectorAll('.character-card').forEach(card => {
                card.classList.remove('active');
            });

        } catch (error) {
            console.error('Failed to select character:', error);
        }
    }

    async function loadConversation(characterId) {
        try {
            const data = await api(`/api/user/conversation/${characterId}`);
            state.conversationHistory = data.messages || [];

            elements.chatMessages.innerHTML = '';

            if (state.conversationHistory.length === 0) {
                // Show initial message
                addMessage(data.initial_message, 'character');
            } else {
                // Render existing messages
                state.conversationHistory.forEach(msg => {
                    addMessage(msg.content, msg.sender === 'user' ? 'user' : 'character', false);
                });
            }

            scrollToBottom();
        } catch (error) {
            console.error('Failed to load conversation:', error);
            // Show initial message as fallback
            elements.chatMessages.innerHTML = '';
            if (state.currentCharacter) {
                addMessage(state.currentCharacter.initial_message, 'character');
            }
        }
    }

    // Chat Functions
    async function sendMessage() {
        const message = elements.messageInput.value.trim();
        if (!message || state.isLoading) return;

        state.isLoading = true;
        elements.sendBtn.disabled = true;
        elements.messageInput.value = '';
        autoResizeTextarea();

        // Add user message
        addMessage(message, 'user');
        state.conversationHistory.push({ sender: 'user', content: message });

        // Show typing indicator
        elements.typingIndicator.classList.remove('hidden');
        scrollToBottom();

        try {
            const response = await api('/api/chatbot/chat', {
                method: 'POST',
                body: {
                    message: message,
                    character_id: state.currentCharacter.id,
                    scripture_mode: state.scriptureMode,
                    scripture_source: state.scriptureSource,
                    conversation_history: state.conversationHistory.slice(-20)
                }
            });

            // Hide typing indicator
            elements.typingIndicator.classList.add('hidden');

            // Add response
            addMessage(response.response, 'character');
            state.conversationHistory.push({ sender: 'character', content: response.response });

        } catch (error) {
            elements.typingIndicator.classList.add('hidden');
            console.error('Chat error:', error);
            addMessage("I'm having trouble connecting right now. Please try again in a moment.", 'character');
        }

        state.isLoading = false;
        elements.sendBtn.disabled = false;
        elements.messageInput.focus();
    }

    function addMessage(content, sender, animate = true) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        if (sender === 'character' && state.currentCharacter) {
            messageDiv.innerHTML = `
                <div class="message-avatar">
                    <img src="/images/${state.currentCharacter.id}.svg" alt="${state.currentCharacter.name}" onerror="this.src='/images/default-avatar.svg'">
                </div>
                <div class="message-content">
                    ${formatMessageContent(content)}
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-content">
                    ${formatMessageContent(content)}
                </div>
            `;
        }

        if (!animate) {
            messageDiv.style.animation = 'none';
        }

        elements.chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    function formatMessageContent(content) {
        // Convert line breaks to paragraphs
        const paragraphs = content.split('\n\n').filter(p => p.trim());
        let html = paragraphs.map(p => `<p>${escapeHtml(p).replace(/\n/g, '<br>')}</p>`).join('');

        // Highlight scripture references
        html = html.replace(
            /"([^"]+)"\s*-\s*([A-Za-z0-9\s]+\d+:\d+(?:-\d+)?(?:\s*\([^)]+\))?)/g,
            '<div class="scripture-reference">"$1" - $2</div>'
        );

        return html;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function scrollToBottom() {
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    }

    function autoResizeTextarea() {
        const textarea = elements.messageInput;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
    }

    // Authentication Functions
    async function checkAuth() {
        try {
            const data = await api('/api/auth/check-auth');
            state.isAuthenticated = data.authenticated;
            state.user = data.user;

            updateAuthUI();

            if (data.authenticated && data.is_new_day && data.recommendation) {
                showRecommendation(data.recommendation);
            } else if (!data.authenticated) {
                openModal(elements.authModal);
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            openModal(elements.authModal);
        }
    }

    async function login(identifier, password) {
        try {
            const data = await api('/api/auth/login', {
                method: 'POST',
                body: { username: identifier, password }
            });

            state.isAuthenticated = true;
            state.user = data.user;
            updateAuthUI();
            closeModal(elements.authModal);

            if (data.is_new_day && data.recommendation) {
                showRecommendation(data.recommendation);
            }

            // Reload conversation with saved history
            if (state.currentCharacter) {
                await loadConversation(state.currentCharacter.id);
            }

            return true;
        } catch (error) {
            throw error;
        }
    }

    async function register(username, email, password) {
        try {
            const data = await api('/api/auth/register', {
                method: 'POST',
                body: { username, email, password }
            });

            state.isAuthenticated = true;
            state.user = data.user;
            updateAuthUI();
            closeModal(elements.authModal);

            return true;
        } catch (error) {
            throw error;
        }
    }

    async function logout() {
        try {
            await api('/api/auth/logout', { method: 'POST' });
            state.isAuthenticated = false;
            state.user = null;
            state.conversationHistory = [];
            updateAuthUI();

            // Reset to initial message
            if (state.currentCharacter) {
                elements.chatMessages.innerHTML = '';
                addMessage(state.currentCharacter.initial_message, 'character');
            }
        } catch (error) {
            console.error('Logout failed:', error);
        }
    }

    function updateAuthUI() {
        if (state.isAuthenticated && state.user) {
            elements.accountInfo.innerHTML = `
                <p>Signed in as <strong>${state.user.username}</strong></p>
                <p style="font-size: 0.85rem; color: var(--text-secondary)">${state.user.email}</p>
            `;
            elements.logoutBtn.style.display = 'block';
            elements.showAuthBtn.style.display = 'none';
            loadUserStats();
        } else {
            elements.accountInfo.innerHTML = '<p>Sign in to save your conversations</p>';
            elements.logoutBtn.style.display = 'none';
            elements.showAuthBtn.style.display = 'block';
            elements.userStats.innerHTML = '<p>Sign in to track your conversations and get personalized recommendations.</p>';
        }
    }

    async function loadUserStats() {
        if (!state.isAuthenticated) return;

        try {
            const stats = await api('/api/user/stats');
            elements.userStats.innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">Total Messages</span>
                    <span class="stat-value">${stats.total_messages}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Characters Met</span>
                    <span class="stat-value">${stats.characters_talked_to}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Book of Mormon</span>
                    <span class="stat-value">${stats.section_breakdown.book_of_mormon || 0} msgs</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Old Testament</span>
                    <span class="stat-value">${stats.section_breakdown.old_testament || 0} msgs</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">New Testament</span>
                    <span class="stat-value">${stats.section_breakdown.new_testament || 0} msgs</span>
                </div>
            `;
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    // Recommendation Functions
    function showRecommendation(recommendation) {
        const char = state.characters[recommendation.character];
        if (!char) return;

        elements.recCharacterName.textContent = char.name;
        elements.recBtnName.textContent = char.name;
        elements.recommendationReason.textContent = recommendation.reason;

        openModal(elements.recommendationModal);
    }

    async function acceptRecommendation() {
        const charName = elements.recCharacterName.textContent;
        const char = Object.values(state.characters).find(c => c.name === charName);

        if (char) {
            closeModal(elements.recommendationModal);
            await selectCharacter(char.id);

            // Mark recommendation as followed
            try {
                await api('/api/user/recommendation/follow', { method: 'POST' });
            } catch (e) {
                // Silent fail
            }
        }
    }

    // Conversation History Functions
    async function loadConversationHistory() {
        if (!state.isAuthenticated) {
            elements.conversationsList.innerHTML = '<p class="no-conversations">Sign in to save and access your conversation history.</p>';
            return;
        }

        try {
            const data = await api('/api/user/conversations');
            const conversations = data.conversations;

            if (conversations.length === 0) {
                elements.conversationsList.innerHTML = '<p class="no-conversations">No conversations yet. Start chatting to save your history!</p>';
                return;
            }

            elements.conversationsList.innerHTML = conversations.map(conv => `
                <div class="conversation-item" data-character="${conv.character_id}">
                    <img src="/images/${conv.character_id}.svg" alt="${conv.character_name}" onerror="this.src='/images/default-avatar.svg'">
                    <div class="conversation-info">
                        <h4>${conv.character_name}</h4>
                        <p>${conv.character_title}</p>
                    </div>
                    <div class="conversation-meta">
                        <div>${conv.message_count} messages</div>
                        <div>${formatDate(conv.updated_at)}</div>
                    </div>
                </div>
            `).join('');

            // Add click handlers
            elements.conversationsList.querySelectorAll('.conversation-item').forEach(item => {
                item.addEventListener('click', () => {
                    const charId = item.dataset.character;
                    selectCharacter(charId);
                    closeModal(elements.historyModal);
                });
            });

        } catch (error) {
            console.error('Failed to load history:', error);
            elements.conversationsList.innerHTML = '<p class="no-conversations">Failed to load conversations.</p>';
        }
    }

    function formatDate(isoString) {
        if (!isoString) return '';
        const date = new Date(isoString);
        const now = new Date();
        const diff = now - date;

        if (diff < 86400000) { // Less than 1 day
            return 'Today';
        } else if (diff < 172800000) { // Less than 2 days
            return 'Yesterday';
        } else {
            return date.toLocaleDateString();
        }
    }

    // Modal Functions
    function openModal(modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeModal(modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }

    function closeAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('active');
        });
        document.body.style.overflow = '';
    }

    // Settings Functions
    function loadSettings() {
        // Load from localStorage
        state.scriptureMode = localStorage.getItem('scriptureMode') === 'true';
        state.scriptureSource = localStorage.getItem('scriptureSource') || 'all';

        elements.scriptureModeToggle.checked = state.scriptureMode;
        elements.scriptureSource.value = state.scriptureSource;
        elements.scriptureSourceSection.style.display = state.scriptureMode ? 'block' : 'none';
    }

    function saveSettings() {
        localStorage.setItem('scriptureMode', state.scriptureMode);
        localStorage.setItem('scriptureSource', state.scriptureSource);
    }

    // Event Listeners
    function setupEventListeners() {
        // Send message
        elements.sendBtn.addEventListener('click', sendMessage);
        elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        elements.messageInput.addEventListener('input', autoResizeTextarea);

        // Header buttons
        elements.settingsBtn.addEventListener('click', () => openModal(elements.settingsModal));
        elements.charactersBtn.addEventListener('click', () => openModal(elements.characterModal));
        elements.currentAvatar.addEventListener('click', () => openModal(elements.characterModal));
        elements.historyBtn.addEventListener('click', () => {
            loadConversationHistory();
            openModal(elements.historyModal);
        });
        elements.donateBtn.addEventListener('click', () => {
            window.open('https://www.gofundme.com/f/support-buzly-privacyfirst-community-platform', '_blank');
        });

        // Close modals
        elements.closeSettings.addEventListener('click', () => closeModal(elements.settingsModal));
        elements.closeCharacters.addEventListener('click', () => closeModal(elements.characterModal));
        elements.closeHistory.addEventListener('click', () => closeModal(elements.historyModal));

        // Close modal on background click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    closeModal(modal);
                }
            });
        });

        // Auth tabs
        elements.authTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                elements.authTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');

                if (tab.dataset.tab === 'login') {
                    elements.loginForm.classList.remove('hidden');
                    elements.registerForm.classList.add('hidden');
                } else {
                    elements.loginForm.classList.add('hidden');
                    elements.registerForm.classList.remove('hidden');
                }
            });
        });

        // Login form
        elements.loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            elements.loginError.textContent = '';

            const identifier = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;

            try {
                await login(identifier, password);
            } catch (error) {
                elements.loginError.textContent = error.message;
            }
        });

        // Register form
        elements.registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            elements.registerError.textContent = '';

            const username = document.getElementById('register-username').value;
            const email = document.getElementById('register-email').value;
            const password = document.getElementById('register-password').value;

            try {
                await register(username, email, password);
            } catch (error) {
                elements.registerError.textContent = error.message;
            }
        });

        // Continue as guest
        elements.continueGuest.addEventListener('click', () => {
            closeModal(elements.authModal);
        });

        // Settings
        elements.scriptureModeToggle.addEventListener('change', () => {
            state.scriptureMode = elements.scriptureModeToggle.checked;
            elements.scriptureSourceSection.style.display = state.scriptureMode ? 'block' : 'none';
            saveSettings();
        });

        elements.scriptureSource.addEventListener('change', () => {
            state.scriptureSource = elements.scriptureSource.value;
            saveSettings();
        });

        elements.logoutBtn.addEventListener('click', logout);
        elements.showAuthBtn.addEventListener('click', () => {
            closeModal(elements.settingsModal);
            openModal(elements.authModal);
        });

        // Section tabs
        elements.sectionTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                elements.sectionTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                renderCharacters(tab.dataset.section);
            });
        });

        // Recommendation modal
        elements.acceptRecommendation.addEventListener('click', acceptRecommendation);
        elements.declineRecommendation.addEventListener('click', () => {
            closeModal(elements.recommendationModal);
            openModal(elements.characterModal);
        });

        // Escape key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeAllModals();
            }
        });
    }

    // Initialize
    async function init() {
        loadSettings();
        setupEventListeners();
        await loadCharacters();
        await checkAuth();
    }

    // Start the app
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
