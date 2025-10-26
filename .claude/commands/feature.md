Start feature: $ARGUMENTS

**Autonomous Workflow Protocol:**

1. **Check current state:**
   - Read `.autonomous/state.json`
   - If status is not IDLE, report conflict

2. **Planning phase (if IDLE):**
   - Update state: `{"status": "PLANNING", "task": "$ARGUMENTS"}`
   - Use `system-architect` agent to:
     - Analyze feature requirements
     - Design architecture
     - Identify components needed (frontend, backend, database)
     - Create implementation plan
   - Wait for plan approval

3. **Implementation phase (after approval):**
   - Update state: `{"status": "READY"}`
   - Then update: `{"status": "BUILDING"}`
   - Use specialized agents in parallel:
     - `frontend-engineer` for UI components
     - `backend-engineer` for API/database logic
   - Update state with progress

4. **Testing phase:**
   - Update state: `{"status": "TESTING"}`
   - Use `qa-engineer` to:
     - Run all tests
     - Validate functionality
     - Check for regressions

5. **Review phase:**
   - Use `code-reviewer` to:
     - Review code quality
     - Check security
     - Validate standards compliance

6. **Completion:**
   - Update state: `{"status": "DONE", "next": "Feature complete and approved"}`
   - Report success to user

**CRITICAL:** Follow state transitions. Update `.autonomous/state.json` after each phase.
