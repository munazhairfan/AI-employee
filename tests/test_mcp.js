const http = require('http');

function request(method, path, data = null) {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: 'localhost',
            port: 3004,
            path: path,
            method: method,
            headers: { 'Content-Type': 'application/json' }
        };

        const req = http.request(options, (res) => {
            let body = '';
            res.on('data', chunk => body += chunk);
            res.on('end', () => {
                try {
                    resolve({ status: res.statusCode, data: JSON.parse(body) });
                } catch (e) {
                    resolve({ status: res.statusCode, data: body });
                }
            });
        });

        req.on('error', reject);
        req.setTimeout(10000, () => reject(new Error('Timeout')));

        if (data) req.write(JSON.stringify(data));
        req.end();
    });
}

async function runTests() {
    console.log('='.repeat(60));
    console.log('Odoo MCP Server Tests');
    console.log('='.repeat(60));

    try {
        // Test 1: Health
        console.log('\n[1/4] GET /health...');
        const health = await request('GET', '/health');
        console.log(`Status: ${health.status}`);
        console.log(`Response: ${JSON.stringify(health.data, null, 2)}`);

        // Test 2: Authenticate
        console.log('\n[2/4] POST /authenticate...');
        const auth = await request('POST', '/authenticate', {});
        console.log(`Status: ${auth.status}`);
        console.log(`Response: ${JSON.stringify(auth.data, null, 2)}`);
        const uid = auth.data.uid;

        // Test 3: Create Invoice
        console.log('\n[3/4] POST /create_invoice...');
        const invoice = await request('POST', '/create_invoice', {
            partner_name: 'Test Client ABC',
            amount: 7500,
            description: 'AI Automation Consulting'
        });
        console.log(`Status: ${invoice.status}`);
        console.log(`Response: ${JSON.stringify(invoice.data, null, 2)}`);

        // Test 4: Read Invoices
        console.log('\n[4/4] POST /read_invoices...');
        const invoices = await request('POST', '/read_invoices', {
            state: 'all',
            limit: 5
        });
        console.log(`Status: ${invoices.status}`);
        console.log(`Response: ${JSON.stringify(invoices.data, null, 2)}`);

        console.log('\n' + '='.repeat(60));
        console.log('ALL TESTS COMPLETED');
        console.log('='.repeat(60));

    } catch (error) {
        console.error('\nTEST ERROR:', error.message);
        console.error('Make sure Odoo MCP server is running: node odoo_mcp.js');
    }
}

runTests();
