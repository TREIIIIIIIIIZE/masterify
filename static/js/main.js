/**
 * Main JavaScript for Masterify
 * Handles user interactions, authentication, and general UI functionality
 */

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

const SUPABASE_URL = 'https://movnntymctxclliyehne.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vdm5udHltY3R4Y2xsaXllaG5lIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY2NDE3NTcsImV4cCI6MjA2MjIxNzc1N30.oby1BVjFUJxAUNl1MYTl2HihnT0ZeRc_YZ1B0WmyEYU'; // Remplace par ta clé publique Supabase (pas la service_role)
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let currentUser = null;
    
    // DOM elements
    const loginButton = document.getElementById('login-button');
    const signupButton = document.getElementById('signup-button');
    const logoutButton = document.getElementById('logout-button');
    const userMenu = document.getElementById('user-menu');
    const authButtons = document.getElementById('auth-buttons');
    const creditsDisplay = document.getElementById('credits-display');
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    // Mobile menu toggle
    if (mobileMenuButton) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }
    
    // Add click event listener to document to close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        if (mobileMenu && !mobileMenu.classList.contains('hidden') && 
            !mobileMenuButton.contains(event.target) && 
            !mobileMenu.contains(event.target)) {
            mobileMenu.classList.add('hidden');
        }
    });
    
    // Authentication functions
    async function checkAuthStatus() {
        try {
            const response = await axios.get('/auth/user');
            if (response.data.success) {
                currentUser = response.data.user;
                updateAuthUI(currentUser);
                return currentUser;
            } else {
                updateAuthUI(null);
                return null;
            }
        } catch (error) {
            console.log('Not logged in');
            updateAuthUI(null);
            return null;
        }
    }
    
    function updateAuthUI(user) {
        if (user) {
            if (authButtons) authButtons.classList.add('hidden');
            if (userMenu) {
                userMenu.classList.remove('hidden');
                userMenu.classList.add('flex');
            }
            if (creditsDisplay) {
                creditsDisplay.textContent = `${user.credits} credit${user.credits !== 1 ? 's' : ''}`;
            }
            
            // Update any user-specific elements
            const userNameElements = document.querySelectorAll('.user-name');
            userNameElements.forEach(el => {
                el.textContent = user.username;
            });
            
            const creditElements = document.querySelectorAll('.user-credits');
            creditElements.forEach(el => {
                el.textContent = user.credits;
            });
        } else {
            if (authButtons) authButtons.classList.remove('hidden');
            if (userMenu) {
                userMenu.classList.add('hidden');
                userMenu.classList.remove('flex');
            }
        }
    }
    
    // Handle login form submission
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const loginModal = document.getElementById('login-modal');
            const loginError = document.getElementById('login-error');
            
            const formData = new FormData(loginForm);
            const data = {
                email: formData.get('email'),
                password: formData.get('password')
            };
            
            try {
                const response = await axios.post('/auth/login', data);
                if (response.data.success) {
                    loginModal.classList.add('hidden');
                    currentUser = response.data.user;
                    updateAuthUI(currentUser);
                    
                    // Refresh the page to update UI components
                    window.location.reload();
                }
            } catch (error) {
                loginError.textContent = error.response?.data?.message || 'Login failed';
                loginError.classList.remove('hidden');
            }
        });
    }
    
    // Handle signup form submission
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const signupModal = document.getElementById('signup-modal');
            const signupError = document.getElementById('signup-error');
            
            const formData = new FormData(signupForm);
            const data = {
                username: formData.get('username'),
                email: formData.get('email'),
                password: formData.get('password')
            };
            
            try {
                const response = await axios.post('/auth/register', data);
                if (response.data.success) {
                    signupModal.classList.add('hidden');
                    currentUser = response.data.user;
                    updateAuthUI(currentUser);
                    
                    // Refresh the page to update UI components
                    window.location.reload();
                }
            } catch (error) {
                signupError.textContent = error.response?.data?.message || 'Signup failed';
                signupError.classList.remove('hidden');
            }
        });
    }
    
    // Handle logout button click
    if (logoutButton) {
        logoutButton.addEventListener('click', async () => {
            try {
                const response = await axios.get('/auth/logout');
                if (response.data.success) {
                    currentUser = null;
                    updateAuthUI(null);
                    
                    // Redirect to home page
                    window.location.href = '/';
                }
            } catch (error) {
                console.error('Logout failed', error);
            }
        });
    }
    
    // Modal functionality
    const loginModal = document.getElementById('login-modal');
    const signupModal = document.getElementById('signup-modal');
    const cancelButtons = document.querySelectorAll('.cancel-btn');
    
    if (loginButton) {
        loginButton.addEventListener('click', () => {
            if (loginModal) loginModal.classList.remove('hidden');
        });
    }
    
    if (signupButton) {
        signupButton.addEventListener('click', () => {
            if (signupModal) signupModal.classList.remove('hidden');
        });
    }
    
    if (cancelButtons) {
        cancelButtons.forEach(button => {
            button.addEventListener('click', () => {
                if (loginModal) loginModal.classList.add('hidden');
                if (signupModal) signupModal.classList.add('hidden');
            });
        });
    }
    
    // Close modals when clicking outside
    window.addEventListener('click', (e) => {
        if (loginModal && e.target === loginModal) {
            loginModal.classList.add('hidden');
        }
        if (signupModal && e.target === signupModal) {
            signupModal.classList.add('hidden');
        }
    });
    
    // Animation on scroll
    function animateOnScroll() {
        const elements = document.querySelectorAll('.fade-in, .slide-up');
        
        elements.forEach(function(element) {
            const elementPosition = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            
            if (elementPosition < windowHeight - 100) {
                element.style.opacity = 1;
                element.style.transform = 'translateY(0)';
            }
        });
    }
    
    // Initialize animations
    if (document.querySelectorAll('.fade-in, .slide-up').length > 0) {
        // Initial check
        animateOnScroll();
        
        // Check on scroll
        window.addEventListener('scroll', animateOnScroll);
    }
    
    // Parallax effect initialization
    const parallaxElements = document.querySelectorAll('.parallax');
    if (parallaxElements.length > 0) {
        window.addEventListener('scroll', function() {
            parallaxElements.forEach(element => {
                let scrollPosition = window.pageYOffset;
                element.style.backgroundPositionY = scrollPosition * 0.5 + 'px';
            });
        });
    }
    
    // Parallax effect for background elements
    const parallaxBg = document.querySelector('.parallax-bg');
    const purpleGlows = document.querySelectorAll('.purple-glow');
    
    if (parallaxBg && purpleGlows.length > 0) {
        window.addEventListener('mousemove', function(e) {
            const x = e.clientX / window.innerWidth;
            const y = e.clientY / window.innerHeight;
            
            purpleGlows.forEach(glow => {
                const speed = 30;
                const xPos = (0.5 - x) * speed;
                const yPos = (0.5 - y) * speed;
                
                glow.style.transform = `translate(${xPos}px, ${yPos}px)`;
            });
        });
    }
    
    // Initialize auth check
    checkAuthStatus();
    
    // FAQ accordion functionality
    const accordionButtons = document.querySelectorAll('.accordion-button');
    
    accordionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const accordionItem = this.parentNode;
            
            // Toggle active class
            accordionItem.classList.toggle('active');
            
            // Close other accordion items
            const siblings = Array.from(accordionItem.parentNode.children).filter(item => item !== accordionItem);
            siblings.forEach(sibling => {
                sibling.classList.remove('active');
            });
        });
    });
    
    // Modal logic
    const authModal = document.getElementById('auth-modal');
    const openAuthBtn = document.getElementById('open-auth-modal');
    const closeAuthBtn = document.getElementById('close-auth-modal');
    const emailBtn = document.getElementById('login-email');
    const emailForm = document.getElementById('email-auth-form');
    const authError = document.getElementById('auth-error');

    openAuthBtn && openAuthBtn.addEventListener('click', () => {
        authModal.classList.remove('hidden');
        emailForm.classList.add('hidden');
        authError.classList.add('hidden');
    });
    closeAuthBtn && closeAuthBtn.addEventListener('click', () => {
        authModal.classList.add('hidden');
    });
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') authModal.classList.add('hidden');
    });

    document.getElementById('login-google')?.addEventListener('click', async () => {
        await supabase.auth.signInWithOAuth({ provider: 'google' });
    });
    document.getElementById('login-discord')?.addEventListener('click', async () => {
        await supabase.auth.signInWithOAuth({ provider: 'discord' });
    });
    document.getElementById('login-youtube')?.addEventListener('click', async () => {
        await supabase.auth.signInWithOAuth({ provider: 'google', options: { scopes: 'https://www.googleapis.com/auth/youtube.readonly' } });
    });
    emailBtn?.addEventListener('click', () => {
        emailForm.classList.toggle('hidden');
    });

    emailForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('auth-email').value;
        const password = document.getElementById('auth-password').value;
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) {
            authError.textContent = error.message;
            authError.classList.remove('hidden');
        } else {
            authError.classList.add('hidden');
            window.location.reload();
        }
    });
    
    // Expose some functions globally
    window.masterifyApp = {
        checkAuth: checkAuthStatus,
        updateUI: updateAuthUI,
        currentUser: () => currentUser
    };
});
