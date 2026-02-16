/**
 * ExactusPay Session Manager v2.0
 * Handles 5-minute idle timeout with 60-second warning.
 */

class SessionManager {
    constructor() {
        this.config = {
            timeout: 300,           // 5 minutes total
            warning: 60,            // Show warning 60 seconds before
            heartbeat: 30000,       // Send heartbeat every 30s
            checkInterval: 1000     // Check idle every second
        };
        
        this.state = {
            lastActivity: Date.now(),
            warningActive: false,
            countdown: null,
            modal: null,
            intervals: {}
        };
        
        this.init();
    }

    init() {
        this.createWarningModal();
        this.setupActivityTracking();
        this.setupEventListeners();
        this.startHeartbeat();
        this.startIdleChecker();
        
        console.log('Session Manager: Ready');
    }

    // ======================
    // MODAL & UI COMPONENTS
    // ======================

    createWarningModal() {
        const modalHTML = `
            <div id="sessionWarningModal" class="modal fade" tabindex="-1">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content border-warning">
                        <div class="modal-header bg-warning bg-opacity-10">
                            <h5 class="modal-title text-warning">
                                <i class="bi bi-exclamation-triangle me-2"></i>
                                Session About to Expire
                            </h5>
                        </div>
                        <div class="modal-body">
                            <p>
                                Your session will expire in 
                                <span id="countdownTimer" class="fw-bold text-danger">60</span> 
                                seconds due to inactivity.
                            </p>
                            <div class="progress" style="height: 6px;">
                                <div id="progressBar" class="progress-bar bg-warning" 
                                     style="width: 100%"></div>
                            </div>
                            <p class="small text-muted mt-2">
                                For security, you'll be logged out automatically.
                            </p>
                        </div>
                        <div class="modal-footer">
                            <button id="logoutBtn" class="btn btn-outline-secondary btn-sm">
                                Log Out Now
                            </button>
                            <button id="stayBtn" class="btn btn-primary btn-sm">
                                Stay Signed In
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add modal to DOM
        const container = document.createElement('div');
        container.innerHTML = modalHTML;
        document.body.appendChild(container);

        // Initialize Bootstrap modal
        const modalElement = document.getElementById('sessionWarningModal');
        this.state.modal = new bootstrap.Modal(modalElement);

        // Add button listeners
        document.getElementById('stayBtn').addEventListener('click', () => this.extendSession());
        document.getElementById('logoutBtn').addEventListener('click', () => this.logoutNow());

        // Reset state when modal hides
        modalElement.addEventListener('hidden.bs.modal', () => {
            this.state.warningActive = false;
            this.stopCountdown();
        });
    }

    showWarning() {
        if (this.state.warningActive) return;
        
        this.state.warningActive = true;
        this.state.timeRemaining = this.config.warning;
        
        // Show modal
        if (this.state.modal) {
            this.state.modal.show();
        }
        
        // Start countdown
        this.startCountdown();
    }

    hideWarning() {
        this.state.warningActive = false;
        this.stopCountdown();
        
        if (this.state.modal) {
            this.state.modal.hide();
        }
    }

    startCountdown() {
        if (this.state.countdown) return;
        
        this.state.countdown = setInterval(() => {
            this.state.timeRemaining--;
            
            // Update UI
            const timer = document.getElementById('countdownTimer');
            const progress = document.getElementById('progressBar');
            
            if (timer) timer.textContent = this.state.timeRemaining;
            
            if (progress) {
                const percent = (this.state.timeRemaining / this.config.warning) * 100;
                progress.style.width = `${percent}%`;
                
                // Change color when time is critical
                if (this.state.timeRemaining <= 10) {
                    progress.classList.remove('bg-warning');
                    progress.classList.add('bg-danger');
                }
            }
            
            // Time's up - logout
            if (this.state.timeRemaining <= 0) {
                this.forceLogout();
            }
        }, 1000);
    }

    stopCountdown() {
        if (this.state.countdown) {
            clearInterval(this.state.countdown);
            this.state.countdown = null;
        }
    }

    // ======================
    // ACTIVITY TRACKING
    // ======================

    setupActivityTracking() {
        const events = [
            'mousemove', 'click', 'keydown', 'scroll',
            'touchstart', 'touchmove', 'wheel'
        ];
        
        const resetActivity = () => {
            this.state.lastActivity = Date.now();
            if (this.state.warningActive) {
                this.hideWarning();
            }
        };
        
        events.forEach(event => {
            document.addEventListener(event, resetActivity, { passive: true });
        });
        
        // Also track form interactions
        document.addEventListener('input', resetActivity);
        document.addEventListener('change', resetActivity);
    }

    startIdleChecker() {
        this.state.intervals.idle = setInterval(() => {
            const idleTime = (Date.now() - this.state.lastActivity) / 1000;
            
            // Show warning at 4 minutes
            if (idleTime >= 240 && idleTime < 300 && !this.state.warningActive) {
                this.showWarning();
            }
            
            // Logout at 5 minutes
            if (idleTime >= 300) {
                this.forceLogout();
            }
        }, this.config.checkInterval);
    }

    // ======================
    // HEARTBEAT & NETWORK
    // ======================

    startHeartbeat() {
        const sendHeartbeat = () => {
            fetch('/ajax/heartbeat/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Cache-Control': 'no-cache'
                },
                credentials: 'include'
            }).catch(error => {
                // Network errors are okay - might be offline
                console.debug('Heartbeat failed (possibly offline):', error);
            });
        };
        
        // Send immediately, then every 30s
        sendHeartbeat();
        this.state.intervals.heartbeat = setInterval(sendHeartbeat, this.config.heartbeat);
    }

    // ======================
    // TAB & BROWSER EVENTS
    // ======================

    setupEventListeners() {
        // Tab visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                // Reset activity when tab becomes visible
                this.state.lastActivity = Date.now();
            }
        });
        
        // Tab close detection
        window.addEventListener('beforeunload', () => {
            if (navigator.sendBeacon) {
                const data = new FormData();
                data.append('tab_closed', 'true');
                navigator.sendBeacon('/ajax/tab-close/', data);
            }
        });
    }

    // ======================
    // ACTIONS
    // ======================

    async extendSession() {
        try {
            // Send heartbeat to reset server timer
            await fetch('/ajax/heartbeat/', {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                credentials: 'include'
            });
            
            // Reset local timer
            this.state.lastActivity = Date.now();
            this.hideWarning();
            
            // Show confirmation
            this.showToast('Session extended', 'success');
            
        } catch (error) {
            console.error('Failed to extend session:', error);
            this.showToast('Unable to extend session', 'danger');
        }
    }

    logoutNow() {
        window.location.href = '/logout/';
    }

    async forceLogout() {
        this.cleanup();
        
        try {
            await fetch('/logout/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken(),
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });
        } catch (error) {
            // Continue to redirect even if fetch fails
        }
        
        window.location.href = '/login/?session_expired=true';
    }

    getCsrfToken() {
        const cookie = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    }

    showToast(message, type = 'info') {
        // Create toast container if needed
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        
        // Create toast
        const toastId = 'toast-' + Date.now();
        const toastHTML = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', toastHTML);
        
        // Show and auto-remove
        const toastEl = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
        toast.show();
        
        toastEl.addEventListener('hidden.bs.toast', () => {
            toastEl.remove();
        });
    }

    // ======================
    // CLEANUP
    // ======================

    cleanup() {
        // Clear all intervals
        Object.values(this.state.intervals).forEach(clearInterval);
        this.state.intervals = {};
        
        // Stop countdown
        this.stopCountdown();
        
        // Hide modal
        if (this.state.modal && this.state.warningActive) {
            this.state.modal.hide();
        }
    }
}

// Initialize only for authenticated users
document.addEventListener('DOMContentLoaded', () => {
    const isAuthenticated = document.body.getAttribute('data-user-authenticated') === 'true';
    
    if (isAuthenticated) {
        window.sessionManager = new SessionManager();
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (window.sessionManager) {
                window.sessionManager.cleanup();
            }
        });
    }
});