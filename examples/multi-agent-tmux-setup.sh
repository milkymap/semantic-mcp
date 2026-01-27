#!/bin/bash
# Multi-Agent Claude Code Setup via tmux
#
# This script sets up two Claude Code instances that can communicate
# via tmux send-keys, enabling coordinated work on complex tasks.
#
# Pattern: REQ/REP communication between named tmux sessions
# Use cases: Divide work, share findings, parallel exploration

set -e

SESSION_A="${1:-dante}"
SESSION_B="${2:-vergil}"

echo "=== Multi-Agent Claude Code Setup ==="
echo "Creating sessions: $SESSION_A and $SESSION_B"
echo ""

# Check if tmux is available
if ! command -v tmux &> /dev/null; then
    echo "Error: tmux is required but not installed."
    exit 1
fi

# Check if claude is available
if ! command -v claude &> /dev/null; then
    echo "Error: claude CLI is required but not installed."
    exit 1
fi

# Create first session
if tmux has-session -t "$SESSION_A" 2>/dev/null; then
    echo "Session '$SESSION_A' already exists"
else
    echo "Creating session '$SESSION_A'..."
    tmux new-session -d -s "$SESSION_A"
fi

# Create second session
if tmux has-session -t "$SESSION_B" 2>/dev/null; then
    echo "Session '$SESSION_B' already exists"
else
    echo "Creating session '$SESSION_B'..."
    tmux new-session -d -s "$SESSION_B"
fi

# Start Claude in both sessions
echo ""
echo "Starting Claude Code in both sessions..."
tmux send-keys -t "$SESSION_A" "claude" Enter
tmux send-keys -t "$SESSION_B" "claude" Enter

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To attach to sessions:"
echo "  tmux attach -t $SESSION_A"
echo "  tmux attach -t $SESSION_B"
echo ""
echo "Communication protocol (from either Claude instance):"
echo "  Send message:  tmux send-keys -t <other_session> \"message\""
echo "  Press enter:   tmux send-keys -t <other_session> Enter"
echo ""
echo "Example (from $SESSION_A to $SESSION_B):"
echo "  tmux send-keys -t $SESSION_B \"Hello from $SESSION_A\""
echo "  tmux send-keys -t $SESSION_B Enter"
echo ""
echo "Tip: Introduce the agents to each other by telling each one"
echo "about the other session name and the communication pattern."
