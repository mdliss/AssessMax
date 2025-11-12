# Task: Implement Trend Chart in Student Detail Assessment History Section

## Problem Statement

The Student Detail page (`/student-detail`) has an "Assessment History" section that currently displays placeholder text "Trend chart placeholder" instead of an actual visualization. This section is intended to show a student's skill progression over time but was never fully implemented.

## Context

The application already has:
- A working **Trends page** (`/trends`) that shows multi-student trend analysis using Chart.js
- A working **Radar Chart** component on Student Detail that shows current skill snapshot
- Student assessment history data available from the backend API endpoint `/v1/assessments/{student_id}/history`

## Objective

Replace the placeholder text with a **functional trend line chart** that visualizes the selected student's skill progression over time across all five skills (empathy, adaptability, collaboration, communication, self_regulation).

## Requirements

### 1. Frontend Implementation

**File to modify**: `/Users/max/AssessMax/frontend/src/routes/(app)/student-detail/+page.svelte`

**Location**: Around line 415-417, the section that currently contains:
```html
<div class="h-[320px] rounded-xl border border-[color:var(--border-color)] flex items-center justify-center text-muted">
  Trend chart placeholder
</div>
```

**What to implement**:
1. Create or reuse a Chart.js line chart component similar to the one on the Trends page
2. The chart should:
   - Display all 5 skills as separate colored lines
   - Show assessment dates on the x-axis
   - Show skill scores (0-100 scale) on the y-axis
   - Use the same color scheme as the Trends page for consistency:
     - Empathy: one color
     - Adaptability: another color
     - Collaboration: another color
     - Communication: another color
     - Self-regulation: another color
3. Fetch data from the student's assessment history (which is already being loaded on this page)
4. Handle the case where there's no history data (show "No assessment history available" message)
5. Make the chart responsive and match the design system (use existing pulse-card styling)

### 2. Data Requirements

**The chart needs assessment history data over time**. This data should come from:
- The existing API endpoint: `/v1/assessments/{student_id}/history`
- This endpoint should return an array of assessments ordered by date
- Each assessment should include:
  - Date/timestamp
  - Skill scores (all 5 skills)

**Current state**: The page likely already fetches some assessment data, but verify it includes historical assessments, not just the most recent one.

### 3. Backend Data Population (if needed)

**File**: `/Users/max/AssessMax/backend/populate_data.py`

**Verify the populate script creates**:
- Multiple assessment records per student spread over time (e.g., weekly assessments over 6 months)
- Each assessment should have all 5 skill scores
- Assessments should be properly dated with realistic timestamps
- The assessment history should show the varied trends (not flat lines - this is addressed in the separate "student-trend-variation-prompt.md")

**If the populate script doesn't create enough historical assessments**:
- Ensure each student gets assessments at regular intervals (e.g., every 1-2 weeks)
- Ensure the `/v1/assessments/{student_id}/history` endpoint returns these historical records correctly

### 4. API Endpoint Verification

**Endpoint**: `GET /v1/assessments/{student_id}/history`

**Should return**: Array of assessment objects with structure like:
```json
[
  {
    "assessment_id": "uuid",
    "student_id": "uuid",
    "date": "2024-06-15T10:00:00Z",
    "skills": [
      { "skill": "empathy", "score": 78.5 },
      { "skill": "adaptability", "score": 82.3 },
      { "skill": "collaboration", "score": 75.8 },
      { "skill": "communication", "score": 80.1 },
      { "skill": "self_regulation", "score": 77.9 }
    ]
  },
  // ... more assessments over time
]
```

**Verify**: This endpoint is already implemented and returns data in the correct format. Check the backend router files in `/Users/max/AssessMax/backend/app/assessments/` to confirm.

## Implementation Steps

### Step 1: Check Data Availability
1. Open the Student Detail page in a browser with dev tools
2. Check network tab for API calls to see what assessment data is being fetched
3. Verify the response includes historical assessments (multiple records over time)
4. If only getting one assessment, check the API endpoint implementation

### Step 2: Frontend Chart Component
1. In the Student Detail page component, add state/variables to store assessment history
2. Transform the history data into Chart.js format (arrays of dates and scores)
3. Replace the placeholder div with a Chart.js canvas element (similar to Trends page implementation)
4. Add the chart rendering logic (can reference `/Users/max/AssessMax/frontend/src/routes/(app)/trends/+page.svelte` for examples)
5. Handle loading state and empty data state with appropriate messages

### Step 3: Styling and Polish
1. Ensure the chart uses the same color scheme as other charts in the app
2. Add tooltips showing exact values on hover
3. Make sure the chart is responsive and looks good on different screen sizes
4. Ensure it follows the app's design system (matches other pulse-cards and charts)

### Step 4: Testing
1. Select different students and verify their individual trend lines display correctly
2. Verify students with different trend patterns (improving, declining, stable) show appropriately
3. Check that the chart updates when switching between students
4. Test edge cases (students with only one assessment, students with no assessments)

## Expected Outcome

After implementation:
- The "Trend chart placeholder" text is replaced with a working line chart
- The chart shows the selected student's skill progression over time
- Each of the 5 skills is represented as a separate colored line
- The visualization is consistent with the design of other charts in the application
- Users can hover over data points to see exact values and dates
- The chart gracefully handles cases where there is limited or no data

## Notes

- **Reuse code**: The Trends page already has a working Chart.js implementation - reuse as much of that logic as possible
- **Data source**: Make sure you're using the assessment history data, not just the latest assessment
- **Color consistency**: Use the same color mapping for skills that's used on the Trends page
- **Performance**: If a student has many assessments (100+), consider only showing the most recent 50-100 data points to keep the chart readable

## Files Reference

Primary files to work with:
- Frontend: `/Users/max/AssessMax/frontend/src/routes/(app)/student-detail/+page.svelte`
- Backend populate script: `/Users/max/AssessMax/backend/populate_data.py`
- API router (for verification): `/Users/max/AssessMax/backend/app/assessments/router.py`
- Trends page (for reference): `/Users/max/AssessMax/frontend/src/routes/(app)/trends/+page.svelte`
