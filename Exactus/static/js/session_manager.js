/**
 * Simple Session Manager - JavaScript Only
 * No Django middleware required
 */

class SimpleSessionManager {
    constructor() {
        this.config = {
            timeout: 300,      // 5 minutes
            warning: 60,       // 1 minute warning
            heartbeat: 30000,  // 30 seconds
            checkInterval: 1000 // 1 second
        };
        
        this.lastActivity = Date.now();
        this.warningShown = false;
        this.intervals = {};
        
        this.init();
    }
    
    init() {
        console.log('Simple Session Manager: Initialized');
        
        // Only run if user is authenticated
        if (!this.isAuthenticated()) {
            return;
        }
        
        this.setupActivityTracking();
        this.startIdleChecker();
        this.startHeartbeat();
        this.setupTabCloseDetection();
    }
    
    isAuthenticated() {
        // Check Django's authentication cookie or data attribute
        const body = document.body;
        return body && body.getAttribute('data-user-authenticated') === 'true';
    }
    
    setupActivityTracking() {
        const events = ['mousemove', 'click', 'keydown', 'scroll', 'touchstart'];
        const reset = () => {
            this.lastActivity = Date.now();
            if (this.warningShown) {
                this.hideWarning();
            }
        };
        
        events.forEach(event => {
            document.addEventListener(event, reset);
        });
    }
    
    startIdleChecker() {
        this.intervals.idle = setInterval(() => {
            const idleSeconds = (Date.now() - this.lastActivity) / 1000;
            
            // Show warning at 4 minutes
            if (idleSeconds >= 240 && idleSeconds < 300 && !this.warningShown) {
                this.showWarning();
            }
            
            // Logout at 5 minutes
            if (idleSeconds >= 300) {
                this.forceLogout();
            }
        }, this.config.checkInterval);
    }
    
    showWarning() {
        if (this.warningShown) return;
        this.warningShown = true;
        
        // Create simple warning (no Bootstrap modal)
        const warning = document.createElement('div');
        warning.id = 'sessionWarning';
        warning.innerHTML = `
            <div style="
                position: fixed;
                top: 20px;
                right: 20px;
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 5px;
                padding: 15px;
                z-index: 9999;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                min-width: 300px;
            ">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <span style="
                        background: #ffc107;
                        color: #000;
                        width: 24px;
                        height: 24px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin-right: 10px;
                        font-weight: bold;
                    ">!</span>
                    <strong style="flex-grow: 1;">Session About to Expire</strong>
                    <button id="closeWarning" style="
                        background: none;
                        border: none;
                        font-size: 20px;
                        cursor: pointer;
                    ">&times;</button>
                </div>
                <p style="margin: 0 0 10px 0;">
                    Your session will expire in <span id="countdown" style="font-weight: bold;">60</span> seconds.
                </p>
                <div style="display: flex; gap: 10px;">
                    <button id="extendSession" style="
                        background: #0d6efd;
                        color: white;
                        border: none;
                        padding: 8px 15px;
                        border-radius: 4px;
                        cursor: pointer;
                        flex-grow: 1;
                    ">Stay Signed In</button>
                    <button id="logoutNow" style="
                        background: #6c757d;
                        color: white;
                        border: none;
                        padding: 8px 15px;
                        border-radius: 4px;
                        cursor: pointer;
                    ">Log Out</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(warning);
        
        // Add event listeners
        document.getElementById('extendSession').addEventListener('click', () => this.extendSession());
        document.getElementById('logoutNow').addEventListener('click', () => this.logoutNow());
        document.getElementById('closeWarning').addEventListener('click', () => this.hideWarning());
        
        // Start countdown
        this.startCountdown();
    }
    
    startCountdown() {
        let timeLeft = 60;
        this.intervals.countdown = setInterval(() => {
            timeLeft--;
            const countdownEl = document.getElementById('countdown');
            if (countdownEl) {
                countdownEl.textContent = timeLeft;
                
                // Change color when time is low
                if (timeLeft <= 10) {
                    countdownEl.style.color = '#dc3545';
                }
            }
            
            if (timeLeft <= 0) {
                this.forceLogout();
            }
        }, 1000);
    }
    
    hideWarning() {
        this.warningShown = false;
        const warning = document.getElementById('sessionWarning');
        if (warning) {
            warning.remove();
        }
        if (this.intervals.countdown) {
            clearInterval(this.intervals.countdown);
        }
    }
    
    extendSession() {
        // Send heartbeat
        fetch(window.location.href, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).catch(() => {
            // Ignore errors
        });
        
        // Reset activity
        this.lastActivity = Date.now();
        this.hideWarning();
        
        // Show brief confirmation
        this.showNotification('Session extended');
    }
    
    logoutNow() {
        window.location.href = '/logout/';
    }
    
    forceLogout() {
        // Try to logout via POST
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/logout/';
        
        const csrf = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrf) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'csrfmiddlewaretoken';
            input.value = csrf.value;
            form.appendChild(input);
        }
        
        document.body.appendChild(form);
        form.submit();
    }
    
    startHeartbeat() {
        // Simple heartbeat - just refresh session cookie
        this.intervals.heartbeat = setInterval(() => {
            // Make a lightweight request to keep session alive
            fetch('/?heartbeat=1', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                cache: 'no-cache'
            }).catch(() => {
                // Ignore errors
            });
        }, this.config.heartbeat);
    }
    




    
    setupTabCloseDetection() {
        window.addEventListener('beforeunload', () => {
            if (navigator.sendBeacon) {
                navigator.sendBeacon('/?tab_closed=1');
            }
        });
    }
    
    showNotification(message) {
        const notification = document.createElement('div');
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #198754;
            color: white;
            padding: 10px 15px;
            border-radius: 4px;
            z-index: 9998;
        `;
        
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }
    
    cleanup() {
        Object.values(this.intervals).forEach(clearInterval);
        this.hideWarning();
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.sessionManager = new SimpleSessionManager();
});