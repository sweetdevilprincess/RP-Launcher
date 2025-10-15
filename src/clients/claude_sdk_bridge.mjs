#!/usr/bin/env node
/**
 * Claude Code SDK Bridge
 *
 * High-performance bridge between Python automation and Claude Code SDK.
 * Provides real-time streaming, proper caching, and session management.
 *
 * Communication:
 * - Input: JSON messages via stdin
 * - Output: JSON responses via stdout
 *
 * Features:
 * - Direct SDK integration (no subprocess overhead)
 * - Streaming responses in real-time
 * - Automatic prompt caching for TIER_1 files
 * - Session resumption built-in
 * - Cache statistics reporting
 */

import { query } from '@anthropic-ai/claude-code';
import * as readline from 'readline';

// Session state
let currentSessionId = null;
let conversationHistory = [];

/**
 * Send a JSON message to Python via stdout
 */
function sendMessage(type, data) {
    const message = {
        type,
        timestamp: new Date().toISOString(),
        ...data
    };
    console.log(JSON.stringify(message));
}

/**
 * Send an error message
 */
function sendError(error, details = {}) {
    sendMessage('error', {
        error: error.message || String(error),
        stack: error.stack,
        ...details
    });
}

/**
 * Send a status update
 */
function sendStatus(status, details = {}) {
    sendMessage('status', {
        status,
        ...details
    });
}

/**
 * Send streaming content chunk
 */
function sendChunk(content, metadata = {}) {
    sendMessage('chunk', {
        content,
        ...metadata
    });
}

/**
 * Send final response
 */
function sendResponse(content, usage = {}, metadata = {}) {
    sendMessage('response', {
        content,
        usage,
        ...metadata
    });
}

/**
 * Send cache statistics
 */
function sendCacheStats(usage) {
    const stats = {
        input_tokens: usage.input_tokens || 0,
        output_tokens: usage.output_tokens || 0,
        cache_creation_input_tokens: usage.cache_creation_input_tokens || 0,
        cache_read_input_tokens: usage.cache_read_input_tokens || 0,
    };

    // Calculate savings
    const totalCached = stats.cache_read_input_tokens;
    const totalInput = stats.input_tokens;
    const cacheSavings = totalCached > 0 ? ((totalCached / (totalInput + totalCached)) * 100).toFixed(1) : 0;

    sendMessage('cache_stats', {
        ...stats,
        cache_savings_percent: cacheSavings,
        cache_status: totalCached > 0 ? 'HIT' : (stats.cache_creation_input_tokens > 0 ? 'CREATED' : 'NONE')
    });
}

// Thinking mode presets (matching Claude Code CLI)
const THINKING_MODES = {
    disabled: 0,           // No extended thinking
    think: 4000,           // Quick reasoning
    megathink: 10000,      // Standard reasoning
    ultrathink: 31999,     // Maximum reasoning
};

/**
 * Process a query using Claude Code SDK
 */
async function processQuery(request) {
    const {
        message,
        cached_context = null,
        session_id = null,
        cwd = null,
        thinking_mode = 'megathink',
        thinking_budget = null,
        options = {}
    } = request;

    try {
        sendStatus('processing', { message: 'Initializing Claude Code SDK...' });

        // Build the full prompt
        let fullPrompt = '';

        // If we have cached context, it becomes the system prompt
        // This is what gets cached by Claude's prompt caching
        if (cached_context) {
            fullPrompt = cached_context + '\n\n' + message;
            sendStatus('caching', {
                message: 'Using cached context (TIER_1 files)',
                cached_size: cached_context.length
            });
        } else {
            fullPrompt = message;
        }

        // Determine thinking budget
        let finalBudget;
        if (thinking_budget !== null && thinking_budget !== undefined) {
            // Custom budget provided
            finalBudget = thinking_budget;
        } else if (thinking_mode in THINKING_MODES) {
            // Use preset
            finalBudget = THINKING_MODES[thinking_mode];
        } else {
            // Unknown mode, default to megathink
            finalBudget = THINKING_MODES.megathink;
        }

        // Build SDK options
        const sdkOptions = {
            cwd: cwd || process.cwd(),
            // Resume session if we have one
            resume: session_id || currentSessionId,
            // Continue conversation
            continue: !!currentSessionId,
            ...options
        };

        // Add thinking config only if budget > 0
        if (finalBudget > 0) {
            sdkOptions.maxThinkingTokens = finalBudget;
        }

        sendStatus('querying', {
            message: 'Sending to Claude Code...',
            session_id: sdkOptions.resume || 'new'
        });

        // Create query
        const response = query({
            prompt: fullPrompt,
            options: sdkOptions
        });

        let fullResponse = '';
        let lastUsage = null;
        let assistantMessage = null;
        let newSessionId = null;

        // Process streaming messages
        for await (const msg of response) {
            // Handle different message types
            switch (msg.type) {
                case 'system':
                    if (msg.subtype === 'init') {
                        // Session initialized
                        newSessionId = msg.session_id;
                        currentSessionId = msg.session_id;

                        sendStatus('initialized', {
                            session_id: msg.session_id,
                            model: msg.model,
                            tools: msg.tools?.length || 0,
                            cwd: msg.cwd
                        });
                    }
                    break;

                case 'assistant':
                    // Full assistant message
                    assistantMessage = msg.message;

                    // Extract text content
                    if (msg.message.content) {
                        for (const block of msg.message.content) {
                            if (block.type === 'text') {
                                fullResponse += block.text;
                            }
                        }
                    }

                    // Store usage
                    if (msg.message.usage) {
                        lastUsage = msg.message.usage;
                    }
                    break;

                case 'stream_event':
                    // Streaming content
                    if (msg.event.type === 'content_block_delta') {
                        if (msg.event.delta?.type === 'text_delta') {
                            const chunk = msg.event.delta.text;
                            fullResponse += chunk;
                            sendChunk(chunk);
                        }
                    }
                    break;

                case 'result':
                    // Final result with usage stats
                    if (msg.usage) {
                        lastUsage = msg.usage;
                    }

                    sendStatus('complete', {
                        num_turns: msg.num_turns,
                        duration_ms: msg.duration_ms,
                        cost_usd: msg.total_cost_usd
                    });
                    break;
            }
        }

        // Send final response
        sendResponse(fullResponse, lastUsage, {
            session_id: newSessionId || currentSessionId,
            message_count: conversationHistory.length
        });

        // Send cache statistics if available
        if (lastUsage) {
            sendCacheStats(lastUsage);
        }

        // Update conversation history
        conversationHistory.push({
            role: 'user',
            content: message
        });
        conversationHistory.push({
            role: 'assistant',
            content: fullResponse
        });

    } catch (error) {
        sendError(error, {
            context: 'query_processing',
            request_id: request.request_id
        });
    }
}

/**
 * Clear current session
 */
function clearSession() {
    currentSessionId = null;
    conversationHistory = [];
    sendStatus('session_cleared', {
        message: 'Session cleared - next message will start fresh'
    });
}

/**
 * Main event loop - read JSON requests from stdin
 */
async function main() {
    sendStatus('ready', {
        message: 'Claude Code SDK Bridge initialized',
        sdk_version: '2.0.1',
        node_version: process.version
    });

    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
        terminal: false
    });

    rl.on('line', async (line) => {
        try {
            const request = JSON.parse(line);

            // Handle different command types
            switch (request.command) {
                case 'query':
                    await processQuery(request);
                    break;

                case 'clear_session':
                    clearSession();
                    break;

                case 'ping':
                    sendMessage('pong', {
                        session_id: currentSessionId,
                        history_length: conversationHistory.length
                    });
                    break;

                case 'shutdown':
                    sendStatus('shutdown', { message: 'Shutting down...' });
                    process.exit(0);
                    break;

                default:
                    sendError(new Error(`Unknown command: ${request.command}`), {
                        command: request.command
                    });
            }
        } catch (error) {
            sendError(error, {
                context: 'request_parsing',
                line: line.substring(0, 100)
            });
        }
    });

    rl.on('close', () => {
        sendStatus('closed', { message: 'Input stream closed' });
        process.exit(0);
    });

    // Handle uncaught errors
    process.on('uncaughtException', (error) => {
        sendError(error, { context: 'uncaught_exception' });
        process.exit(1);
    });

    process.on('unhandledRejection', (reason, promise) => {
        sendError(new Error(`Unhandled rejection: ${reason}`), {
            context: 'unhandled_rejection'
        });
    });
}

// Start the bridge
main().catch((error) => {
    sendError(error, { context: 'main_initialization' });
    process.exit(1);
});
