# Temporary Smart Card Bypass - Development Only

## Overview
A temporary bypass has been added to allow access to the patient dashboard without requiring a smart card reader. This is for development purposes only.

## What Was Changed
Modified file: `src/pages/HomePage/HomePage.tsx`

### Changes Made:
1. **Added `handleBypassLogin` function** (lines 70-107)
   - Directly fetches patient data from FHIR server without card reading
   - Accepts a patient ID as parameter
   - Performs same authentication and navigation as normal card flow

2. **Added bypass button to UI** (lines 143-172)
   - Clearly marked as "Development Only"
   - Styled with amber/warning colors to indicate temporary nature
   - Hardcoded to access patient ID "002"

## How to Use
1. Make sure your FHIR server is running
2. Navigate to the homepage (root `/`)
3. Click the **"DEV: Quick Access Patient 002 (Priya Sharma)"** button
4. You will be logged in and redirected to patient 002's dashboard

**Note**: The patient ID in the database is `patient-002` (with the "patient-" prefix), not just `002`.

## How to Remove This Bypass (When You Get Your Card Reader)

### Option 1: Remove the bypass button only
Delete lines 143-172 in `src/pages/HomePage/HomePage.tsx` (the UI button and divider)

### Option 2: Remove all bypass code
1. Delete the `handleBypassLogin` function (lines 70-107)
2. Delete the bypass button UI (lines 143-172)

### Quick Git Command to See Changes
```bash
git diff src/pages/HomePage/HomePage.tsx
```

## Security Note
⚠️ **IMPORTANT**: This bypass should NEVER be deployed to production. It completely bypasses the smart card authentication mechanism and should only be used in local development environments.

## Patient IDs Available
- Patient 002 (currently hardcoded in the bypass button)
- You can modify the patient ID in the `handleBypassLogin('002')` call if you need to access other patients

---
**Created**: 2025-12-21  
**Purpose**: Temporary development access while smart card reader is unavailable
