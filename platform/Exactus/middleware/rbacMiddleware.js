// middleware/rbacMiddleware.js
const axios = require('axios');
const Redis = require('ioredis');
const logger = require('../utils/logger');

class RBACMiddleware {
    constructor() {
        this.redis = new Redis({
            host: process.env.REDIS_HOST,
            port: process.env.REDIS_PORT,
            password: process.env.REDIS_PASSWORD,
            db: process.env.REDIS_PERMISSION_DB
        });
        
        this.cachePrefix = 'exactuspay:permissions:v2';
        this.djangoBaseURL = process.env.DJANGO_API_URL;
        
        // Permission cache with TTL
        this.localCache = new Map();
        this.cacheTTL = 5 * 60 * 1000; // 5 minutes
    }

    /**
     * Middleware to require specific permission
     */
    requirePermission(domain, action) {
        return async (req, res, next) => {
            try {
                if (!req.user || !req.user.role) {
                    return res.status(401).json({
                        error: 'Unauthorized',
                        detail: 'User role not found'
                    });
                }

                const hasPermission = await this.checkPermission(
                    req.user.role, 
                    domain, 
                    action
                );

                if (!hasPermission) {
                    // Log permission denial for security audit
                    await this.logPermissionDenial(
                        req.user, 
                        domain, 
                        action,
                        req.ip
                    );

                    return res.status(403).json({
                        error: 'Forbidden',
                        detail: `${req.user.role} lacks ${domain}.${action} permission`,
                        code: 'PERMISSION_DENIED'
                    });
                }

                // Permission granted - proceed
                next();
            } catch (error) {
                logger.error('RBAC middleware error:', error);
                return res.status(500).json({
                    error: 'Permission check failed',
                    detail: 'Internal server error'
                });
            }
        };
    }

    /**
     * Check if role has specific permission
     */
    async checkPermission(role, domain, action) {
        try {
            // 1. Check local memory cache first
            const cacheKey = `${role}:${domain}:${action}`;
            const cached = this.localCache.get(cacheKey);
            
            if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
                return cached.result;
            }

            // 2. Check Redis distributed cache
            const redisKey = `${this.cachePrefix}:role:${role}`;
            const redisCached = await this.redis.get(redisKey);
            
            if (redisCached) {
                const permissions = JSON.parse(redisCached);
                const hasPerm = permissions.domains?.[domain]?.[action] || false;
                
                // Update local cache
                this.localCache.set(cacheKey, {
                    result: hasPerm,
                    timestamp: Date.now()
                });
                
                return hasPerm;
            }

            // 3. Fall back to Django API
            const hasPerm = await this.fetchFromDjangoAPI(role, domain, action);
            
            // Cache the result
            this.localCache.set(cacheKey, {
                result: hasPerm,
                timestamp: Date.now()
            });

            return hasPerm;
        } catch (error) {
            logger.error(`Permission check failed for ${role}.${domain}.${action}:`, error);
            
            // In case of failure, default to deny for security
            return false;
        }
    }

    /**
     * Fetch permission from Django API
     */
    async fetchFromDjangoAPI(role, domain, action) {
        try {
            const response = await axios.post(
                `${this.djangoBaseURL}/api/permissions/validate/`,
                { role, domain, action },
                {
                    headers: {
                        'Authorization': `Bearer ${process.env.DJANGO_API_TOKEN}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: 5000 // 5 second timeout
                }
            );

            return response.data.has_permission;
        } catch (error) {
            if (error.response) {
                // Django API returned an error
                logger.error(`Django API error: ${error.response.status}`, error.response.data);
            } else {
                logger.error('Django API request failed:', error.message);
            }
            throw error;
        }
    }

    /**
     * Get all effective permissions for a role (for frontend)
     */
    async getRolePermissions(role) {
        try {
            // Try Redis cache first
            const redisKey = `${this.cachePrefix}:role:${role}`;
            const redisCached = await this.redis.get(redisKey);
            
            if (redisCached) {
                return JSON.parse(redisCached);
            }

            // Fetch from Django API
            const response = await axios.get(
                `${this.djangoBaseURL}/api/permissions/effective/${role}/`,
                {
                    headers: {
                        'Authorization': `Bearer ${process.env.DJANGO_API_TOKEN}`
                    },
                    timeout: 5000
                }
            );

            // Cache in Redis for future use
            await this.redis.setex(
                redisKey,
                300, // 5 minutes TTL
                JSON.stringify(response.data)
            );

            return response.data;
        } catch (error) {
            logger.error(`Failed to get permissions for role ${role}:`, error);
            throw error;
        }
    }

    /**
     * Log permission denial for security audit
     */
    async logPermissionDenial(user, domain, action, ipAddress) {
        try {
            await axios.post(
                `${this.djangoBaseURL}/api/audit/log-permission-denial/`,
                {
                    user_id: user.id,
                    username: user.username,
                    role: user.role,
                    domain,
                    action,
                    ip_address: ipAddress,
                    timestamp: new Date().toISOString(),
                    user_agent: 'NodeJS-API'
                },
                {
                    headers: {
                        'Authorization': `Bearer ${process.env.DJANGO_API_TOKEN}`
                    }
                }
            );
        } catch (error) {
            // Don't throw error if audit logging fails
            logger.error('Failed to log permission denial:', error);
        }
    }

    /**
     * Invalidate cache for a specific role
     */
    async invalidateRoleCache(role) {
        const redisKey = `${this.cachePrefix}:role:${role}`;
        await this.redis.del(redisKey);
        
        // Clear local cache entries for this role
        for (const [key] of this.localCache.entries()) {
            if (key.startsWith(`${role}:`)) {
                this.localCache.delete(key);
            }
        }
        
        logger.info(`Invalidated RBAC cache for role: ${role}`);
    }
}

// Singleton instance
const rbacMiddleware = new RBACMiddleware();
module.exports = rbacMiddleware;