# How to Enable Iteration Field for Sprints

## Quick Steps

1. **Go to your GitHub project:**
   - Open: https://github.com/mohithgowdak/projects/0
   - Or navigate to: Your Profile → Projects → Machine Learning Fundamentals

2. **Open Project Settings:**
   - Click the **gear icon (⚙️)** or **"..." menu** in the top right
   - Select **"Settings"** or **"Project settings"**

3. **Add Iteration Field:**
   - In the left sidebar, click **"Fields"**
   - Click **"New field"** button
   - Select **"Iteration"** from the field type dropdown
   - Name it **"Sprint"** (or "Iteration")
   - Click **"Save"**

4. **Verify:**
   - The iteration field should now appear in your project
   - You can now create sprints programmatically

## Alternative: Via Project Board

1. Go to your project board
2. Click the **"+"** button next to column headers
3. Select **"New field"**
4. Choose **"Iteration"** type
5. Name it and save

## Why This is Needed

GitHub Projects v2 iteration fields are special system fields that may not be creatable via the GraphQL API in all cases. Enabling them manually ensures they're properly configured for your project.

After enabling the iteration field, try creating your sprint again!


