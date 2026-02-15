// test/rbac.integration.test.js
const request = require('supertest');
const express = require('express');
const rbacMiddleware = require('../middleware/rbacMiddleware');
const Redis = require('ioredis-mock');

// Mock Redis
jest.mock('ioredis', () => require('ioredis-mock'));

describe('RBAC Integration Tests', () => {
    let app;
    let mockRedis;

    beforeEach(() => {
        app = express();
        app.use(express.json());
        
        // Mock user authentication middleware
        app.use((req, res, next) => {
            req.user = {
                id: 1,
                username: 'test_manager',
                role: 'MANAGER'
            };
            next();
        });

        mockRedis = new Redis();
        rbacMiddleware.redis = mockRedis;
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    test('should allow access when permission exists', async () => {
        // Mock Redis to return permissions
        const mockPermissions = {
            domains: {
                PAYRUN: {
                    READ: true,
                    CREATE: true,
                    UPDATE: false,
                    DELETE: false
                }
            }
        };

        await mockRedis.set(
            'exactuspay:permissions:v2:role:MANAGER',
            JSON.stringify(mockPermissions)
        );

        app.get(
            '/api/payruns',
            rbacMiddleware.requirePermission('PAYRUN', 'READ'),
            (req, res) => {
                res.status(200).json({ message: 'Access granted' });
            }
        );

        const response = await request(app)
            .get('/api/payruns')
            .expect(200);

        expect(response.body.message).toBe('Access granted');
    });

    test('should deny access when permission missing', async () => {
        const mockPermissions = {
            domains: {
                PAYRUN: {
                    READ: false, // No read permission
                    CREATE: false,
                    UPDATE: false,
                    DELETE: false
                }
            }
        };

        await mockRedis.set(
            'exactuspay:permissions:v2:role:MANAGER',
            JSON.stringify(mockPermissions)
        );

        app.get(
            '/api/payruns',
            rbacMiddleware.requirePermission('PAYRUN', 'READ'),
            (req, res) => {
                res.status(200).json({ message: 'Access granted' });
            }
        );

        const response = await request(app)
            .get('/api/payruns')
            .expect(403);

        expect(response.body.error).toBe('Forbidden');
        expect(response.body.detail).toContain('lacks PAYRUN.READ permission');
    });

    test('should fall back to Django API when cache miss', async () => {
        // Clear Redis cache
        await mockRedis.del('exactuspay:permissions:v2:role:MANAGER');

        // Mock axios to simulate Django API response
        const mockAxios = require('axios');
        mockAxios.post.mockResolvedValue({
            data: { has_permission: true }
        });

        app.get(
            '/api/payruns',
            rbacMiddleware.requirePermission('PAYRUN', 'READ'),
            (req, res) => {
                res.status(200).json({ message: 'Access granted via API fallback' });
            }
        );

        const response = await request(app)
            .get('/api/payruns')
            .expect(200);

        expect(response.body.message).toBe('Access granted via API fallback');
        expect(mockAxios.post).toHaveBeenCalledWith(
            expect.stringContaining('/api/permissions/validate/'),
            expect.objectContaining({
                role: 'MANAGER',
                domain: 'PAYRUN',
                action: 'READ'
            }),
            expect.any(Object)
        );
    });

    test('should handle Django API failure gracefully', async () => {
        await mockRedis.del('exactuspay:permissions:v2:role:MANAGER');

        const mockAxios = require('axios');
        mockAxios.post.mockRejectedValue(new Error('Django API unavailable'));

        app.get(
            '/api/payruns',
            rbacMiddleware.requirePermission('PAYRUN', 'READ'),
            (req, res) => {
                res.status(200).json({ message: 'Access granted' });
            }
        );

        // Should deny access when API fails (fail-closed)
        await request(app)
            .get('/api/payruns')
            .expect(403);
    });
});

// test/rbac.cache.test.js
describe('RBAC Cache Tests', () => {
    test('should cache permissions locally after first check', async () => {
        const mockPermissions = {
            domains: {
                PAYRUN: { READ: true }
            }
        };

        await rbacMiddleware.redis.set(
            'exactuspay:permissions:v2:role:MANAGER',
            JSON.stringify(mockPermissions)
        );

        // First call - should hit Redis
        const result1 = await rbacMiddleware.checkPermission('MANAGER', 'PAYRUN', 'READ');
        
        // Second call - should hit local cache
        const result2 = await rbacMiddleware.checkPermission('MANAGER', 'PAYRUN', 'READ');

        expect(result1).toBe(true);
        expect(result2).toBe(true);
        
        // Verify Redis was called only once
        const redisCallCount = await rbacMiddleware.redis.get.callCount;
        expect(redisCallCount).toBe(1);
    });

    test('should invalidate cache correctly', async () => {
        await rbacMiddleware.redis.set(
            'exactuspay:permissions:v2:role:MANAGER',
            JSON.stringify({ domains: { PAYRUN: { READ: true } } })
        );

        // Prime the cache
        await rbacMiddleware.checkPermission('MANAGER', 'PAYRUN', 'READ');

        // Invalidate cache
        await rbacMiddleware.invalidateRoleCache('MANAGER');

        // Should hit Redis again after invalidation
        await rbacMiddleware.checkPermission('MANAGER', 'PAYRUN', 'READ');

        const redisCallCount = await rbacMiddleware.redis.get.callCount;
        expect(redisCallCount).toBe(2); // Called again after invalidation
    });
});