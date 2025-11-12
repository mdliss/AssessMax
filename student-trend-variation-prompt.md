# Task: Add Realistic Variation to Student Assessment Trend Data

## Problem Statement

Currently, the synthetic data generation in `backend/populate_data.py` creates student assessment history records where each student's skill scores remain constant across all time periods. This results in flat horizontal trend lines in the visualization, which is unrealistic and doesn't demonstrate the system's trend analysis capabilities.

## Objective

Modify the data population script to generate **realistic, varied assessment scores over time** for each student, simulating actual learning progression patterns that educators would observe in real classroom settings.

## Requirements

### 1. Score Variation Patterns

Each student should have scores that vary over time in realistic ways:

- **Natural fluctuation**: Scores should not be perfectly linear but should show natural ups and downs that reflect real student performance
- **Overall trajectories**: Some students should show improvement over time, some should show decline, and some should remain relatively stable with minor variations
- **Skill-specific patterns**: Different skills (empathy, adaptability, collaboration, communication, self_regulation) should have independent variation patterns for each student
- **Realistic ranges**: Scores should stay within reasonable bounds (typically 1-5 or 1-10 scale, depending on your assessment model)

### 2. Student Archetypes

Create diverse student profiles to represent realistic classroom scenarios:

- **Improvers** (30-40% of students): Start with lower scores and show gradual improvement over the 6-month period
- **High Performers** (20-30%): Start with high scores and maintain them with minor fluctuations
- **Struggling Students** (15-20%): Start with lower scores and either stay flat or show slight decline
- **Volatile Learners** (15-20%): Show significant ups and downs, representing students who have inconsistent performance
- **Late Bloomers** (10-15%): Start flat or declining, then show significant improvement in the latter half of the timeline

### 3. Temporal Realism

- **Weekly/Bi-weekly assessments**: Generate data points at regular intervals (every 1-2 weeks) over the 6-month period
- **Seasonal effects**: Consider that performance might dip slightly before breaks or show improvement after targeted interventions
- **Momentum**: If a student is improving, they should generally continue improving (with occasional setbacks) rather than randomly jumping between high and low scores
- **Correlation between skills**: Related skills (e.g., collaboration and communication) might show some correlation in their trends, though not perfect correlation

### 4. Implementation Guidelines

The data generation should:

1. **For each student**, determine their archetype (improver, high performer, etc.)
2. **For each skill** for that student, generate a base starting score appropriate to their archetype
3. **For each time point** (assessment date), calculate the score by:
   - Taking the previous score as a baseline
   - Adding a trend component (positive for improvers, negative for declining, minimal for stable)
   - Adding random noise (small fluctuations of ±0.3 to ±0.8 points)
   - Ensuring the score stays within valid bounds
   - Applying some smoothing so changes aren't too abrupt

4. **Maintain data consistency**:
   - Each assessment record should still link properly to the student and include all required metadata
   - The existing class aggregate calculations should still work correctly
   - Database constraints should be satisfied

5. **Preserve existing functionality**:
   - Don't break the current data model or schema
   - Ensure upload jobs, class aggregates, and evidence records are still created appropriately
   - The momentum metrics, trajectory calculations, and stability ranges in the frontend should now show meaningful values

## Expected Outcome

After this change, when viewing the Trends page:

- **Class mode**: Should show 5 skill lines (one per skill) that represent the averaged trajectories across all students, with realistic variation showing the class's overall trends
- **Student mode**: Should show 5 skill lines for an individual student that vary over time, clearly demonstrating whether the student is improving, struggling, or maintaining performance in each skill area
- **Momentum metrics**: Should display meaningful values (not all zeros or nulls) reflecting actual trend directions
- **Trajectory**: Should show "Upward", "Stable", or "Downward" based on the actual data patterns
- **Stability Range**: Should reflect the actual variation in the data

## Files to Modify

Primary file: `/Users/max/AssessMax/backend/populate_data.py`

Focus on the section that creates Assessment records and generates skill scores. Look for where scores are currently set to fixed values and replace that logic with the variation algorithm described above.

## Testing Validation

After implementation, verify:

1. Run the script and check that it completes without errors
2. View the Trends page in both class and student modes
3. Confirm that trend lines show realistic variation (not flat, not completely random)
4. Check that different students show different patterns
5. Verify that the momentum metrics and trajectory indicators display meaningful values
6. Ensure switching between different students shows different trend patterns

## Additional Considerations

- Use appropriate random seed management if you want reproducible "random" data for testing
- Consider adding comments in the code explaining the archetype distribution and variation logic
- Document any new constants (like variation ranges, trend strengths) so they can be easily adjusted
- Ensure the variation algorithm is efficient enough to generate 6 months of data for multiple students quickly (under 10 seconds total)
