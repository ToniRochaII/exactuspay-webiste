// frontend/src/utils/rbacHelpers.js
import { rbacApi } from './api';

class RBACHelpers {
    /**
     * Check if current user has permission
     */
    static async hasPermission(domain, action) {
        try {
            const user = this.getCurrentUser();
            if (!user || !user.role) return false;

            // Check cached permissions first
            const cached = this.getCachedPermission(user.role, domain, action);
            if (cached !== null) return cached;

            // Fetch from API
            const response = await rbacApi.validatePermission(
                user.role, 
                domain, 
                action
            );

            // Cache the result
            this.cachePermission(user.role, domain, action, response.has_permission);
            
            return response.has_permission;
        } catch (error) {
            console.error('Permission check failed:', error);
            return false; // Default to deny on error
        }
    }

    /**
     * Get all permissions for current user (for UI rendering)
     */
    static async getUserPermissions() {
        try {
            const user = this.getCurrentUser();
            if (!user || !user.role) return {};

            const cached = sessionStorage.getItem(`rbac_permissions_${user.role}`);
            if (cached) {
                return JSON.parse(cached);
            }

            const response = await rbacApi.getRolePermissions(user.role);
            
            // Cache for session
            sessionStorage.setItem(
                `rbac_permissions_${user.role}`, 
                JSON.stringify(response.domains)
            );

            return response.domains;
        } catch (error) {
            console.error('Failed to get user permissions:', error);
            return {};
        }
    }

    /**
     * Hide/show UI elements based on permissions
     */
    static async applyUIPermissions() {
        const permissions = await this.getUserPermissions();
        
        // Example: Hide create button if no CREATE permission
        const canCreatePayrun = permissions.PAYRUN?.CREATE;
        const createButton = document.getElementById('create-payrun-btn');
        if (createButton) {
            createButton.style.display = canCreatePayrun ? 'block' : 'none';
        }

        // Example: Disable delete buttons if no DELETE permission
        const canDelete = permissions.PAYRUN?.DELETE;
        document.querySelectorAll('.delete-btn').forEach(btn => {
            if (!canDelete) {
                btn.disabled = true;
                btn.title = 'Delete permission required';
            }
        });
    }

    /**
     * Role-based navigation renderer
     */
    static async renderNavigation() {
        const permissions = await this.getUserPermissions();
        const navContainer = document.getElementById('main-navigation');
        
        const navItems = [
            {
                id: 'payroll',
                label: 'Payroll',
                required: ['PAYRUN', 'READ'],
                icon: '💰'
            },
            {
                id: 'employees', 
                label: 'Employees',
                required: ['EMPLOYEE', 'READ'],
                icon: '👥'
            },
            {
                id: 'reports',
                label: 'Reports',
                required: ['PAYREGISTER', 'READ'],
                icon: '📊'
            },
            {
                id: 'admin',
                label: 'Admin',
                required: ['USER', 'READ'],
                icon: '⚙️'
            }
        ];

        const visibleNavItems = navItems.filter(item => {
            return item.required.every(([domain, action]) => 
                permissions[domain]?.[action]
            );
        });

        const navHTML = visibleNavItems.map(item => `
            <li class="nav-item">
                <a class="nav-link" href="/${item.id}" data-nav="${item.id}">
                    ${item.icon} ${item.label}
                </a>
            </li>
        `).join('');

        navContainer.innerHTML = navHTML;
    }

    // Helper methods
    static getCurrentUser() {
        // Implementation depends on your auth system
        return JSON.parse(localStorage.getItem('currentUser'));
    }

    static getCachedPermission(role, domain, action) {
        const key = `perm_${role}_${domain}_${action}`;
        const cached = sessionStorage.getItem(key);
        return cached ? JSON.parse(cached) : null;
    }

    static cachePermission(role, domain, action, value) {
        const key = `perm_${role}_${domain}_${action}`;
        sessionStorage.setItem(key, JSON.stringify(value));
    }
}

export default RBACHelpers;