/**
 * Odoo MCP Server - Gold Tier
 * Odoo ERP Integration via JSON-RPC (native http)
 * 
 * Run: node odoo_mcp.js
 */

const express = require('express');
const bodyParser = require('body-parser');
const http = require('http');
require('dotenv').config();

const app = express();
const PORT = process.env.MCP_PORT || 3004;

// Odoo configuration from .env
const ODOO_CONFIG = {
    url: process.env.ODOO_URL || 'http://localhost',
    port: parseInt(process.env.ODOO_PORT) || 8069,
    db: process.env.ODOO_DB || 'ai_employee_db',
    username: process.env.ODOO_USER || 'admin',
    password: process.env.ODOO_PASS || 'admin'
};

// Parse URL to extract hostname without port
const parsedUrl = ODOO_CONFIG.url.replace('http://', '').replace('https://', '').split(':')[0];
const ODOO_HOSTNAME = parsedUrl || 'localhost';

// Middleware
app.use(bodyParser.json());

// JSON-RPC helper using native http
function jsonRpcCall(service, method, args) {
    return new Promise((resolve, reject) => {
        const url = `${ODOO_CONFIG.url}:${ODOO_CONFIG.port}/jsonrpc`;
        const payload = {
            jsonrpc: '2.0',
            method: 'call',
            params: { service, method, args },
            id: Math.floor(Math.random() * 1000000)
        };

        const data = JSON.stringify(payload);
        const options = {
            hostname: ODOO_HOSTNAME,
            port: ODOO_CONFIG.port,
            path: '/jsonrpc',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': data.length
            },
            timeout: 30000
        };

        console.log(`[JSONRPC] ${service}.${method}`);

        const req = http.request(options, (res) => {
            let body = '';
            res.on('data', chunk => body += chunk);
            res.on('end', () => {
                try {
                    const result = JSON.parse(body);
                    if (result.error) {
                        reject(new Error(result.error.data?.message || result.error.message));
                    } else {
                        resolve(result.result);
                    }
                } catch (e) {
                    reject(new Error(`Parse error: ${e.message}`));
                }
            });
        });

        req.on('error', reject);
        req.on('timeout', () => {
            req.destroy();
            reject(new Error('Request timeout'));
        });

        req.write(data);
        req.end();
    });
}

// Authenticate with Odoo
async function authenticate() {
    console.log(`[AUTH] db=${ODOO_CONFIG.db}, user=${ODOO_CONFIG.username}`);
    
    const result = await jsonRpcCall('common', 'authenticate', [
        ODOO_CONFIG.db,
        ODOO_CONFIG.username,
        ODOO_CONFIG.password,
        {}
    ]);
    
    const uid = typeof result === 'number' ? result : (result && result.uid);
    
    if (!uid || uid <= 0) {
        throw new Error('Authentication failed: Invalid credentials');
    }
    
    console.log(`[AUTH] Success: uid=${uid}`);
    return uid;
}

// Execute Odoo method
async function executeMethod(model, method, args = [], kwargs = {}) {
    const uid = await authenticate();
    
    const fullArgs = [ODOO_CONFIG.db, uid, ODOO_CONFIG.password, model, method, args];
    if (kwargs && Object.keys(kwargs).length > 0) {
        fullArgs.push(kwargs);
    }
    
    console.log(`[EXEC] ${model}.${method}`);
    const result = await jsonRpcCall('object', 'execute_kw', fullArgs);
    console.log(`[EXEC] Result: ${JSON.stringify(result).substring(0, 100)}`);
    return result;
}

// GET /health
app.get('/health', async (req, res) => {
    console.log('[HEALTH] Check requested');
    try {
        const uid = await authenticate();
        res.json({
            success: true,
            status: 'connected',
            odoo: { url: `${ODOO_CONFIG.url}:${ODOO_CONFIG.port}`, db: ODOO_CONFIG.db, user: ODOO_CONFIG.username },
            uid,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error(`[HEALTH] Error: ${error.message}`);
        res.status(500).json({ success: false, status: 'disconnected', error: error.message });
    }
});

// POST /authenticate
app.post('/authenticate', async (req, res) => {
    console.log('[AUTHENTICATE] Request received');
    try {
        const db = req.body.db || ODOO_CONFIG.db;
        const username = req.body.username || ODOO_CONFIG.username;
        const password = req.body.password || ODOO_CONFIG.password;
        
        console.log(`[AUTHENTICATE] db=${db}, user=${username}`);
        
        const result = await jsonRpcCall('common', 'authenticate', [db, username, password, {}]);
        const uid = typeof result === 'number' ? result : (result && result.uid);
        
        if (!uid || uid <= 0) {
            return res.status(401).json({ success: false, error: 'Invalid credentials' });
        }
        
        console.log(`[AUTHENTICATE] Success: uid=${uid}`);
        res.json({ success: true, uid, db, user: username });
    } catch (error) {
        console.error(`[AUTHENTICATE] Error: ${error.message}`);
        res.status(500).json({ success: false, error: error.message });
    }
});

// POST /create_invoice
app.post('/create_invoice', async (req, res) => {
    console.log('[CREATE_INVOICE] Request received');
    
    const { partner_name, amount, description } = req.body;
    
    if (!partner_name || !amount || !description) {
        return res.status(400).json({ success: false, error: 'Missing required fields: partner_name, amount, description' });
    }
    
    console.log(`[CREATE_INVOICE] partner=${partner_name}, amount=${amount}, desc=${description}`);
    
    try {
        // Search for existing partner
        const existingPartners = await executeMethod('res.partner', 'search_read', [
            [['name', 'ilike', partner_name]]
        ], { fields: ['id', 'name'], limit: 1 });
        
        let partnerId;
        
        if (existingPartners && existingPartners.length > 0) {
            partnerId = existingPartners[0].id;
            console.log(`[CREATE_INVOICE] Found partner: id=${partnerId}`);
        } else {
            partnerId = await executeMethod('res.partner', 'create', [{ name: partner_name, customer_rank: 1 }]);
            console.log(`[CREATE_INVOICE] Created partner: id=${partnerId}`);
        }
        
        // Create invoice
        const invoiceId = await executeMethod('account.move', 'create', [{
            move_type: 'out_invoice',
            partner_id: partnerId,
            invoice_line_ids: [[0, 0, { name: description, quantity: 1, price_unit: parseFloat(amount) }]]
        }]);
        
        console.log(`[CREATE_INVOICE] Invoice created: id=${invoiceId}`);
        
        res.json({ success: true, invoice_id: invoiceId, partner_id: partnerId, partner_name, amount, message: 'Invoice created successfully' });
    } catch (error) {
        console.error(`[CREATE_INVOICE] Error: ${error.message}`);
        res.status(500).json({ success: false, error: error.message });
    }
});

// POST /read_invoices
app.post('/read_invoices', async (req, res) => {
    console.log('[READ_INVOICES] Request received');
    
    const { limit = 10, offset = 0, state = 'posted' } = req.body || {};
    console.log(`[READ_INVOICES] limit=${limit}, state=${state}`);
    
    try {
        const domain = [['move_type', '=', 'out_invoice']];
        if (state !== 'all') domain.push(['state', '=', state]);
        
        const invoices = await executeMethod('account.move', 'search_read', [domain], {
            fields: ['id', 'name', 'partner_id', 'amount_total', 'amount_untaxed', 'amount_tax', 'state', 'invoice_date', 'invoice_date_due', 'ref'],
            limit: parseInt(limit),
            offset: parseInt(offset),
            order: 'invoice_date desc, id desc'
        });
        
        const formatted = invoices.map(inv => ({
            id: inv.id,
            name: inv.name,
            partner_id: Array.isArray(inv.partner_id) ? inv.partner_id[0] : inv.partner_id,
            partner_name: Array.isArray(inv.partner_id) ? inv.partner_id[1] : null,
            amount_total: inv.amount_total,
            state: inv.state,
            invoice_date: inv.invoice_date,
            invoice_date_due: inv.invoice_date_due
        }));
        
        console.log(`[READ_INVOICES] Found ${formatted.length} invoices`);
        res.json({ success: true, count: formatted.length, invoices: formatted });
    } catch (error) {
        console.error(`[READ_INVOICES] Error: ${error.message}`);
        res.status(500).json({ success: false, error: error.message });
    }
});

// POST /search_partner
app.post('/search_partner', async (req, res) => {
    console.log('[SEARCH_PARTNER] Request received');
    const { name } = req.body;
    if (!name) return res.status(400).json({ success: false, error: 'Missing required field: name' });
    
    console.log(`[SEARCH_PARTNER] Searching: ${name}`);
    
    try {
        const partners = await executeMethod('res.partner', 'search_read', [
            [['name', 'ilike', name]]
        ], { fields: ['id', 'name', 'email', 'phone', 'vat', 'is_customer', 'is_supplier'], limit: 20 });
        
        console.log(`[SEARCH_PARTNER] Found ${partners.length} partners`);
        res.json({ success: true, count: partners.length, partners });
    } catch (error) {
        console.error(`[SEARCH_PARTNER] Error: ${error.message}`);
        res.status(500).json({ success: false, error: error.message });
    }
});

// POST /create_partner
app.post('/create_partner', async (req, res) => {
    console.log('[CREATE_PARTNER] Request received');
    const { name, email, phone, is_customer = true } = req.body;
    if (!name) return res.status(400).json({ success: false, error: 'Missing required field: name' });

    console.log(`[CREATE_PARTNER] Creating: ${name}`);

    try {
        const partnerData = { name, email: email || '', phone: phone || '' };
        if (is_customer) partnerData.customer_rank = 1;
        
        const partnerId = await executeMethod('res.partner', 'create', [partnerData]);
        console.log(`[CREATE_PARTNER] Created: id=${partnerId}`);
        res.json({ success: true, partner_id: partnerId, name });
    } catch (error) {
        console.error(`[CREATE_PARTNER] Error: ${error.message}`);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Start server
app.listen(PORT, () => {
    console.log('='.repeat(60));
    console.log('Odoo MCP Server - Gold Tier');
    console.log('='.repeat(60));
    console.log(`Server: http://localhost:${PORT}`);
    console.log(`Odoo: ${ODOO_CONFIG.url}:${ODOO_CONFIG.port}/${ODOO_CONFIG.db}`);
    console.log('Endpoints: /health, /authenticate, /create_invoice, /read_invoices, /search_partner, /create_partner');
    console.log('='.repeat(60));
});
