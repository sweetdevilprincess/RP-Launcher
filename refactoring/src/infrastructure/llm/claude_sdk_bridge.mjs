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
 * - Custom system prompt loading from config file
 */

import { query } from '@anthropic-ai/claude-agent-sdk';
import * as readline from 'readline';
import { readFile } from 'fs/promises';
import { join, dirname, resolve } from 'path';

// Session state
let currentSessionId = null;
let conversationHistory = [];

/**
 * Recursively resolve @import statements in markdown files
 * Follows Claude Code's @import pattern with max depth of 5 hops
 *
 * @param {string} content - File content with potential @import statements
 * @param {string} baseDir - Directory containing the file (for resolving relative imports)
 * @param {number} depth - Current recursion depth (max 5)
 * @param {Set<string>} visited - Set of already-visited file paths to prevent cycles
 * @returns {Promise<string>} Fully resolved content with all imports inlined
 */
async function resolveImports(content, baseDir, depth = 0, visited = new Set()) {
    // Max depth limit (matching Claude Code CLI)
    if (depth >= 5) {
        return content;
    }

    // Find all @import statements (but not in code blocks)
    // Pattern: @path/to/file.md (not inside backticks or code fences)
    const lines = content.split('\n');
    const resolvedLines = [];
    let inCodeBlock = false;

    for (const line of lines) {
        // Track code fences
        if (line.trim().startsWith('```')) {
            inCodeBlock = !inCodeBlock;
            resolvedLines.push(line);
            continue;
        }

        // Skip processing if we're inside a code block
        if (inCodeBlock) {
            resolvedLines.push(line);
            continue;
        }

        // Check for @import pattern (not in inline code spans)
        // Allow spaces in filenames: match @path/to/file.md where path can contain spaces
        const importMatch = line.match(/^@(.+\.md)\s*$/);
        if (importMatch && !line.includes('`')) {
            const importPath = importMatch[1].trim();

            // Resolve path relative to baseDir
            const absolutePath = resolve(baseDir, importPath);

            // Check if we've already visited this file (prevent cycles)
            if (visited.has(absolutePath)) {
                resolvedLines.push(`<!-- Skipping circular import: ${importPath} -->`);
                continue;
            }

            try {
                // Read the imported file
                const importedContent = await readFile(absolutePath, 'utf-8');

                // Mark as visited
                visited.add(absolutePath);

                // Recursively resolve imports in the imported file
                const importedDir = dirname(absolutePath);
                const resolvedImport = await resolveImports(
                    importedContent,
                    importedDir,
                    depth + 1,
                    visited
                );

                // Add comment showing where content came from (with resolved absolute path for debugging)
                resolvedLines.push(`<!-- BEGIN IMPORT: ${importPath} (resolved to: ${absolutePath}) -->`);
                resolvedLines.push(resolvedImport);
                resolvedLines.push(`<!-- END IMPORT: ${importPath} -->`);
            } catch (error) {
                // If import fails, leave a detailed comment and continue
                resolvedLines.push(`<!-- Failed to import ${importPath} (tried: ${absolutePath}): ${error.message} -->`);
            }
        } else {
            resolvedLines.push(line);
        }
    }

    return resolvedLines.join('\n');
}

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
    think: 5000,           // Quick planning, simple refactoring
    'think hard': 10000,   // Feature design, debugging
    megathink: 10000,      // Standard reasoning (same as think hard)
    'think harder': 25000, // Architecture decisions, complex bugs
    ultrathink: 31999,     // Maximum reasoning - system design
};

/**
 * Process a query using Claude Code SDK
 */
async function processQuery(request) {
    const {
        message,
        cached_context = null,
        conversation_history = null,
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

        // If we have conversation history, format it
        if (conversation_history && conversation_history.length > 0) {
            fullPrompt = 'Previous conversation:\n\n';
            for (const msg of conversation_history) {
                const role = msg.role === 'user' ? 'User' : 'Assistant';
                fullPrompt += `${role}: ${msg.content}\n\n`;
            }
            fullPrompt += `User: ${message}`;
            sendStatus('history', {
                message: 'Using conversation history from session',
                history_length: conversation_history.length
            });
        } else {
            fullPrompt = message;
        }

        // If we have cached context, prepend it
        // This is what gets cached by Claude's prompt caching
        if (cached_context) {
            fullPrompt = cached_context + '\n\n' + fullPrompt;
            sendStatus('caching', {
                message: 'Using cached context (TIER_1 files)',
                cached_size: cached_context.length
            });
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

        // Load custom system prompt if available
        let customSystemPrompt = null;
        let configDir = null;  // Declare outside try block so it's accessible later
        try {
            // Find the project root by looking for config directory
            // Start from cwd and go up directories until we find config/
            let searchDir = cwd || process.cwd();

            // Try up to 5 levels up to find config directory
            for (let i = 0; i < 5; i++) {
                const testPath = join(searchDir, 'config');
                try {
                    await readFile(join(testPath, 'system_prompt_sdk.md'), 'utf-8');
                    configDir = testPath;
                    break;
                } catch {
                    // Not here, go up one level
                    searchDir = join(searchDir, '..');
                }
            }

            if (configDir) {
                const systemPromptPath = join(configDir, 'system_prompt_sdk.md');
                const rawPrompt = await readFile(systemPromptPath, 'utf-8');

                sendStatus('system_prompt_processing', {
                    message: 'Processing @import statements in system prompt...',
                    raw_length: rawPrompt.length
                });

                // Resolve @import statements recursively
                customSystemPrompt = await resolveImports(rawPrompt, configDir);

                sendStatus('system_prompt_loaded', {
                    message: `Custom system prompt loaded and imports resolved`,
                    prompt_length: customSystemPrompt.length,
                    raw_length: rawPrompt.length,
                    expansion: `${((customSystemPrompt.length / rawPrompt.length) * 100).toFixed(0)}%`
                });
            } else {
                sendStatus('system_prompt_default', {
                    message: 'No custom system prompt found (searched up to 5 directories), using SDK default (empty)'
                });
            }
        } catch (error) {
            // File doesn't exist or can't be read - that's okay, use SDK default
            sendStatus('system_prompt_default', {
                message: `Error loading system prompt: ${error.message}, using SDK default (empty)`
            });
        }

        // Build SDK options
        const sdkOptions = {
            cwd: cwd || process.cwd(),
            // Enable streaming events (REQUIRED for real-time streaming)
            includePartialMessages: true,
            // Disable all tools for roleplay mode
            // This prevents the SDK from adding tool documentation to the system prompt
            allowedTools: [],
            // Allow reading from config/guidelines directory (if we found configDir during system prompt loading)
            // This enables Claude to reference guideline files during conversation
            allowedPaths: configDir ? [
                cwd || process.cwd(),  // RP directory
                configDir,              // config/ directory
                join(configDir, 'guidelines')  // config/guidelines/ directory
            ] : undefined,
            ...options
        };

        // Log allowed paths for debugging
        if (sdkOptions.allowedPaths) {
            sendStatus('debug', {
                message: 'Configured allowed paths for file access',
                paths: sdkOptions.allowedPaths
            });
        }

        // Add custom system prompt if loaded
        if (customSystemPrompt) {
            sdkOptions.systemPrompt = customSystemPrompt;
            sendStatus('debug', {
                message: 'System prompt added to SDK options',
                prompt_preview: customSystemPrompt.substring(0, 100) + '...'
            });
        }

        // Only use SDK session management if we DON'T have conversation_history
        // If we have conversation_history, we're managing state from disk ourselves
        if (!conversation_history || conversation_history.length === 0) {
            sdkOptions.resume = session_id || currentSessionId;
            sdkOptions.continue = !!currentSessionId;
            sendStatus('debug', {
                message: 'Using SDK session management',
                resume: sdkOptions.resume,
                continue: sdkOptions.continue
            });
        } else {
            sendStatus('debug', {
                message: 'NOT using SDK session management (conversation_history provided)',
                history_length: conversation_history.length
            });
        }

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
        let hasStreamedChunks = false;

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
                            hasStreamedChunks = true;
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
        // If we streamed chunks, don't send content again (it's already been sent)
        // If we didn't stream, send the full response (fallback for non-streaming responses)
        const responseContent = hasStreamedChunks ? '' : fullResponse;

        sendResponse(responseContent, lastUsage, {
            session_id: newSessionId || currentSessionId,
            message_count: conversationHistory.length,
            total_length: fullResponse.length,
            streamed: hasStreamedChunks
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
