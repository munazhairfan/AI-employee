/**
 * Dashboard HTTP Server
 * Run: node dashboard-server.js
 * Port: 3000
 * 
 * Serves the customer dashboard and proxies API requests
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.DASHBOARD_PORT || 3000;

const server = http.createServer((req, res) => {
    // CORS headers for API proxy
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    // Handle CORS preflight
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }

    // Serve dashboard
    if (req.method === 'GET' && (req.url === '/' || req.url === '/dashboard' || req.url === '/dashboard.html')) {
        const dashboardPath = path.join(__dirname, 'public', 'dashboard.html');
        
        fs.readFile(dashboardPath, 'utf8', (err, content) => {
            if (err) {
                res.writeHead(500);
                res.end('Error loading dashboard');
                return;
            }
            
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(content);
        });
        return;
    }

    // Proxy API requests to backend servers
    if (req.method === 'POST' && req.url.startsWith('/api/')) {
        proxyApiRequest(req, res);
        return;
    }

    // 404 for other routes
    res.writeHead(404);
    res.end('Not found');
});

// Simple API proxy
function proxyApiRequest(req, res) {
    const url = new URL(req.url, `http://localhost:${PORT}`);
    const pathParts = url.pathname.split('/');
    
    let targetPort;
    let targetPath;
    
    // Route to appropriate backend
    if (url.pathname.includes('linkedin')) {
        targetPort = 3008;
        targetPath = '/api/v1/actions/post-linkedin';
    } else if (url.pathname.includes('email')) {
        targetPort = 3011;
        targetPath = '/api/v1/actions/send-email';
    } else if (url.pathname.includes('invoice') || url.pathname.includes('odoo')) {
        targetPort = 3004;
        targetPath = '/create_invoice';
    } else {
        res.writeHead(404);
        res.end('Unknown API endpoint');
        return;
    }

    // Forward request
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
        const options = {
            hostname: 'localhost',
            port: targetPort,
            path: targetPath,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(body)
            }
        };

        const proxyReq = http.request(options, (proxyRes) => {
            let proxyBody = '';
            proxyRes.on('data', chunk => { proxyBody += chunk; });
            proxyRes.on('end', () => {
                res.writeHead(proxyRes.statusCode, { 'Content-Type': 'application/json' });
                res.end(proxyBody);
            });
        });

        proxyReq.on('error', (e) => {
            res.writeHead(500);
            res.end(JSON.stringify({ error: `Backend server error: ${e.message}` }));
        });

        proxyReq.write(body);
        proxyReq.end();
    });
}

server.listen(PORT, () => {
    console.log('🎯 Dashboard Server running');
    console.log(`   URL: http://localhost:${PORT}`);
    console.log(`   Dashboard: http://localhost:${PORT}/dashboard`);
    console.log('');
    console.log('   Backend servers:');
    console.log('   - LinkedIn: http://localhost:3008');
    console.log('   - Email: http://localhost:3011');
    console.log('   - Odoo: http://localhost:3004');
    console.log('');
    console.log('   Open http://localhost:' + PORT + ' in your browser!');
});
