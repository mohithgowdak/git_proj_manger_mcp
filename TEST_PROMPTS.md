# Test Prompts for AI Features - GitHub Project Manager MCP

This document contains ready-to-use prompts for testing all AI-powered features in Cursor. Copy and paste these prompts into Cursor's chat to test the MCP server functionality.

## 🎯 Basic Project Management Tests

### 1. List All Projects
```
List all GitHub projects for the repository
```

### 2. Create a New Project
```
Create a new GitHub project called "AI Learning Project" with description "A project to track AI/ML learning progress" for owner mohithgowdak with private visibility
```

### 3. Get Project Details
```
Get details of the project with ID [PROJECT_ID]
```

---

## 🤖 AI-Powered Feature Tests

### 4. Create Roadmap (AI-Powered Planning)
```
Create a roadmap for a project called "Machine Learning Fundamentals" with the following milestones:
- Milestone 1: "Foundation Setup" (due in 2 weeks) - includes issues for setting up Python environment, installing libraries, and creating project structure
- Milestone 2: "Core Concepts" (due in 4 weeks) - includes issues for learning supervised learning, unsupervised learning, and neural networks
- Milestone 3: "Practical Projects" (due in 6 weeks) - includes issues for building a classification model, a regression model, and a neural network

Make it a private project for mohithgowdak
```

### 5. Plan Sprint with AI Assistance
```
Plan a new sprint titled "Week 1 - Foundation" starting from 2025-01-15 and ending on 2025-01-22 with the following goals:
- Set up development environment
- Complete initial project setup
- Review project requirements

Include issues with IDs: [ISSUE_ID_1, ISSUE_ID_2]
```

### 6. Get Sprint Metrics
```
Get metrics for sprint [SPRINT_ID] including all issues
```

### 7. Get Milestone Metrics
```
Get progress metrics for milestone [MILESTONE_ID] including all related issues
```

### 8. Find Overdue Milestones
```
Get all overdue milestones, limit to 10, and include their issues
```

### 9. Find Upcoming Milestones
```
Get upcoming milestones within the next 30 days, limit to 5, and include their issues
```

---
## done till here. 
## 📋 Issue Management Tests   

### 10. Create an Issue
```
Create a new issue titled "Implement User Authentication" with description "Add JWT-based authentication system with login, logout, and token refresh capabilities" with high priority and type "feature"
```

### 11. List All Issues
```
List all open issues for the project, sorted by priority
```

### 12. Get Issue Details
```
Get full details of issue [ISSUE_ID]
```

### 13. Update Issue Status
```
Update issue [ISSUE_ID] to status "in_progress"
```

---

## 🏷️ Labels and Organization

### 14. Create Labels
```
Create labels for the project:
- "bug" (red color, description: "Something isn't working")
- "enhancement" (blue color, description: "New feature or request")
- "documentation" (green color, description: "Documentation improvements")
- "ai-feature" (purple color, description: "AI-powered feature")
```

### 15. List All Labels
```
List all labels in the repository
```

---

## 📊 Project Fields and Views

### 16. Create Custom Project Field
```
Create a custom field called "Complexity" of type "single_select" with options: "Low", "Medium", "High", "Critical" for project [PROJECT_ID]
```

### 17. List Project Fields
```
List all fields for project [PROJECT_ID]
```

### 18. Create Project View
```
Create a new board view called "Sprint Board" for project [PROJECT_ID]
```

### 19. List Project Views
```
List all views for project [PROJECT_ID]
```

---

## 🔗 Project Items Management

### 20. Add Issue to Project
```
Add issue [ISSUE_ID] to project [PROJECT_ID] as a project item
```

### 21. List Project Items
```
List all items in project [PROJECT_ID], limit to 20
```

### 22. Set Field Value
```
Set the "Complexity" field to "High" for project item [ITEM_ID] in project [PROJECT_ID]
```

### 23. Get Field Value
```
Get the value of "Complexity" field for project item [ITEM_ID] in project [PROJECT_ID]
```

---

## 🎯 Advanced Workflow Tests

### 24. Complete Project Setup Workflow
```
1. Create a new project called "AI Learning Journey"
2. Create a milestone "Week 1 - Getting Started" due in 7 days
3. Create 3 issues:
   - "Set up Python environment" (high priority)
   - "Install required libraries" (medium priority)
   - "Create project structure" (medium priority)
4. Add all issues to the project
5. Create a sprint "Sprint 1" starting today, ending in 7 days
6. Add all issues to the sprint
```

### 25. Project Cleanup
```
Delete project [PROJECT_ID] after confirming it's no longer needed
```

---
### tested till here

## 📝 AI Feature Testing Prompts (When AI Tools Are Available)

### 26. Generate PRD (Product Requirements Document)
```
Generate a comprehensive PRD for a project idea: "AI-powered personal learning assistant that tracks learning progress, recommends courses, and provides personalized study plans"

Project name: "LearnAI Assistant"
Author: "mohithgowdak"
Complexity: "high"
Timeline: "3 months"
Include market research: true
```

### 27. Parse PRD and Generate Tasks
```
Parse the following PRD content and generate actionable development tasks:
[PASTE PRD CONTENT HERE]

Maximum tasks: 30
Create traceability matrix: true
Include use cases: true
Project ID: [PROJECT_ID]
```

### 28. Analyze Task Complexity
```
Analyze the complexity of this task:
Title: "Implement real-time collaboration features"
Description: "Build WebSocket-based real-time collaboration system with conflict resolution and presence indicators"
Team experience: "mixed"
Include breakdown: true
Include risks: true
```

### 29. Get Next Task Recommendations
```
Recommend the next tasks for our team:
Sprint capacity: 40 hours
Team skills: ["python", "machine-learning", "tensorflow", "pytorch"]
Maximum complexity: 7
Include analysis: true
```

### 30. Expand Complex Task
```
Expand this complex task into subtasks:
Title: "Build Machine Learning Pipeline"
Description: "Create end-to-end ML pipeline with data preprocessing, model training, evaluation, and deployment"
Current complexity: 8
Target complexity: 3
Include estimates: true
Include dependencies: true
```

### 31. Add Feature with AI Analysis
```
Add a new feature to the project:
Feature idea: "Automated Model Retraining"
Description: "System that automatically retrains ML models when new data is available or performance degrades"
Requested by: "data-science-team"
Business justification: "Improve model accuracy over time and reduce manual intervention"
Target users: ["data-scientists", "ml-engineers"]
Auto-approve: true
Expand to tasks: true
Create lifecycle: true
```

### 32. Enhance PRD
```
Enhance the existing PRD with gap analysis and improvements:
[PASTE PRD CONTENT HERE]

Include market research: true
Validate completeness: true
```

### 33. Create Traceability Matrix
```
Create a comprehensive traceability matrix for project [PROJECT_ID]:
PRD Content: [PASTE PRD CONTENT]
Features: [LIST FEATURES]
Tasks: [LIST TASKS]
Validate completeness: true
```

---

## 🔍 Testing Tips

1. **Start Simple**: Begin with basic operations like listing projects and creating issues
2. **Use Real IDs**: Replace `[PROJECT_ID]`, `[ISSUE_ID]`, etc. with actual IDs from your repository
3. **Test Incrementally**: Test one feature at a time to isolate any issues
4. **Check Results**: Verify that operations complete successfully and data is created/updated correctly
5. **Test Error Cases**: Try invalid IDs or missing parameters to test error handling

## 📌 Quick Reference

**Available MCP Tools:**
- `create_project` - Create new GitHub project
- `list_projects` - List all projects
- `create_milestone` - Create project milestone
- `create_issue` - Create GitHub issue
- `create_sprint` - Plan a sprint
- `create_roadmap` - AI-powered roadmap creation
- `plan_sprint` - Plan sprint with issues
- `get_milestone_metrics` - Get milestone progress
- `get_sprint_metrics` - Get sprint metrics
- `create_label` - Create repository labels
- `create_project_field` - Add custom fields
- `create_project_view` - Create project views
- `add_project_item` - Add items to project
- `set_field_value` - Set custom field values

**Note**: Some AI features mentioned in the README (like `generate_prd`, `parse_prd`, `analyze_task_complexity`) may require the AI service implementation to be fully connected. Test with the available MCP tools first, then verify AI features if they're implemented.



