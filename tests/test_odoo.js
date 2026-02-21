const fetch = require('node-fetch');

const ODOO_CONFIG = {
    url: 'http://localhost',
    port: 8069,
    db: 'ai_employee_db',
    username: 'admin',
    password: 'admin'
};

async function odooJsonRpc(service, method, args) {
    const url = `${ODOO_CONFIG.url}:${ODOO_CONFIG.port}/jsonrpc`;

    console.log(`Connecting to: ${url}`);
    console.log(`Service: ${service}, Method: ${method}`);
    console.log(`Args: ${JSON.stringify(args)}`);

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            jsonrpc: '2.0',
            method: 'call',
            params: {
                service: service,
                method: method,
                args: args
            },
            id: 1
        })
    });

    const result = await response.json();
    console.log(`Response: ${JSON.stringify(result, null, 2)}`);
    return result;
}

async function test() {
    console.log('=== Testing Odoo Authentication ===\n');
    
    try {
        const result = await odooJsonRpc('common', 'authenticate', [
            ODOO_CONFIG.db,
            ODOO_CONFIG.username,
            ODOO_CONFIG.password,
            {}
        ]);

        if (result.result && result.result.uid) {
            console.log('\n✓ Authentication SUCCESSFUL!');
            console.log(`UID: ${result.result.uid}`);
        } else {
            console.log('\n✗ Authentication FAILED!');
        }
    } catch (error) {
        console.error('\n✗ Error:', error.message);
    }
}

test();
