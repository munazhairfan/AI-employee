/**
 * Social Media MCP Server - Gold Tier
 * Draft posting with clipboard + manual browser workflow
 * 
 * Run: node social_mcp.js
 * Install dependencies: npm install express clipboardy
 */

const express = require('express');
const clipboardyModule = require('clipboardy');
const clipboardy = clipboardyModule.default || clipboardyModule;
const { spawn } = require('child_process');

const app = express();
const PORT = 3005;

// Platform URLs for posting
const PLATFORM_URLS = {
    facebook: 'https://www.facebook.com/',
    instagram: 'https://www.instagram.com/create/post/',
    x: 'https://twitter.com/compose/post'
};

// Middleware
app.use(express.json());

/**
 * POST /post_draft_fb
 * Copy content to clipboard and open Facebook for manual posting
 */
app.post('/post_draft_fb', async (req, res) => {
    try {
        const { content } = req.body;

        if (!content) {
            return res.status(400).json({
                success: false,
                error: 'Missing required field: content'
            });
        }

        console.log(`[${new Date().toISOString()}] Facebook draft received (${content.length} chars)`);

        // Copy to clipboard
        await clipboardy.write(content);
        console.log('Content copied to clipboard');

        // Open browser to Facebook
        await openBrowser(PLATFORM_URLS.facebook);
        console.log('Facebook opened in browser');

        console.log('Ready for manual post');

        res.json({
            success: true,
            message: 'Content copied to clipboard, Facebook opened. Ready for manual post.',
            platform: 'facebook',
            content_length: content.length
        });

    } catch (error) {
        console.error(`[${new Date().toISOString()}] Error with Facebook draft:`, error.message);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

/**
 * POST /post_draft_ig
 * Copy content to clipboard and open Instagram for manual posting
 */
app.post('/post_draft_ig', async (req, res) => {
    try {
        const { content } = req.body;

        if (!content) {
            return res.status(400).json({
                success: false,
                error: 'Missing required field: content'
            });
        }

        console.log(`[${new Date().toISOString()}] Instagram draft received (${content.length} chars)`);

        // Copy to clipboard
        await clipboardy.write(content);
        console.log('Content copied to clipboard');

        // Open browser to Instagram
        await openBrowser(PLATFORM_URLS.instagram);
        console.log('Instagram opened in browser');

        console.log('Ready for manual post');

        res.json({
            success: true,
            message: 'Content copied to clipboard, Instagram opened. Ready for manual post.',
            platform: 'instagram',
            content_length: content.length
        });

    } catch (error) {
        console.error(`[${new Date().toISOString()}] Error with Instagram draft:`, error.message);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

/**
 * POST /post_draft_x
 * Copy content to clipboard and open X (Twitter) for manual posting
 */
app.post('/post_draft_x', async (req, res) => {
    try {
        const { content } = req.body;

        if (!content) {
            return res.status(400).json({
                success: false,
                error: 'Missing required field: content'
            });
        }

        console.log(`[${new Date().toISOString()}] X draft received (${content.length} chars)`);

        // Copy to clipboard
        await clipboardy.write(content);
        console.log('Content copied to clipboard');

        // Open browser to X
        await openBrowser(PLATFORM_URLS.x);
        console.log('X opened in browser');

        console.log('Ready for manual post');

        res.json({
            success: true,
            message: 'Content copied to clipboard, X opened. Ready for manual post.',
            platform: 'x',
            content_length: content.length
        });

    } catch (error) {
        console.error(`[${new Date().toISOString()}] Error with X draft:`, error.message);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

/**
 * Open URL in default browser
 */
async function openBrowser(url) {
    return new Promise((resolve, reject) => {
        const platform = process.platform;
        let cmd;

        if (platform === 'win32') {
            cmd = spawn('cmd', ['/c', 'start', url]);
        } else if (platform === 'darwin') {
            cmd = spawn('open', [url]);
        } else {
            cmd = spawn('xdg-open', [url]);
        }

        cmd.on('error', (err) => {
            reject(new Error(`Failed to open browser: ${err.message}`));
        });

        cmd.on('close', (code) => {
            if (code === 0) {
                resolve();
            } else {
                reject(new Error(`Browser process exited with code ${code}`));
            }
        });

        // Resolve immediately as spawn is non-blocking for the app launch
        setTimeout(resolve, 500);
    });
}

/**
 * GET /health
 * Health check endpoint
 */
app.get('/health', (req, res) => {
    res.json({
        success: true,
        status: 'running',
        endpoints: [
            'POST /post_draft_fb - Facebook draft posting',
            'POST /post_draft_ig - Instagram draft posting',
            'POST /post_draft_x - X (Twitter) draft posting',
            'GET /health - Health check'
        ],
        timestamp: new Date().toISOString()
    });
});

// Start server
app.listen(PORT, () => {
    console.log('='.repeat(60));
    console.log('Social Media MCP Server - Gold Tier');
    console.log('='.repeat(60));
    console.log(`Server running on http://localhost:${PORT}`);
    console.log('');
    console.log('Endpoints:');
    console.log(`  POST /post_draft_fb  - Copy to clipboard + open Facebook`);
    console.log(`  POST /post_draft_ig  - Copy to clipboard + open Instagram`);
    console.log(`  POST /post_draft_x   - Copy to clipboard + open X (Twitter)`);
    console.log(`  GET  /health         - Health check`);
    console.log('');
    console.log('Workflow:');
    console.log('  1. Send POST request with { "content": "your post text" }');
    console.log('  2. Content is copied to clipboard automatically');
    console.log('  3. Browser opens to platform compose page');
    console.log('  4. Paste (Ctrl+V) and post manually');
    console.log('='.repeat(60));
});
