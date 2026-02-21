/**
 * MCP Server - Silver Tier
 * External Action Server for Email Sending
 *
 * SETUP INSTRUCTIONS:
 *
 * 1. Install Node.js from: https://nodejs.org/
 *
 * 2. Initialize project:
 *    npm init -y
 *
 * 3. Install dependencies:
 *    npm install express nodemailer cors body-parser dotenv
 *
 * 4. Create .env file in project root:
 *    EMAIL_USER=yourname@gmail.com
 *    EMAIL_PASS=your_app_password
 *
 * 5. Run the server:
 *    node mcp_server.js
 *
 * 6. Test the endpoint:
 *    curl -X POST http://localhost:3000/send_email ^
 *      -H "Content-Type: application/json" ^
 *      -d "{\"to\":\"test@example.com\",\"subject\":\"Test\",\"body\":\"Hello\"}"
 *
 * CONFIGURATION:
 * - Set EMAIL_USER and EMAIL_PASS in .env file or environment variables
 * - Or use console.log mode (default) for testing
 */

const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const nodemailer = require('nodemailer');
const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');

// Load environment variables from .env file
dotenv.config({ path: path.join(__dirname, '..', '.env') });

const app = express();
const PORT = 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Ensure Pending_Approval directory exists
const pendingApprovalDir = path.join('AI_Employee_Vault', 'Pending_Approval');
if (!fs.existsSync(pendingApprovalDir)) {
    fs.mkdirSync(pendingApprovalDir, { recursive: true });
}

// Configure email transporter (SMTP or console mode)
const SMTP_USER = process.env.EMAIL_USER || '';
const SMTP_PASS = process.env.EMAIL_PASS || '';
const CONSOLE_MODE = !SMTP_USER; // Use console.log if no SMTP configured

let transporter = null;
if (!CONSOLE_MODE) {
    transporter = nodemailer.createTransport({
        host: 'smtp.gmail.com',
        port: 587,
        secure: false,
        auth: {
            user: SMTP_USER,
            pass: SMTP_PASS
        }
    });
}

/**
 * POST /send_email
 * Send an email directly (approval already handled by orchestrator)
 *
 * Request body:
 * {
 *   "to": "recipient@example.com",
 *   "subject": "Email subject",
 *   "body": "Email body content",
 *   "cc": "optional@example.com",  // optional
 *   "priority": "high"              // optional
 * }
 */
app.post('/send_email', (req, res) => {
    const { to, subject, body, cc, priority } = req.body;

    // Validate required fields
    if (!to || !subject || !body) {
        return res.status(400).json({
            success: false,
            error: 'Missing required fields: to, subject, body'
        });
    }

    console.log(`[${new Date().toISOString()}] Sending email to ${to}: ${subject}`);

    if (CONSOLE_MODE) {
        // Console mode (no SMTP configured)
        console.log(`[${new Date().toISOString()}] CONSOLE MODE - Email would be sent:`);
        console.log(`  To: ${to}`);
        console.log(`  Subject: ${subject}`);
        console.log(`  Body: ${body.substring(0, 100)}...`);

        res.json({
            success: true,
            message: 'Email sent (console mode - check logs)',
            mode: 'console',
            details: { to, subject }
        });
    } else {
        // Real SMTP sending
        const mailOptions = {
            from: SMTP_USER,
            to,
            subject,
            text: body,
            cc: cc || undefined
        };

        transporter.sendMail(mailOptions, (error, info) => {
            if (error) {
                console.error(`[${new Date().toISOString()}] Email send error:`, error);

                return res.status(500).json({
                    success: false,
                    error: error.message
                });
            }

            console.log(`[${new Date().toISOString()}] Email sent successfully: ${info.messageId}`);

            res.json({
                success: true,
                message: 'Email sent successfully',
                messageId: info.messageId,
                mode: 'smtp',
                details: { to, subject }
            });
        });
    }
});

/**
 * POST /approve_email
 * Approve and send a pending email
 * 
 * Request body:
 * {
 *   "approval_file": "AI_Employee_Vault/Pending_Approval/EMAIL_APPROVAL_*.md",
 *   "action": "approve"  // or "reject"
 * }
 */
app.post('/approve_email', (req, res) => {
    const { approval_file, action } = req.body;

    if (!approval_file) {
        return res.status(400).json({
            success: false,
            error: 'Missing approval_file path'
        });
    }

    if (!fs.existsSync(approval_file)) {
        return res.status(404).json({
            success: false,
            error: 'Approval file not found'
        });
    }

    let content = fs.readFileSync(approval_file, 'utf-8');
    
    if (action === 'approve') {
        // Extract email details from approval file
        const toMatch = content.match(/\*\*To:\*\* (.+)/);
        const ccMatch = content.match(/\*\*CC:\*\* (.+)/);
        const subjectMatch = content.match(/\*\*Subject:\*\* (.+)/);
        const bodyMatch = content.match(/\*\*Body:\*\*\n([\s\S]*?)(?=\n---|$)/);

        if (!toMatch || !subjectMatch || !bodyMatch) {
            return res.status(400).json({
                success: false,
                error: 'Could not parse email details from approval file'
            });
        }

        const to = toMatch[1].trim();
        const subject = subjectMatch[1].trim();
        const body = bodyMatch[1].trim();
        const cc = ccMatch ? ccMatch[1].trim() : null;

        if (CONSOLE_MODE) {
            // Console mode (testing)
            console.log(`[${new Date().toISOString()}] SENDING EMAIL:`);
            console.log(`  To: ${to}`);
            console.log(`  Subject: ${subject}`);
            console.log(`  Body: ${body.substring(0, 100)}...`);
            
            // Update approval file
            content = content.replace('status: pending', 'status: sent (console mode)');
            fs.writeFileSync(approval_file, content, 'utf-8');

            res.json({
                success: true,
                message: 'Email sent (console mode - check logs)',
                mode: 'console'
            });
        } else {
            // Real SMTP sending
            const mailOptions = {
                from: SMTP_USER,
                to,
                subject,
                text: body,
                cc: cc || undefined
            };

            transporter.sendMail(mailOptions, (error, info) => {
                if (error) {
                    console.error(`[${new Date().toISOString()}] Email send error:`, error);
                    
                    content = content.replace('status: pending', 'status: failed');
                    fs.writeFileSync(approval_file, content, 'utf-8');

                    return res.status(500).json({
                        success: false,
                        error: error.message
                    });
                }

                console.log(`[${new Date().toISOString()}] Email sent: ${info.messageId}`);
                
                content = content.replace('status: pending', `status: sent (${info.messageId})`);
                fs.writeFileSync(approval_file, content, 'utf-8');

                res.json({
                    success: true,
                    message: 'Email sent successfully',
                    messageId: info.messageId,
                    mode: 'smtp'
                });
            });
        }
    } else if (action === 'reject') {
        // Reject the email
        content = content.replace('status: pending', 'status: rejected');
        fs.writeFileSync(approval_file, content, 'utf-8');

        console.log(`[${new Date().toISOString()}] Email rejected: ${approval_file}`);

        res.json({
            success: true,
            message: 'Email approval rejected'
        });
    } else {
        return res.status(400).json({
            success: false,
            error: 'Invalid action. Use "approve" or "reject"'
        });
    }
});

/**
 * GET /pending_emails
 * List all pending email approvals
 */
app.get('/pending_emails', (req, res) => {
    const files = fs.readdirSync(pendingApprovalDir)
        .filter(f => f.startsWith('EMAIL_APPROVAL_'))
        .map(f => {
            const filePath = path.join(pendingApprovalDir, f);
            const content = fs.readFileSync(filePath, 'utf-8');
            const statusMatch = content.match(/status: (.+)/);
            const toMatch = content.match(/\*\*To:\*\* (.+)/);
            const subjectMatch = content.match(/\*\*Subject:\*\* (.+)/);

            return {
                file: f,
                status: statusMatch ? statusMatch[1].trim() : 'unknown',
                to: toMatch ? toMatch[1].trim() : 'unknown',
                subject: subjectMatch ? subjectMatch[1].trim() : 'unknown'
            };
        });

    res.json({
        success: true,
        pending: files.filter(f => f.status.includes('pending')),
        completed: files.filter(f => !f.status.includes('pending'))
    });
});

/**
 * GET /health
 * Health check endpoint
 */
app.get('/health', (req, res) => {
    res.json({
        success: true,
        status: 'running',
        mode: CONSOLE_MODE ? 'console' : 'smtp',
        timestamp: new Date().toISOString()
    });
});

// Start server
app.listen(PORT, () => {
    console.log('='.repeat(60));
    console.log('MCP SERVER - Silver Tier');
    console.log('='.repeat(60));
    console.log(`Server running on http://localhost:${PORT}`);
    console.log(`Mode: ${CONSOLE_MODE ? 'Console (testing)' : 'SMTP (live)'}`);
    console.log('');
    console.log('Endpoints:');
    console.log(`  POST /send_email      - Create email approval request`);
    console.log(`  POST /approve_email   - Approve/reject pending email`);
    console.log(`  GET  /pending_emails  - List all pending approvals`);
    console.log(`  GET  /health          - Health check`);
    console.log('');
    console.log('Pending approvals stored in:', pendingApprovalDir);
    console.log('='.repeat(60));
});
