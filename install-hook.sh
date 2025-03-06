#!/bin/bash

# Create the hooks directory if it doesn't exist
mkdir -p .git/hooks

# Install the pre-commit hook
echo "Installing pre-commit hook..."
cp pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

echo "Git hook installed successfully!"
echo "Now, every time you make a commit, a text file with the current date and time in the filename will be created and added to the repository."