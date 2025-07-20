#!/bin/bash

# Script to revert score_form.html to commit 72eb1c80f1a3e127cad0557af58d48302872d09a

echo "Reverting templates/score_form.html to commit 72eb1c80f1a3e127cad0557af58d48302872d09a..."

# Navigate to the git repository
cd /Users/mattortiz/Code/spades

# Check out the specific version of the file
git checkout 72eb1c80f1a3e127cad0557af58d48302872d09a -- templates/score_form.html

# Check the status
echo "File reverted. Current git status:"
git status

echo "Revert complete!"
