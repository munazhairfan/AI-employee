import fetch from 'node-fetch';

async function test() {
    const url = 'http://localhost:3004/read_invoices';
    
    console.log('Testing read_invoices with state=draft...\n');
    
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ state: 'draft', limit: 10 })
    });
    
    const result = await response.json();
    console.log('Response:', JSON.stringify(result, null, 2));
}

test();
