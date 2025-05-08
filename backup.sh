#!/usr/bin/env bash
git checkout -b backup
git add .
git commit -m "Backup on $(date +%Y-%m-%d)"
git push origin backup
git checkout main