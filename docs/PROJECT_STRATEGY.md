# ArchiAI — Project Strategy Document

> **Version:** 1.0
> **Date:** 2026-05-23
> **Status:** Active — MVP Planning Phase

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Problem Statement](#2-problem-statement)
3. [Business Opportunity](#3-business-opportunity)
4. [Core Product Features](#4-core-product-features)
5. [Requirements](#5-requirements)
6. [3D Canvas Requirement](#6-3d-canvas-requirement)
7. [AI / Layout Generation Requirement](#7-ai--layout-generation-requirement)
8. [Web Scraper and Training Data Pipeline](#8-web-scraper-and-training-data-pipeline)
9. [Collaboration, Version Control, Auto-save, and Logging](#9-collaboration-version-control-auto-save-and-logging)
10. [Agile Workflow](#10-agile-workflow)
11. [User Stories](#11-user-stories)
12. [Sprint Roadmap](#12-sprint-roadmap)
13. [Recommended Tech Stack](#13-recommended-tech-stack)
14. [Recommended Project Structure](#14-recommended-project-structure)
15. [Recommended Database Models](#15-recommended-database-models)
16. [API Plan](#16-api-plan)
17. [Technical Workflow](#17-technical-workflow)
18. [MVP Scope](#18-mvp-scope)
19. [Future Scope](#19-future-scope)
20. [Development Rules](#20-development-rules)
21. [Post-Strategy Summary](#21-post-strategy-summary)

---

## 1. Product Overview

### What is ArchiAI?

ArchiAI is an AI-powered architectural design platform that converts natural language design briefs into interactive 3D architectural layouts. Users describe what they want — a three-bedroom apartment, a small office with an open floor plan, a studio with a rooftop terrace — and ArchiAI generates a structured 3D layout that they can view, edit, refine, and export directly in the browser.

Unlike traditional CAD or BIM tools that require years of learning, ArchiAI is designed to be usable by anyone. Non-technical users get a fast, visual concept. Professionals get a rapid first draft they can refine. Teams get a shared workspace with version history and accountability.

### Problem It Solves

Architectural concept generation today is slow, expensive, and inaccessible. A homeowner wanting to visualise a renovation idea either hires a professional or struggles with complex tools they were never trained on. A student working on a design project starts from scratch every time. A small construction firm spends hours on early-stage layout sketches that may never be used. ArchiAI removes this friction by making concept-level architectural planning fast, visual, and collaborative — in minutes, not days.

### Why It Is Useful

- Generates a spatial layout directly from plain language — no prior design knowledge required
- Provides an interactive 3D canvas so users see what they are getting and can adjust it immediately
- Supports team-based project work with version history, change logs, and role-based access
- Creates a starting point that professionals can refine, not a toy that replaces professional work
- Reduces the cost of early-stage design exploration for small businesses, homeowners, and students

### Target Users

| Persona | Core Use Case |
|---|---|
| Architecture students | Fast layout prototypes for coursework and portfolio projects |
| Freelance architects | Rapid first-draft concepts to share with clients |
| Interior designers | Space planning and room arrangement visualisation |
| Homeowners | Visualise renovation or extension ideas before hiring professionals |
| Real estate developers | Concept-level site layout planning for early feasibility |
| Small construction firms | Fast layout sketching before formal drawings begin |
| Design agencies | Team-based concept exploration with shared workspaces |

### Business Opportunity

The global architecture software market is valued at over $2.5 billion and growing. The total addressable market expands significantly when non-professional users — homeowners, small developers, students — are included. Existing tools like AutoCAD, Revit, and SketchUp dominate the professional segment but are inaccessible to the wider market. ArchiAI targets the underserved segment: users who need concept-level output fast without a steep learning curve or high price point.

The freemium SaaS model allows low-friction acquisition. The paid tiers monetise power users, teams, and professional workflows. As the AI generation quality improves and the platform adds export formats and integrations, it moves upmarket toward professional and enterprise customers.

### Product Vision

ArchiAI becomes the fastest way to go from an idea to a visual architectural concept. It democratises early-stage design by removing the barrier of technical skill and expensive tooling. Over time, ArchiAI evolves from a concept generator into a full lightweight design platform, supporting professionals and non-professionals alike — with AI assistance, team collaboration, version control, and export capabilities built in from day one.

### MVP Version

The MVP delivers the core loop:

1. Register and log in
2. Create a project
3. Enter a natural language design brief
4. Receive a basic 3D layout rendered in the browser
5. Select and move rooms/components using mouse drag-and-drop and transform controls
6. Save the project with auto-save and basic version history
7. View activity logs

The MVP proves the value proposition: prompt in, 3D layout out, editable in the browser.

### Future Full-Scale Version

The full product adds real-time multi-user collaboration, AI model improvement from collected data, advanced 3D editing, multi-floor buildings, interior design suggestions, subscription billing, premium exports (PDF, CAD, BIM-ready formats), a public template marketplace, and mobile support.

---

## 2. Problem Statement

### Creating Initial Architectural Concepts Takes Time

Early-stage layout planning — even at concept level — requires significant manual effort. Architects and designers spend hours on first drafts that clients may immediately reject. Students restart from scratch for every project. ArchiAI generates the first draft in seconds.

### Non-Technical Users Cannot Visualise Design Ideas

A homeowner with a renovation idea has no practical way to visualise it without hiring a professional or learning complex software. ArchiAI gives non-technical users an immediate visual output from plain language input.

### Early-Stage Layout Planning Is Expensive

Hiring an architect for concept-level sketches costs money many clients cannot justify for exploratory work. ArchiAI makes early-stage concept generation affordable — even free at entry level.

### Existing Tools Are Complex and Inaccessible for Beginners

AutoCAD, Revit, and SketchUp are powerful but require significant training. Tools like Floorplanner and RoomSketcher are simpler but still require manual drawing. ArchiAI's prompt-first approach removes the learning curve entirely for concept generation.

### Designers Need Faster Ways to Create First Drafts

Even experienced designers waste time on exploratory first drafts. ArchiAI provides a starting point that professionals can refine rather than build from zero.

### Students and Small Teams Need Affordable Tools

Architecture students and small teams need concept-generation tools that do not require expensive software licenses or long onboarding. ArchiAI's free tier addresses this directly.

### Team-Based Design Work Lacks Proper Version Control and Documentation

When multiple people work on a design project, tracking who changed what and why is difficult in most current tools. ArchiAI builds version control, activity logs, and change documentation into the core product from the start.

---

## 3. Business Opportunity

### Monetisation Model

ArchiAI follows a freemium SaaS model. The free tier provides enough value to attract and retain casual users. Paid tiers unlock features that power users and professionals need.

#### Free Plan
- Up to 3 projects
- Basic layout generation (limited prompts per month)
- Basic 3D canvas viewing and editing
- Standard export (image only)
- Community support

#### Student Plan — $5/month
- Up to 10 projects
- More AI generation credits
- PDF export
- Basic version history
- Priority support

#### Professional Plan — $19/month
- Unlimited projects
- Full AI refinement credits
- All export formats
- Full version history and activity logs
- Shareable project links

#### Team/Agency Plan — $49/month per workspace
- Everything in Professional
- Up to 10 members per workspace
- Team activity history
- Role-based permissions (Owner, Admin, Editor, Viewer)
- Workspace-level project dashboard

#### Enterprise Plan — Custom pricing
- Unlimited members
- Custom AI generation credits
- API access
- SLA and dedicated support
- On-premise deployment option (future)

### Additional Monetisation Paths

| Path | Description |
|---|---|
| Pay-per-export | CAD/BIM-ready export as a one-time purchase |
| AI credit top-ups | Purchase additional generation credits |
| Template marketplace | Buy or sell community layout templates |
| Partner integrations | Revenue sharing with construction, real estate, or furniture platforms |
| White-label licensing | License the platform to architecture schools or firms |

### Market Positioning

ArchiAI enters the market as the fastest and most accessible concept-generation tool for architectural layout planning. It is not trying to replace Revit or AutoCAD. It is targeting the concept phase — the phase that currently has no good tool for non-professionals and no fast tool for professionals.

---

## 4. Core Product Features

### User Account Features

- Register with email and password
- Login / Logout
- Forgot password and password reset flow
- User profile (name, avatar, bio, plan tier)
- Saved projects dashboard
- Account settings (email, password, notification preferences)

### Workspace / Team Features

- Create a workspace/team
- Invite members by email
- Manage member roles: Owner, Admin, Editor, Viewer
- Remove members
- Team project dashboard (shared view of all workspace projects)
- Team activity history
- Future: real-time collaborative editing with WebSocket support

### Design Generation Features

- Natural language design brief input
- Requirement extraction from prompt (room types, counts, sizes, relationships)
- Room and floor planning from extracted requirements
- Rule-based layout generation (MVP) with AI-assisted generation (future)
- Structured 3D layout JSON output
- Prompt-based design refinement (follow-up prompts improve existing layout)
- Generation status feedback (Loading, Generated, Error)

### 3D Editor Features

- Interactive 3D canvas with Three.js / React Three Fiber
- Orbit, zoom, and pan camera controls
- Click/select rooms and components directly in the canvas
- Move rooms/components with mouse drag-and-drop inside the canvas
- Move objects along X, Y, and Z axes using transform controls / gizmos
- Support both free mouse drag movement and precise inspector-based position editing
- Resize, rotate, duplicate, and delete objects
- Snap objects to grid for clean alignment
- Inspector panel: exact dimensions, position (X/Y/Z), rotation, label editing
- Add and remove walls, doors, windows, stairs, floors, and open spaces
- Smooth and responsive editing experience
- Auto-save canvas changes after major edits

### Project Management Features

- Create project (name, description, type)
- Save project manually
- Auto-save at regular intervals and after major edits
- Load and open existing projects
- Update project metadata
- Delete project
- Duplicate project
- Rename project
- Project thumbnail/preview generation
- Project version history
- Restore previous version

### Logging and Documentation Features

- Activity log for every project
- Log: who, what, when, and optionally why
- Track manual canvas edits (move, resize, rotate, delete, add)
- Track prompt-generated and refined changes
- Track project exports
- Track team and member actions (invite, role change, removal)
- System-level logs for admin and developer monitoring
- Logs include: user ID/name, action type, timestamp, affected object, previous value, new value, optional comment

### Export and Share Features

- Export layout as image (PNG/JPG)
- Export project summary as PDF
- Shareable project link (public or token-protected)
- Future: CAD/BIM-ready export formats (DXF, IFC, etc.)

### Admin / Developer Features

- API health monitoring
- User management (view, suspend, delete)
- Project and workspace management
- Scraper and data pipeline monitoring
- Error log viewer
- Activity log viewer
- AI model improvement tracking

---

## 5. Requirements

### Functional Requirements

- User can register, log in, log out, and manage their account
- User can create, update, delete, duplicate, and manage projects
- User can create or join teams/workspaces
- User can invite members to projects or workspaces
- User can assign and manage member roles: Owner, Admin, Editor, Viewer
- User can enter a natural language architectural design brief
- System extracts layout requirements from the prompt
- System generates a basic 3D architectural layout
- User can view the generated layout in an interactive 3D canvas
- User can click/select objects directly in the 3D canvas
- User can move rooms/components visually using mouse drag-and-drop
- User can edit exact X, Y, and Z position values through an inspector panel
- User can resize, rotate, duplicate, and delete objects in the canvas
- User can save, load, update, delete, and duplicate projects
- System auto-saves project changes at intervals and after major edits
- System displays save status: Saving, Saved, or Error
- User can refine the layout using follow-up prompts
- System stores layout JSON in the database
- System creates a new design version when a layout is saved or regenerated
- System tracks activity logs with user, action, timestamp, object, old/new values
- User can view version history for a project
- User can restore a previous version
- System can export and share design output
- Admin can manage users, projects, teams, API health, scraper status, and AI workflow

### Non-Functional Requirements

- 3D canvas interactions must be smooth and responsive (target 60fps)
- UI must be clean, modern, and intuitive for non-technical users
- Backend must be structured for horizontal scaling
- Authentication must be secure (JWT with refresh tokens or session-based)
- Role-based access control enforced at API level
- All API errors return structured JSON responses with status codes
- Code must be modular: frontend, backend, AI logic, scraper, logging, and collaboration kept separate
- Simple layouts should generate in under 5 seconds
- Database schema must support future real-time features (optimistic locking, change streams)
- Environment variables used for all secrets — no hardcoded credentials
- Local development setup must be straightforward (Docker Compose or equivalent)
- Deployment-ready: containerised, environment-configurable, stateless backend
- Logging must be reliable enough for debugging and team accountability
- Conflict handling must not corrupt project state even when multiple users edit simultaneously

---

## 6. 3D Canvas Requirement

The 3D canvas is the core of the ArchiAI user experience. It is where the generated layout lives and where users improve it. It must feel fast, intuitive, and responsive — not like a CAD tool and not like a game engine viewport.

### Interaction Requirements

| Interaction | Requirement |
|---|---|
| Camera | Orbit (rotate), zoom (scroll), pan (middle mouse / two-finger) |
| Select | Left-click on a room or component to select it |
| Move (visual) | Drag selected object with mouse to reposition it in the canvas |
| Move (precise) | Edit X/Y/Z values in the inspector panel |
| Transform controls | Visible X/Y/Z axis gizmo on selected objects for constrained movement |
| Resize | Drag resize handles or edit W/H/D in inspector |
| Rotate | Rotate handle or edit rotation value in inspector |
| Duplicate | Keyboard shortcut (Ctrl+D) or context menu |
| Delete | Delete key or context menu |
| Snap to grid | Toggle-able grid snapping for clean alignment |
| Add component | Button or panel to add wall, door, window, stair, floor, or open space |
| Deselect | Click on empty canvas area |
| Undo/Redo | Ctrl+Z / Ctrl+Shift+Z (future sprint) |

### Inspector Panel

The inspector panel appears when an object is selected. It shows:

- Object type and label (editable)
- Position: X, Y, Z (editable number fields)
- Dimensions: Width, Height, Depth (editable number fields)
- Rotation: X, Y, Z in degrees (editable number fields)
- Material/colour selector (future)
- Delete and Duplicate buttons

### Auto-save on Canvas Edits

After any significant canvas edit (move, resize, rotate, delete, add), the system queues an auto-save. The save status indicator in the UI shows: Saving → Saved / Error.

### Suggested Implementation Stack

| Concern | Tool |
|---|---|
| 3D rendering | Three.js via React Three Fiber |
| Camera controls | `@react-three/drei` OrbitControls |
| Transform gizmo | `@react-three/drei` TransformControls |
| Drag movement | Custom pointer event handler or DragControls |
| UI overlay | React + Tailwind CSS |
| Canvas state | Zustand store |
| Object selection | Raycasting via Three.js |

---

## 7. AI / Layout Generation Requirement

### Generation Pipeline

```
User prompt input
  → Prompt validation and sanitisation
  → Requirement extraction (room types, counts, sizes, relationships, style, constraints)
  → Floor planning (number of floors, floor dimensions)
  → Room list generation (room names, area estimates, adjacency rules)
  → 2D spatial layout algorithm (room placement, corridor logic, door/window positions)
  → 3D structure conversion (add height, walls, floors, ceilings, stairs)
  → Layout JSON construction
  → Save to database as new Design and DesignVersion
  → Activity log entry for generation action
  → Return layout JSON to frontend
  → Frontend renders 3D canvas from JSON
```

### Requirement Extraction (MVP — Rule-Based)

The MVP uses keyword extraction and pattern matching to identify:
- Number of bedrooms, bathrooms, living spaces, kitchens, offices, etc.
- Approximate total area (if mentioned)
- Building type (apartment, house, office, studio, etc.)
- Style preferences (open plan, compact, etc.)
- Special requirements (rooftop, balcony, garage, etc.)

Future versions replace or augment this with an LLM-based extraction step using the Anthropic Claude API.

### Layout Generation (MVP — Rule-Based)

The MVP uses a deterministic rule-based layout engine:
- Assign standard area estimates per room type
- Place rooms on a grid using a simple packing algorithm
- Apply adjacency rules (kitchen near dining, master bedroom away from living room, etc.)
- Add walls between rooms, doors on shared walls, and windows on external walls
- Output positions, dimensions, and rotations as absolute values

### Layout JSON Schema

```json
{
  "version": "1.0",
  "project_id": "uuid",
  "design_version_id": "uuid",
  "generated_at": "ISO8601 timestamp",
  "metadata": {
    "title": "3 Bedroom Apartment",
    "building_type": "apartment",
    "total_area_sqm": 120,
    "floors": 1,
    "style": "open_plan"
  },
  "floors": [
    {
      "floor_id": "uuid",
      "level": 0,
      "label": "Ground Floor",
      "height": 2.8,
      "rooms": [
        {
          "id": "uuid",
          "type": "bedroom",
          "label": "Master Bedroom",
          "position": { "x": 0, "y": 0, "z": 0 },
          "dimensions": { "width": 4, "height": 2.8, "depth": 5 },
          "rotation": { "x": 0, "y": 0, "z": 0 },
          "material": "default_wall",
          "colour": "#e8d5b7",
          "constraints": ["external_wall_north"]
        }
      ],
      "walls": [
        {
          "id": "uuid",
          "start": { "x": 0, "z": 0 },
          "end": { "x": 4, "z": 0 },
          "thickness": 0.2,
          "height": 2.8,
          "type": "external"
        }
      ],
      "doors": [
        {
          "id": "uuid",
          "wall_id": "uuid",
          "position": { "x": 1.5, "z": 0 },
          "width": 0.9,
          "height": 2.1,
          "type": "hinged"
        }
      ],
      "windows": [
        {
          "id": "uuid",
          "wall_id": "uuid",
          "position": { "x": 2, "y": 1, "z": 0 },
          "width": 1.2,
          "height": 1.0,
          "sill_height": 0.9
        }
      ],
      "stairs": [],
      "open_spaces": []
    }
  ],
  "version_metadata": {
    "version_number": 1,
    "created_by": "user_uuid",
    "generation_prompt": "original prompt text",
    "refinement_prompt": null,
    "change_summary": "Initial generation"
  }
}
```

### Prompt Refinement

When a user submits a follow-up prompt on an existing design:
1. Load the current layout JSON
2. Extract what changed in the new prompt (add room, remove room, resize, change style, etc.)
3. Apply changes to the existing layout
4. Save as a new DesignVersion
5. Return updated layout JSON
6. Log the refinement action

---

## 8. Web Scraper and Training Data Pipeline

### Purpose

To improve layout generation quality over time, ArchiAI builds a data pipeline that collects publicly available architectural layout references. This data is cleaned, structured, and used to improve layout rules and eventually train or fine-tune AI generation models.

### Legal and Ethical Rules

- Only scrape publicly accessible data where permitted by the site's robots.txt and terms of service
- Never scrape copyrighted or watermarked architectural drawings without explicit permission
- Never store personally identifiable information from scraped sources
- Always store the source URL and access date for attribution and audit
- Do not use scraped data to directly reproduce copyrighted layouts — use it for pattern and rule extraction only
- Keep scraper logic completely separate from the main application

### Data to Collect

- Floor plan examples from educational and public architecture resources
- Room arrangement patterns (common adjacencies, typical room sizes)
- Building type references (apartment, house, office, retail, etc.)
- Common layout rules (setbacks, circulation paths, aspect ratios)
- Room-to-total-area ratios
- Door and window placement patterns
- Egress and accessibility patterns from public building code references

### Pipeline Architecture

```
Web scraper (Scrapy / Playwright / BeautifulSoup)
  → Raw data storage (JSON/image files, S3 or local)
  → Source validation and deduplication
  → Data cleaning (Pandas)
  → Metadata extraction (room count, area, type, adjacency labels)
  → Feature extraction (spatial patterns, dimension statistics)
  → Layout pattern dataset (structured JSON/CSV)
  → Rule engine improvement (update layout generation rules)
  → Future: model fine-tuning dataset
```

### Scraper Components

| Component | Purpose |
|---|---|
| `ScraperRunner` | Orchestrates scrape jobs, respects rate limits |
| `RobotsTxtChecker` | Validates each target domain before scraping |
| `DataCleaner` | Normalises and deduplicates raw collected data |
| `MetadataExtractor` | Tags data with building type, room count, style |
| `FeatureExtractor` | Extracts spatial patterns and dimension statistics |
| `PatternStore` | Stores processed layout patterns for use in generation |

### Admin Monitoring

The admin panel exposes:
- Scraper run history (start time, end time, records collected)
- Source URL list and status
- Error log for failed scrape attempts
- Data volume metrics

---

## 9. Collaboration, Version Control, Auto-save, and Logging

### Team Collaboration

- A **Workspace** groups users and projects under a single team identity
- A **Project** can have members separate from the workspace, or inherit workspace members
- Member roles define what each user can do:

| Role | Permissions |
|---|---|
| Owner | Full control: delete workspace, transfer ownership, all permissions |
| Admin | Manage members and roles, all edit permissions |
| Editor | Create, edit, and delete designs; cannot manage members |
| Viewer | View-only access to projects and designs |

- Team members can view the project activity history
- Future: real-time collaborative editing via WebSocket with operational transform or CRDT conflict resolution

### Version Control

- Every time a user saves a project after making changes, a new **DesignVersion** is created
- Prompt-generated changes and manual canvas edits both result in new versions
- Each version stores: full layout JSON snapshot, version number, timestamp, author, prompt used (if any), change summary
- Users can view a list of all versions for a project
- Users can preview and restore any previous version
- Future: side-by-side version diff view

### Auto-save

- After any significant canvas edit, a debounced auto-save is triggered (default 30-second debounce after last edit)
- The editor UI shows a persistent save status indicator:
  - **Saved** — green, last save time shown
  - **Saving...** — animated spinner
  - **Unsaved changes** — amber, prompts manual save
  - **Error** — red, shows retry option
- Auto-save creates or updates a **draft version** (a special version type that does not increment the main version number)
- When the user explicitly saves, the draft is promoted to a named version
- Auto-save does not overwrite named previous versions — history is always preserved

### Logging

Every important event in the system creates an **ActivityLog** entry.

#### Logged Actions

| Category | Actions |
|---|---|
| Project | created, renamed, duplicated, deleted, exported, shared |
| Design | prompt submitted, layout generated, design refined, version created, version restored |
| Canvas | object moved, object resized, object rotated, object renamed, object deleted, object added |
| Team | workspace created, member invited, role changed, member removed |
| Auth | user registered, user logged in, password changed |
| System | API error, scraper run started, scraper run completed, model updated |

#### Log Entry Structure

```json
{
  "id": "uuid",
  "project_id": "uuid",
  "workspace_id": "uuid",
  "user_id": "uuid",
  "user_name": "Samarth Chatli",
  "action_type": "object_moved",
  "timestamp": "2026-05-23T14:32:11Z",
  "affected_object_id": "uuid",
  "affected_object_type": "room",
  "affected_object_label": "Master Bedroom",
  "previous_value": { "position": { "x": 0, "y": 0, "z": 0 } },
  "new_value": { "position": { "x": 2, "y": 0, "z": 1 } },
  "reason": null,
  "metadata": {}
}
```

---

## 10. Agile Workflow

### Product Vision

ArchiAI gives anyone the ability to generate and explore an architectural layout in minutes, directly from a description — no design training required.

### Product Backlog

The product backlog is a prioritised list of all features and improvements. Items are expressed as user stories, ordered by business value and dependency. The backlog evolves each sprint as new information emerges.

High priority backlog items (MVP):
1. User registration and authentication
2. Project creation and management
3. Design brief input and basic layout generation
4. 3D canvas rendering and editing
5. Save/load with version history
6. Basic activity logging
7. Basic workspace/team structure

Medium priority (post-MVP):
8. Prompt refinement
9. Advanced 3D editing (multi-floor, stairs, windows)
10. Team collaboration and role management
11. Scraper and data pipeline
12. Export and sharing features

Lower priority (future):
13. Real-time collaboration
14. AI model improvement
15. Payment and subscription system
16. Template marketplace
17. Mobile support

### Sprint Planning

Each sprint is 1–2 weeks. At the start of each sprint:
1. Select backlog items that fit the sprint capacity
2. Break selected items into concrete tasks
3. Define the sprint goal
4. Assign tasks to team members (or self-assign for solo development)

### Sprint Goals

Each sprint has a single sentence goal that describes what a user can do after the sprint that they could not do before. This keeps the sprint focused and makes success measurable.

### User Stories

User stories follow the format:
> As a [user type], I want to [action], so that [benefit].

Each story has acceptance criteria that define when it is done.

### Definition of Done

A feature is done when:
- Code is written and reviewed
- Tests pass (unit and integration)
- Feature works end-to-end in local development
- Activity log entry is created for relevant actions
- API endpoints return correct responses
- UI shows correct state (loading, success, error)
- No regressions in existing features
- Code is committed with a descriptive message
- README or docs updated if setup steps changed

### Sprint Review

At the end of each sprint, demonstrate what was built. Test the sprint goal. Review what was completed versus planned.

### Sprint Retrospective

After the review:
- What went well?
- What slowed progress?
- What should change next sprint?

Keep retrospectives short and action-oriented. One improvement per sprint is enough.

### MVP Delivery

The MVP is delivered after Sprint 9. It includes: auth, project management, basic layout generation, 3D canvas with editing, version history, activity logging, and basic workspace structure.

### Future Iterations

After MVP, iterations focus on:
- AI generation quality improvement
- Advanced collaboration features
- Export and sharing
- Payment and subscription
- Performance and scale

---

## 11. User Stories

### Authentication

**US-01: Register an account**
As a new user, I want to register an account, so that I can save my projects and access the platform.

Acceptance criteria:
- User can enter name, email, and password
- System validates email format and password strength
- System creates user record and returns JWT token
- User is redirected to their dashboard on success
- Duplicate email returns a clear error message

---

**US-02: Log in**
As a registered user, I want to log in to my account, so that I can access my saved projects.

Acceptance criteria:
- User can enter email and password
- System validates credentials and returns JWT token
- Invalid credentials return a clear error message
- User is redirected to their dashboard on success

---

### Workspace and Team

**US-03: Create a workspace/team**
As a user, I want to create a team workspace, so that I can collaborate with others on design projects.

Acceptance criteria:
- User can enter workspace name and description
- User becomes the Owner of the workspace
- Workspace appears in the user's workspace list

---

**US-04: Invite team members**
As a workspace owner or admin, I want to invite users by email, so that they can access and contribute to workspace projects.

Acceptance criteria:
- Owner/admin can enter an email address to send an invitation
- Invited user receives an invitation link
- Accepted invitation adds user to workspace with default Editor role
- Invitation link expires after 48 hours

---

**US-05: Manage member roles**
As a workspace owner or admin, I want to change a member's role, so that access permissions stay appropriate as the team grows.

Acceptance criteria:
- Owner/admin can view all workspace members
- Owner/admin can change a member's role to Owner, Admin, Editor, or Viewer
- Role change is immediately effective
- Role change is logged in the activity history
- Owner cannot demote themselves without assigning another Owner

---

### Project Management

**US-06: Create a project**
As a user, I want to create a new project, so that I can start working on a new architectural layout.

Acceptance criteria:
- User can enter project name, description, and building type
- Project is created with a unique ID and appears in the dashboard
- Creation is logged in activity history

---

**US-07: Enter a design brief**
As a user, I want to describe my design idea in plain text, so that the system can generate a layout without me needing to draw anything.

Acceptance criteria:
- User sees a text area for the design brief
- User can enter free-form text (minimum 10 characters)
- System shows a loading state while processing
- System returns a 3D layout on success
- System shows a clear error message on failure

---

### 3D Canvas and Editing

**US-08: View layout in 3D canvas**
As a user, I want to see my generated layout in a 3D interactive view, so that I can understand the spatial arrangement.

Acceptance criteria:
- Generated layout renders in the 3D canvas within 5 seconds
- User can orbit, zoom, and pan the camera using mouse controls
- Rooms are displayed as labelled 3D blocks
- Walls, doors, and windows are visible as distinct elements

---

**US-09: Select objects in the canvas**
As a user, I want to click on a room or component in the canvas to select it, so that I can edit or move it.

Acceptance criteria:
- Clicking an object highlights it visually (outline or colour change)
- Inspector panel appears showing the selected object's properties
- Clicking empty canvas space deselects the object
- Only one object can be selected at a time (MVP)

---

**US-10: Move objects with mouse drag-and-drop**
As a user, I want to drag rooms and components with my mouse, so that I can visually rearrange the layout without entering coordinates.

Acceptance criteria:
- User can click/select a room or component in the 3D canvas
- User can drag the selected object with the mouse to move it visually
- User can use transform controls to move objects on X, Y, and Z axes
- User can still edit exact position values in the inspector panel
- Movement feels smooth and does not require only manual coordinate input
- Position change is reflected immediately in the inspector panel
- Move action is logged in the activity history
- Auto-save is triggered after the move

---

**US-11: Move objects with X/Y/Z transform controls**
As a user, I want to move objects along specific axes using visible gizmos, so that I can make precise directional adjustments.

Acceptance criteria:
- Selected object shows visible X (red), Y (green), Z (blue) axis handles
- Dragging an axis handle moves the object only along that axis
- Position values in the inspector panel update in real-time
- Constrained movement prevents accidental off-axis placement

---

**US-12: Edit dimensions through inspector panel**
As a user, I want to type exact values into the inspector panel, so that I can set precise positions and dimensions for any object.

Acceptance criteria:
- Inspector shows editable fields for X, Y, Z position and Width, Height, Depth
- Pressing Enter or Tab applies the value to the canvas immediately
- Invalid values (non-numeric, out of bounds) show an inline error
- Changes are reflected in the 3D canvas in real-time

---

**US-13: Refine design using prompt**
As a user, I want to type a follow-up instruction to improve my layout, so that I can iterate on the design without starting over.

Acceptance criteria:
- User can enter a refinement prompt while viewing an existing layout
- System applies the changes to the current layout
- A new design version is created for the refinement
- The canvas updates to show the refined layout
- Refinement action is logged with the prompt text

---

### Saving and Version Control

**US-14: Auto-save project changes**
As a user, I want my project to save automatically, so that I do not lose work if I close the browser.

Acceptance criteria:
- Project auto-saves after significant canvas edits (debounced 30 seconds)
- Save status indicator shows: Saving, Saved, or Error
- Auto-save does not overwrite named version history
- Unsaved changes are indicated in the UI

---

**US-15: View version history**
As a user, I want to see a list of all saved versions of my project, so that I can track how the design evolved.

Acceptance criteria:
- Version history panel lists all named versions in reverse chronological order
- Each entry shows: version number, timestamp, author, and change summary
- User can click a version to preview it

---

**US-16: Restore a previous version**
As a user, I want to restore an older version of my project, so that I can undo unwanted changes.

Acceptance criteria:
- User can select a version from history and click Restore
- System sets that version's layout JSON as the current design
- A new version is created representing the restore action
- Restore action is logged with the version number restored from

---

### Logging and Activity

**US-17: View activity logs**
As a team member, I want every project change to be tracked with who changed it, what changed, when it changed, and why, so that the team has proper documentation and can restore previous work if needed.

Acceptance criteria:
- Every important project edit creates an activity log entry
- Saved layout changes create a new version or update the current draft version
- Users can view version history
- Users can restore a previous version
- Logs show user, action, timestamp, affected object, old value, and new value
- Team members can view recent project activity
- Admin/owner can manage member roles and access

---

### Export and Share

**US-18: Export final output**
As a user, I want to export my layout as an image or PDF, so that I can share it outside the platform.

Acceptance criteria:
- User can trigger export from the editor toolbar
- Image export produces a PNG/JPG screenshot of the 3D canvas
- PDF export produces a document with project metadata and layout image
- Export action is logged

---

**US-19: Share project link**
As a user, I want to generate a shareable link to my project, so that clients or colleagues can view it without an account.

Acceptance criteria:
- User can generate a public or token-protected share link
- Shared link opens a read-only view of the latest published version
- User can revoke the share link at any time
- Share action is logged

---

### Data Pipeline

**US-20: Collect training data**
As a developer, I want the scraper to collect publicly available layout references, so that we can improve generation quality over time.

Acceptance criteria:
- Scraper only runs on permitted sources (robots.txt checked)
- Collected data is stored with source URL and timestamp
- Admin can view scraper run history and status
- Scraper failures are logged and do not affect the main application

---

### Admin

**US-21: Manage users and projects as admin**
As an admin, I want to view and manage all users, projects, and teams on the platform, so that I can maintain platform health and handle support requests.

Acceptance criteria:
- Admin can view a list of all users, projects, and workspaces
- Admin can suspend or delete a user account
- Admin can view system activity logs and error logs
- Admin dashboard shows platform health metrics

---

## 12. Sprint Roadmap

---

### Sprint 0: Product Planning

**Goal:** Establish a shared understanding of the product so that every build decision is grounded in clear requirements and architecture.

**Main Tasks:**
- Finalise requirements document (this file)
- Define user personas and target use cases
- Select and document tech stack with rationale
- Design database schema (all models)
- Design API contract (all routes)
- Define folder structure for frontend and backend
- Define MVP scope and sprint order
- Create initial GitHub repository with branch strategy
- Write initial README with setup instructions

**Expected Output:**
- `docs/PROJECT_STRATEGY.md` (this file)
- `docs/API_PLAN.md`
- `docs/DATA_MODEL.md`
- Repository with branch: `main`, `develop`, feature branch convention agreed

**Acceptance Criteria:**
- All team members understand what the MVP includes and excludes
- Tech stack is agreed and justified
- Database models cover all MVP features
- API routes cover all MVP user stories
- No ambiguity about folder structure or module boundaries

---

### Sprint 1: Authentication and Project Setup

**Goal:** Users can register, log in, and reach a personal dashboard where their projects will live.

**Main Tasks:**
- Set up backend project (FastAPI or Django)
- Set up database connection (PostgreSQL)
- Implement User model
- Implement register endpoint (`POST /api/auth/register`)
- Implement login endpoint (`POST /api/auth/login`)
- Implement logout endpoint (`POST /api/auth/logout`)
- Implement `GET /api/auth/me`
- Implement JWT token generation and validation middleware
- Set up frontend project (React + TypeScript + Tailwind)
- Build register page
- Build login page
- Build basic dashboard page (empty, authenticated)
- Protect dashboard route (redirect if not authenticated)
- Write tests for all auth endpoints

**Expected Output:**
- Working registration and login flow
- JWT tokens issued on login
- Protected routes working in frontend
- User model in database

**Acceptance Criteria:**
- User can register with email and password
- Duplicate email registration returns 409 error
- Login with correct credentials returns JWT token
- Login with wrong credentials returns 401 error
- `/api/auth/me` returns current user info when authenticated
- Dashboard redirects to login if not authenticated

---

### Sprint 2: Backend Foundation

**Goal:** Core API infrastructure is in place so all future features have a consistent, reliable base.

**Main Tasks:**
- Implement `GET /api/health` route
- Implement Project model and CRUD endpoints
- Implement basic error handling middleware (structured JSON errors)
- Implement request validation using Pydantic
- Set up logging infrastructure (file + database)
- Implement ActivityLog model
- Write basic activity logging utility function
- Write tests for project CRUD endpoints

**Expected Output:**
- Health route returns service status
- Project create, read, update, delete endpoints working
- Consistent error response format across all routes
- Basic activity logging working

**Acceptance Criteria:**
- `GET /api/health` returns 200 with service info
- `POST /api/projects` creates a project and returns it
- `GET /api/projects` returns the current user's projects
- `PUT /api/projects/:id` updates project, returns updated record
- `DELETE /api/projects/:id` deletes project, returns 204
- All error responses follow `{ error: string, code: string, status: number }` format
- Project creation logs an activity entry

---

### Sprint 3: Frontend Foundation

**Goal:** The core UI shell is in place so users have a consistent experience navigating the application.

**Main Tasks:**
- Build landing page (hero, features summary, CTA)
- Build navigation/header component (auth-aware)
- Build project dashboard page (list projects, create project button)
- Build project creation modal/form
- Build prompt input page (text area, submit button, loading state)
- Connect all pages to backend APIs using Axios
- Set up Zustand store for auth state and project state
- Add global toast notification system (success, error, info)
- Write component tests for key UI elements

**Expected Output:**
- Landing page with CTA
- Dashboard showing the user's projects
- Prompt input page accessible from a project

**Acceptance Criteria:**
- Unauthenticated users see landing page and can navigate to register/login
- Authenticated users see their project dashboard
- Creating a project from the dashboard makes an API call and updates the list
- Prompt input page accepts text and shows loading state on submit

---

### Sprint 4: Basic 3D Canvas

**Goal:** Users can see a 3D scene in the browser and interact with it using mouse controls, with basic object selection and movement working.

**Main Tasks:**
- Set up React Three Fiber canvas with basic scene (lights, grid, background)
- Add OrbitControls for camera orbit, zoom, and pan
- Render a hardcoded set of room blocks as coloured 3D boxes to verify rendering
- Implement object selection using raycasting (left-click to select)
- Highlight selected object visually (emissive outline or colour change)
- Add TransformControls gizmo to selected object
- Implement mouse drag-and-drop movement for selected objects
- Build basic inspector panel (shows position, dimensions of selected object)
- Connect inspector input fields to update object state
- Write tests for selection and position update logic

**Expected Output:**
- Interactive 3D canvas with camera controls
- Clickable room blocks that show selection highlight
- Transform gizmo for X/Y/Z constrained movement
- Mouse drag-and-drop movement working in canvas
- Inspector panel showing and updating position values

**Acceptance Criteria:**
- Camera orbits, zooms, and pans with mouse
- Clicking a room block selects it and shows the inspector
- Dragging a selected object moves it smoothly in the canvas
- Inspector X/Y/Z fields update when object is moved
- Editing an inspector field moves the object in the canvas
- TransformControls gizmo is visible on selected object and constrains movement to one axis

---

### Sprint 5: Basic 3D Layout Generation

**Goal:** Users can submit a design brief and receive a generated 3D layout rendered in the canvas.

**Main Tasks:**
- Implement prompt service (extracts room list and basic dimensions from text)
- Implement rule-based layout engine (assigns positions to rooms on a grid)
- Implement layout-to-JSON serialiser (outputs layout JSON schema)
- Implement `POST /api/design/generate` endpoint
- Implement Design and DesignVersion models
- Save generated design and first version to database
- Log generation action in ActivityLog
- Connect frontend prompt input page to generation API
- Parse returned layout JSON and render rooms in the canvas
- Show loading state during generation, error state on failure

**Expected Output:**
- User submits prompt → API returns layout JSON → Canvas renders layout
- Design and version saved to database
- Generation logged in activity history

**Acceptance Criteria:**
- A prompt like "3 bedroom apartment with living room and kitchen" generates a layout with at least those rooms
- Layout JSON matches the defined schema
- Rooms render in the 3D canvas as labelled blocks
- Generation under 5 seconds for prompts up to 10 rooms
- Failed generation shows a user-friendly error message

---

### Sprint 6: 3D Editing Workflow

**Goal:** Users have a complete editing experience: select, move, resize, rotate, duplicate, delete, snap to grid, and edit via inspector.

**Main Tasks:**
- Add resize handles (or inspector-based resize) for selected objects
- Add rotation handle (or inspector-based rotation)
- Implement duplicate (Ctrl+D shortcut and context menu)
- Implement delete (Delete key and context menu)
- Implement grid snapping toggle
- Add "Add object" panel (add wall, door, window, stair, floor, open space)
- Add object labels displayed in the canvas
- Log every edit action (move, resize, rotate, add, delete) in activity log
- Trigger auto-save after any edit (debounced)
- Write tests for edit actions and their log entries

**Expected Output:**
- Full editing toolkit: move, resize, rotate, duplicate, delete, snap, add
- All edits logged in activity history
- Auto-save triggers after edits

**Acceptance Criteria:**
- User can resize a room by editing inspector Width/Height/Depth
- User can rotate a room using the inspector or rotation handle
- Ctrl+D duplicates the selected object
- Delete key removes the selected object
- Grid snapping aligns moved objects to grid when enabled
- Every edit creates an activity log entry with old and new values
- Auto-save indicator shows "Saving..." and then "Saved" after each edit

---

### Sprint 7: Database and Project Management

**Goal:** Users can save, load, update, delete, and manage their projects reliably with proper persistence.

**Main Tasks:**
- Implement full project save (layout JSON → database)
- Implement project load (fetch layout JSON → render in canvas)
- Implement manual save button (promotes draft version to named version)
- Implement project delete with confirmation modal
- Implement project duplicate
- Implement project rename
- Generate and store project thumbnails (canvas screenshot on save)
- Display thumbnails in the project dashboard
- Write tests for save, load, version creation

**Expected Output:**
- Projects save and load correctly from database
- Dashboard shows project thumbnails
- Manual save creates a new named version

**Acceptance Criteria:**
- Manual save stores current layout JSON as a named version
- Loading a project restores the layout correctly in the canvas
- Deleted projects are removed from dashboard
- Duplicated project creates a new project with a copy of the layout
- Project thumbnail visible in dashboard after first save

---

### Sprint 8: Prompt Refinement

**Goal:** Users can improve their generated layout using follow-up prompts without losing the previous version.

**Main Tasks:**
- Implement `POST /api/design/refine` endpoint
- Implement refinement logic (apply delta changes to existing layout JSON)
- Create new DesignVersion on every successful refinement
- Log refinement action with prompt text in activity log
- Build refinement prompt input UI (below existing canvas)
- Show diff indicator when a refinement changes the layout
- Write tests for refinement endpoint and version creation

**Expected Output:**
- Follow-up prompt updates the layout and creates a new version
- Version history shows both the original and refined versions

**Acceptance Criteria:**
- Submitting "add a study room" to an existing layout adds the room
- Submitting "remove the dining room" removes it
- Each refinement creates a new DesignVersion
- Refinement action logged with prompt text
- Version history shows the refinement entry

---

### Sprint 9: Team Collaboration, Version Control, and Logging

**Goal:** Teams can share projects, manage roles, view history, and restore previous versions — ArchiAI is team-ready.

**Main Tasks:**
- Implement Workspace model and CRUD endpoints
- Implement TeamMember model with role field
- Implement workspace invite endpoint
- Implement role management endpoint
- Build workspace creation and management UI
- Build member invite and role management UI
- Implement version history panel in the editor
- Implement version restore endpoint and UI
- Build activity log panel (per-project feed)
- Implement auto-save with draft version logic
- Implement save status indicator (Saving / Saved / Error)
- Write tests for workspace, role, version, and log endpoints

**Expected Output:**
- Workspaces with member roles working
- Version history visible and restorable in editor
- Activity log panel showing all project actions
- Auto-save with status indicator

**Acceptance Criteria:**
- User can create a workspace and invite a member by email
- Invited member joins with Editor role
- Owner can change a member's role
- Version history panel lists all saved versions
- Clicking Restore on a version sets it as current layout
- Restore creates a new version entry in history
- Activity log shows all actions with user, time, old/new values
- Auto-save triggers within 30 seconds of last edit
- Save status indicator updates correctly

---

### Sprint 10: Web Scraper and Data Pipeline

**Goal:** A responsible, isolated data pipeline collects and structures layout reference data for future generation improvement.

**Main Tasks:**
- Set up scraper module (completely separate from main app)
- Implement RobotsTxtChecker utility
- Implement basic Scrapy/BeautifulSoup scraper for one permitted public source
- Store raw data with source URL and timestamp
- Implement data cleaning step (Pandas)
- Implement metadata extraction (room count, type, area labels)
- Implement ScraperSource and ScraperRun models
- Implement scraper management API endpoints
- Build scraper admin panel (run, view status, view sources)
- Write tests for data cleaning and metadata extraction

**Expected Output:**
- Working scraper that collects permitted layout reference data
- Cleaned and labelled dataset stored in database
- Admin panel for monitoring scraper runs

**Acceptance Criteria:**
- Scraper checks robots.txt before accessing any URL
- Scraper stores source URL and timestamp with every record
- Scraper run is logged with start time, end time, and record count
- Admin can trigger a scraper run from the admin panel
- Admin can view run history and error log

---

### Sprint 11: AI / Layout Improvement

**Goal:** Layout generation quality improves using patterns collected from the data pipeline and better extraction logic.

**Main Tasks:**
- Analyse collected layout data for common patterns and rules
- Update layout engine rules using extracted patterns (better room sizing, adjacency, placement)
- Improve requirement extraction (handle edge cases from real user prompts collected in production)
- Optionally integrate Claude API for prompt understanding (if rule-based extraction proves insufficient)
- Add building-type-specific generation templates (apartment, house, office, studio)
- Test generation quality against a set of benchmark prompts
- Write tests for improved layout engine

**Expected Output:**
- Measurably better layout generation across common prompt types
- Building-type templates producing recognisably correct spatial arrangements

**Acceptance Criteria:**
- Apartment prompts produce layouts with private/public zone separation
- Office prompts produce layouts with open space, meeting rooms, and support spaces
- Room sizing matches typical real-world ranges for each room type
- Benchmark prompt set passes visual quality review

---

### Sprint 12: Export, Share, and Polish

**Goal:** The MVP is complete, tested, and ready for real users.

**Main Tasks:**
- Implement image export (canvas screenshot to PNG/JPG)
- Implement PDF export (layout image + project metadata)
- Implement shareable project link (public read-only view)
- Full UI review and polish (spacing, typography, responsiveness, loading states, empty states)
- End-to-end testing of the full user journey (register → create → generate → edit → save → export)
- Fix all known bugs and edge cases
- Write comprehensive README with local setup instructions
- Set up Docker Compose for local development
- Prepare deployment configuration (environment variables, build scripts)
- Final review of all activity logs, version history, and auto-save behaviour

**Expected Output:**
- Export and share features working
- Polished, production-quality UI
- Docker-based local setup
- Deployment-ready build

**Acceptance Criteria:**
- Image export produces a clean PNG of the current canvas view
- PDF export includes project name, date, brief, and canvas image
- Share link opens a read-only view of the design
- All empty states, loading states, and error states display correctly
- Local setup works with a single `docker-compose up` command
- Full user journey works end-to-end without errors

---

## 13. Recommended Tech Stack

### Frontend

| Technology | Purpose |
|---|---|
| React 18 | UI component framework |
| TypeScript | Type safety and developer experience |
| Tailwind CSS | Utility-first styling |
| Three.js | 3D rendering engine |
| React Three Fiber | React wrapper for Three.js |
| @react-three/drei | Helper components (OrbitControls, TransformControls, etc.) |
| Zustand | Lightweight global state management for editor and auth state |
| Axios | HTTP client for API calls |
| React Router | Client-side routing |
| React Hook Form | Form handling and validation |

### Backend

| Technology | Purpose |
|---|---|
| Python 3.11+ | Primary backend language |
| FastAPI | High-performance async REST API framework |
| PostgreSQL | Primary relational database |
| SQLAlchemy | ORM for database interaction |
| Alembic | Database migrations |
| Pydantic v2 | Request/response validation and serialisation |
| python-jose | JWT token generation and validation |
| passlib / bcrypt | Password hashing |
| python-dotenv | Environment variable management |
| WebSockets (future) | Real-time collaboration support |

### AI / Layout Logic

| Technology | Purpose |
|---|---|
| Python | Layout engine implementation |
| Custom rule engine | MVP layout generation logic |
| Anthropic Claude API (future) | LLM-based prompt understanding and generation |
| NumPy/Pandas | Numerical and data operations in layout engine |

### Data Pipeline

| Technology | Purpose |
|---|---|
| Python | Scraper and pipeline language |
| Scrapy | Web scraping framework |
| BeautifulSoup | HTML parsing for simpler scrape targets |
| Playwright | JavaScript-rendered page scraping where permitted |
| Pandas | Data cleaning and transformation |
| PostgreSQL | Processed data storage |

### DevOps and Deployment

| Technology | Purpose |
|---|---|
| Docker + Docker Compose | Containerisation and local development |
| GitHub | Source control and CI/CD |
| GitHub Actions | Automated testing and linting on push |
| Render / Railway / Fly.io | Initial cloud deployment (MVP) |
| AWS / GCP (future) | Scalable cloud deployment |
| dotenv / environment variables | Secrets management |

---

## 14. Recommended Project Structure

```
archiai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth/
│   │   │   │   ├── router.py
│   │   │   │   └── schemas.py
│   │   │   ├── users/
│   │   │   │   ├── router.py
│   │   │   │   └── schemas.py
│   │   │   ├── workspaces/
│   │   │   │   ├── router.py
│   │   │   │   └── schemas.py
│   │   │   ├── projects/
│   │   │   │   ├── router.py
│   │   │   │   └── schemas.py
│   │   │   ├── designs/
│   │   │   │   ├── router.py
│   │   │   │   └── schemas.py
│   │   │   ├── versions/
│   │   │   │   ├── router.py
│   │   │   │   └── schemas.py
│   │   │   ├── logs/
│   │   │   │   ├── router.py
│   │   │   │   └── schemas.py
│   │   │   ├── scraper/
│   │   │   │   ├── router.py
│   │   │   │   └── schemas.py
│   │   │   └── health/
│   │   │       └── router.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── workspace.py
│   │   │   ├── team_member.py
│   │   │   ├── project.py
│   │   │   ├── project_member.py
│   │   │   ├── design.py
│   │   │   ├── design_version.py
│   │   │   ├── layout_object.py
│   │   │   ├── activity_log.py
│   │   │   ├── change_log.py
│   │   │   ├── export_record.py
│   │   │   ├── scraper_source.py
│   │   │   └── scraper_run.py
│   │   ├── schemas/
│   │   │   └── (Pydantic schemas matching each model)
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── prompt_service.py
│   │   │   ├── layout_service.py
│   │   │   ├── version_service.py
│   │   │   ├── logging_service.py
│   │   │   ├── collaboration_service.py
│   │   │   ├── scraper_service.py
│   │   │   ├── ai_service.py
│   │   │   └── export_service.py
│   │   ├── database/
│   │   │   ├── connection.py
│   │   │   └── migrations/
│   │   ├── config/
│   │   │   └── settings.py
│   │   ├── utils/
│   │   │   ├── jwt.py
│   │   │   ├── hashing.py
│   │   │   ├── pagination.py
│   │   │   └── thumbnails.py
│   │   ├── tests/
│   │   │   ├── test_auth.py
│   │   │   ├── test_projects.py
│   │   │   ├── test_designs.py
│   │   │   ├── test_versions.py
│   │   │   └── test_logs.py
│   │   └── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── canvas/
│   │   │   │   ├── Scene.tsx
│   │   │   │   ├── RoomBlock.tsx
│   │   │   │   ├── WallMesh.tsx
│   │   │   │   ├── DoorMesh.tsx
│   │   │   │   ├── WindowMesh.tsx
│   │   │   │   ├── TransformGizmo.tsx
│   │   │   │   ├── SelectionHighlight.tsx
│   │   │   │   └── GridHelper.tsx
│   │   │   ├── editor/
│   │   │   │   ├── InspectorPanel.tsx
│   │   │   │   ├── Toolbar.tsx
│   │   │   │   ├── SaveStatusIndicator.tsx
│   │   │   │   ├── RefinementInput.tsx
│   │   │   │   └── AddObjectPanel.tsx
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Footer.tsx
│   │   │   ├── auth/
│   │   │   │   ├── RegisterForm.tsx
│   │   │   │   └── LoginForm.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── ProjectCard.tsx
│   │   │   │   ├── ProjectGrid.tsx
│   │   │   │   └── CreateProjectModal.tsx
│   │   │   ├── workspace/
│   │   │   │   ├── WorkspaceCard.tsx
│   │   │   │   ├── MemberList.tsx
│   │   │   │   └── InviteMemberModal.tsx
│   │   │   ├── version/
│   │   │   │   ├── VersionHistoryPanel.tsx
│   │   │   │   └── VersionEntry.tsx
│   │   │   ├── logs/
│   │   │   │   ├── ActivityLogPanel.tsx
│   │   │   │   └── LogEntry.tsx
│   │   │   └── ui/
│   │   │       ├── Button.tsx
│   │   │       ├── Modal.tsx
│   │   │       ├── Toast.tsx
│   │   │       ├── Input.tsx
│   │   │       └── Spinner.tsx
│   │   ├── pages/
│   │   │   ├── Landing/
│   │   │   ├── Login/
│   │   │   ├── Register/
│   │   │   ├── Dashboard/
│   │   │   ├── Workspace/
│   │   │   ├── Editor/
│   │   │   ├── ProjectView/
│   │   │   ├── ActivityLog/
│   │   │   └── VersionHistory/
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── auth.service.ts
│   │   │   ├── project.service.ts
│   │   │   ├── design.service.ts
│   │   │   ├── version.service.ts
│   │   │   └── log.service.ts
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useProject.ts
│   │   │   ├── useCanvas.ts
│   │   │   └── useAutoSave.ts
│   │   ├── store/
│   │   │   ├── authStore.ts
│   │   │   ├── projectStore.ts
│   │   │   ├── editorStore.ts
│   │   │   └── uiStore.ts
│   │   ├── styles/
│   │   │   └── globals.css
│   │   ├── utils/
│   │   │   ├── layoutParser.ts
│   │   │   ├── canvasHelpers.ts
│   │   │   └── formatters.ts
│   │   ├── types/
│   │   │   ├── layout.types.ts
│   │   │   ├── project.types.ts
│   │   │   └── user.types.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.ts
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── metadata/
│
├── docs/
│   ├── PROJECT_STRATEGY.md       ← this file
│   ├── API_PLAN.md
│   ├── DATA_PIPELINE.md
│   ├── BUSINESS_PLAN.md
│   ├── VERSION_CONTROL_PLAN.md
│   └── LOGGING_PLAN.md
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 15. Recommended Database Models

### User
Stores registered user accounts.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| email | String | Unique, indexed |
| hashed_password | String | bcrypt hash |
| name | String | Display name |
| avatar_url | String | Optional |
| plan_tier | Enum | free, student, pro, team, enterprise |
| is_active | Boolean | Account suspension flag |
| created_at | Timestamp | |
| updated_at | Timestamp | |

---

### Workspace
Represents a team or organisation unit that groups projects and members.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | String | |
| description | String | Optional |
| owner_id | FK → User | |
| plan_tier | Enum | Workspace subscription level |
| created_at | Timestamp | |
| updated_at | Timestamp | |

---

### TeamMember
Junction table linking users to workspaces with roles.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| workspace_id | FK → Workspace | |
| user_id | FK → User | |
| role | Enum | owner, admin, editor, viewer |
| joined_at | Timestamp | |

---

### Project
A single design project owned by a user or workspace.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | String | |
| description | String | Optional |
| building_type | String | apartment, house, office, etc. |
| owner_id | FK → User | |
| workspace_id | FK → Workspace | Optional |
| thumbnail_url | String | Optional |
| is_deleted | Boolean | Soft delete |
| created_at | Timestamp | |
| updated_at | Timestamp | |

---

### ProjectMember
Links additional users to a project with specific roles.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| project_id | FK → Project | |
| user_id | FK → User | |
| role | Enum | admin, editor, viewer |
| added_at | Timestamp | |

---

### Design
The current active design state for a project.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| project_id | FK → Project | |
| layout_json | JSONB | Full layout object |
| generation_prompt | Text | Original prompt |
| status | Enum | draft, saved, archived |
| created_by | FK → User | |
| created_at | Timestamp | |
| updated_at | Timestamp | |

---

### DesignVersion
A snapshot of a design at a point in time. Immutable once created.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| design_id | FK → Design | |
| project_id | FK → Project | |
| version_number | Integer | Auto-incrementing per project |
| version_type | Enum | auto_draft, named, restored |
| layout_json | JSONB | Snapshot of layout at this version |
| change_summary | String | Brief description of what changed |
| prompt_used | Text | Prompt that triggered this version (if any) |
| created_by | FK → User | |
| created_at | Timestamp | |

---

### LayoutObject
Optional: individual object records for fine-grained tracking. For MVP, layout is stored as JSONB in DesignVersion; individual LayoutObject records are used for detailed change logging.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Matches ID in layout JSON |
| design_id | FK → Design | |
| object_type | Enum | room, wall, door, window, stair, open_space |
| label | String | |
| position_json | JSONB | { x, y, z } |
| dimensions_json | JSONB | { width, height, depth } |
| rotation_json | JSONB | { x, y, z } |
| floor_level | Integer | |
| created_at | Timestamp | |
| updated_at | Timestamp | |

---

### ActivityLog
Records every important event in the system.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| project_id | FK → Project | Optional |
| workspace_id | FK → Workspace | Optional |
| user_id | FK → User | |
| action_type | String | Enum of all logged action types |
| affected_object_id | UUID | Optional |
| affected_object_type | String | Optional |
| affected_object_label | String | Optional |
| previous_value | JSONB | Optional |
| new_value | JSONB | Optional |
| reason | String | Optional comment/reason |
| metadata | JSONB | Additional context |
| timestamp | Timestamp | Indexed |

---

### ChangeLog
Detailed change records for design edits, linked to ActivityLog.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| activity_log_id | FK → ActivityLog | |
| design_version_id | FK → DesignVersion | |
| field_name | String | Which field changed |
| old_value | JSONB | |
| new_value | JSONB | |
| timestamp | Timestamp | |

---

### ExportRecord
Tracks every export action for billing, audit, and analytics.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| project_id | FK → Project | |
| user_id | FK → User | |
| export_type | Enum | image, pdf, share_link, cad (future) |
| file_url | String | Optional, stored output |
| created_at | Timestamp | |

---

### ScraperSource
Tracks permitted data sources for the layout data pipeline.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | String | Human-readable source name |
| base_url | String | |
| robots_txt_url | String | |
| is_permitted | Boolean | Checked against robots.txt |
| data_type | String | floor_plans, layout_rules, etc. |
| added_at | Timestamp | |
| last_checked | Timestamp | |

---

### ScraperRun
Logs each run of the data pipeline scraper.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| source_id | FK → ScraperSource | |
| started_at | Timestamp | |
| completed_at | Timestamp | Optional |
| status | Enum | running, completed, failed |
| records_collected | Integer | |
| error_message | String | Optional |

---

## 16. API Plan

### Auth

| Method | Route | Description | Auth |
|---|---|---|---|
| POST | `/api/auth/register` | Register new user | Public |
| POST | `/api/auth/login` | Login, returns JWT | Public |
| POST | `/api/auth/logout` | Invalidate session/token | Auth |
| GET | `/api/auth/me` | Get current user info | Auth |

---

### Workspaces / Teams

| Method | Route | Description | Auth |
|---|---|---|---|
| GET | `/api/workspaces` | List user's workspaces | Auth |
| POST | `/api/workspaces` | Create workspace | Auth |
| GET | `/api/workspaces/:id` | Get workspace detail | Member |
| PUT | `/api/workspaces/:id` | Update workspace | Owner/Admin |
| DELETE | `/api/workspaces/:id` | Delete workspace | Owner |
| POST | `/api/workspaces/:id/invite` | Invite member by email | Owner/Admin |
| PUT | `/api/workspaces/:id/members/:memberId/role` | Change member role | Owner/Admin |
| DELETE | `/api/workspaces/:id/members/:memberId` | Remove member | Owner/Admin |

---

### Projects

| Method | Route | Description | Auth |
|---|---|---|---|
| POST | `/api/projects` | Create project | Auth |
| GET | `/api/projects` | List user's projects | Auth |
| GET | `/api/projects/:id` | Get project detail | Member |
| PUT | `/api/projects/:id` | Update project metadata | Editor+ |
| DELETE | `/api/projects/:id` | Delete project | Owner/Admin |
| POST | `/api/projects/:id/duplicate` | Duplicate project | Member |
| GET | `/api/projects/:id/activity` | Get project activity log | Member |

---

### Designs

| Method | Route | Description | Auth |
|---|---|---|---|
| POST | `/api/design/generate` | Generate layout from prompt | Editor+ |
| POST | `/api/design/refine` | Refine existing layout | Editor+ |
| GET | `/api/designs` | List designs for a project | Member |
| GET | `/api/designs/:id` | Get design with layout JSON | Member |
| PUT | `/api/designs/:id` | Update design (save canvas edits) | Editor+ |
| DELETE | `/api/designs/:id` | Delete design | Owner/Admin |

---

### Versions

| Method | Route | Description | Auth |
|---|---|---|---|
| GET | `/api/projects/:id/versions` | List all versions for project | Member |
| POST | `/api/projects/:id/versions` | Create named version (manual save) | Editor+ |
| GET | `/api/projects/:id/versions/:versionId` | Get specific version | Member |
| POST | `/api/projects/:id/restore-version` | Restore a previous version | Editor+ |

---

### Logs

| Method | Route | Description | Auth |
|---|---|---|---|
| POST | `/api/logs/activity` | Create activity log entry | Auth (internal) |
| GET | `/api/logs/system` | Get system-level logs | Admin |
| GET | `/api/projects/:id/logs` | Get project activity log | Member |

---

### Export / Share

| Method | Route | Description | Auth |
|---|---|---|---|
| POST | `/api/export/image` | Export canvas as image | Member |
| POST | `/api/export/pdf` | Export project as PDF | Member |
| POST | `/api/share/:projectId` | Generate shareable link | Member |
| DELETE | `/api/share/:projectId` | Revoke shareable link | Owner/Editor |

---

### Scraper

| Method | Route | Description | Auth |
|---|---|---|---|
| POST | `/api/scraper/run` | Trigger a scraper run | Admin |
| GET | `/api/scraper/status` | Get current scraper run status | Admin |
| GET | `/api/scraper/sources` | List all scraper sources | Admin |

---

### System

| Method | Route | Description | Auth |
|---|---|---|---|
| GET | `/api/health` | Service health check | Public |

---

## 17. Technical Workflow

```
User registers / logs in
  │
  ▼
JWT token issued → stored in localStorage / httpOnly cookie
  │
  ▼
User creates or joins a Workspace
  │
  ▼
User creates a Project
  │
  ▼
User enters a design brief (text area)
  │
  ▼
Frontend sends POST /api/design/generate
  │
  ▼
Backend: prompt_service extracts requirements
  → layout_service builds 2D/3D layout JSON
  → Design and DesignVersion records created
  → ActivityLog entry: "layout_generated"
  │
  ▼
Backend returns layout JSON
  │
  ▼
Frontend parses layout JSON → renders in React Three Fiber canvas
  │
  ▼
User interacts with canvas:
  → Click to select object → inspector panel opens
  → Drag to move (DragControls / pointer events)
  → Transform gizmo for X/Y/Z constrained movement
  → Inspector fields for exact value editing
  → Resize, rotate, delete, duplicate via toolbar/keyboard
  │
  ▼
On each edit:
  → Zustand editorStore updated
  → Canvas re-renders with updated positions
  → Auto-save debounce timer starts
  → ActivityLog entry queued: "object_moved" / "object_resized" etc.
  │
  ▼
Auto-save triggers:
  → PUT /api/designs/:id (layout JSON payload)
  → Draft DesignVersion created or updated
  → Save status indicator: Saving → Saved
  │
  ▼
User submits refinement prompt:
  → POST /api/design/refine
  → Backend applies delta changes to existing layout
  → New DesignVersion created
  → ActivityLog: "design_refined"
  → Canvas updates with refined layout
  │
  ▼
User views version history → can preview any version
User restores a version → POST /api/projects/:id/restore-version
  → New DesignVersion created for the restore action
  → Canvas loads restored layout
  │
  ▼
User views activity log → full list of all project actions
  │
  ▼
User exports or shares:
  → POST /api/export/image or /api/export/pdf
  → ExportRecord created
  → ActivityLog: "project_exported"
  │
  ▼
Background: Scraper collects layout reference data
  → Data cleaned and structured
  → Layout patterns extracted
  → Generation rules improved
  → Future: model fine-tuned on collected data
```

---

## 18. MVP Scope

### Included in MVP

| Feature | Included |
|---|---|
| Landing page | Yes |
| Register and login | Yes |
| User dashboard | Yes |
| Basic workspace and project structure | Yes |
| Create project | Yes |
| Prompt input and submission | Yes |
| Basic backend API | Yes |
| Rule-based layout JSON generation | Yes |
| Basic 3D canvas rendering (room blocks) | Yes |
| Camera orbit, zoom, pan | Yes |
| Click to select objects | Yes |
| Mouse drag-and-drop movement | Yes |
| Transform controls (X/Y/Z gizmo) | Yes |
| Inspector panel (position, dimensions) | Yes |
| Resize and rotate via inspector | Yes |
| Delete and duplicate objects | Yes |
| Grid snapping | Yes |
| Save and load project | Yes |
| Auto-save with status indicator | Yes |
| Basic activity log | Yes |
| Basic version history | Yes |
| Restore previous version | Yes |
| Basic documentation and README | Yes |

### Excluded from MVP

| Feature | Reason |
|---|---|
| Full AI model training | Requires significant data — post-MVP |
| Complex scraper automation | Not core to user value in MVP |
| CAD/BIM export | Complex format — post-MVP |
| Payment and subscription system | Not needed until growth |
| Real-time multi-user editing | Complex infrastructure — post-MVP |
| Team chat and commenting | Not core to MVP value |
| Advanced conflict resolution | Requires real-time infra — post-MVP |
| Advanced architectural validation | Requires domain model training — post-MVP |
| Multi-floor buildings | Adds complexity to generation and canvas — post-MVP |
| Mobile and tablet support | Desktop-first for MVP |

---

## 19. Future Scope

| Feature | Description |
|---|---|
| Subscription plans and billing | Stripe integration, plan tiers, usage limits |
| Payment gateway | Freemium conversion, upgrade flows |
| Advanced AI generation | LLM-based prompt understanding, Claude API integration |
| AI model fine-tuning | Training on collected layout data for better generation |
| More realistic 3D materials | Textured walls, floors, furniture surfaces |
| Multi-floor buildings | Stacked floor plans, staircases connecting floors |
| Interior design suggestions | Furniture placement recommendations, style presets |
| Furniture and object library | Drag-and-drop furniture, fixtures, and fittings |
| Real-time collaboration | WebSocket-based live editing, cursor presence, conflict resolution |
| Comments and annotations | Inline design comments linked to specific objects |
| Advanced version comparison | Side-by-side visual diff of two versions |
| CAD/BIM export | DXF, IFC, and Revit-compatible export formats |
| Template marketplace | Buy, sell, and share layout templates |
| Public design gallery | Community showcase of published designs |
| Mobile and tablet support | Touch-optimised 3D canvas, responsive editor |
| API access for integrations | Developer API for third-party integration |
| White-label licensing | Platform licensing for architecture schools and firms |

---

## 20. Development Rules

### Build Philosophy

- Build step by step, sprint by sprint. Do not build features for sprints that have not started.
- The MVP must work end-to-end before any post-MVP feature work begins.
- Do not over-engineer the MVP. Simple, working, and tested is better than clever and incomplete.

### Code Quality

- Keep frontend, backend, AI logic, scraper, logging, and collaboration logic in separate modules. Do not mix concerns.
- Use clear, descriptive file and variable names. Code should read like documentation.
- Write tests before or alongside code — not after.
- Do not add error handling for scenarios that cannot happen. Handle errors at system boundaries (user input, external APIs, database).
- Do not add comments explaining what the code does. Only add comments explaining why when the reason is non-obvious.

### 3D Canvas Rules

- Mouse drag-and-drop movement must work directly inside the canvas without requiring coordinate input.
- Inspector-based editing supports precision but is not the only way to move objects.
- Keep 3D interactions smooth and responsive. Target 60fps for canvas operations.
- Canvas state is owned by the Zustand editorStore. Three.js meshes are derived views of this state.

### Logging and Versioning Rules

- Every important canvas edit, generation action, and team action must create an activity log entry.
- Auto-save must not overwrite named version history. Named versions are immutable once created.
- Draft auto-save versions are mutable until promoted to named versions by manual save.

### Security Rules

- All secrets in environment variables. Never hardcode credentials, API keys, or database URLs.
- Authenticate all API routes except register, login, health, and public share views.
- Enforce role-based permissions at the API level, not only in the frontend.
- Sanitise all user inputs before processing. Validate request schemas using Pydantic.
- Use bcrypt for password hashing. Never store plaintext passwords.

### Data Pipeline Rules

- Never scrape a site without first checking robots.txt.
- Always store source URL and access timestamp with scraped data.
- Keep scraper logic completely isolated from the main application.
- Do not use scraped data to reproduce copyrighted work. Use only for pattern and rule extraction.

### Team and Communication Rules

- Ask before making major architectural or scope changes.
- Update the README whenever local setup steps change.
- Write clear commit messages that describe what changed and why.
- Do not push directly to main. Use feature branches and pull requests.

---

## 21. Post-Strategy Summary

### Files and Folders to Create for MVP

**Priority 1 — Sprint 0 (now):**
```
docs/PROJECT_STRATEGY.md       ← this file
docs/API_PLAN.md
docs/DATA_MODEL.md
README.md
.env.example
docker-compose.yml
```

**Priority 2 — Sprint 1:**
```
backend/
  app/main.py
  app/config/settings.py
  app/database/connection.py
  app/models/user.py
  app/schemas/user.py
  app/api/auth/router.py
  app/services/auth_service.py
  app/utils/jwt.py
  app/utils/hashing.py
  app/tests/test_auth.py
  requirements.txt
  Dockerfile

frontend/
  src/App.tsx
  src/main.tsx
  src/pages/Landing/
  src/pages/Login/
  src/pages/Register/
  src/pages/Dashboard/
  src/store/authStore.ts
  src/services/auth.service.ts
  src/components/auth/LoginForm.tsx
  src/components/auth/RegisterForm.tsx
  src/components/ui/Button.tsx
  src/components/ui/Input.tsx
  package.json
  tsconfig.json
  tailwind.config.ts
  Dockerfile
```

---

### First Sprint Tasks (Sprint 1)

1. Set up FastAPI backend project with PostgreSQL connection
2. Create User model and Alembic migration
3. Implement `/api/auth/register` with password hashing
4. Implement `/api/auth/login` with JWT issuance
5. Implement `/api/auth/me` with JWT middleware
6. Write tests for all three auth endpoints
7. Set up React + TypeScript + Tailwind frontend
8. Build login page connected to auth API
9. Build register page connected to auth API
10. Build authenticated dashboard stub with protected route redirect
11. Set up Zustand auth store
12. Commit working sprint with passing tests

---

### Recommended Database Models (Summary)

| Model | Purpose |
|---|---|
| User | Registered user accounts |
| Workspace | Team/organisation grouping |
| TeamMember | User-workspace relationship with role |
| Project | Individual design project |
| ProjectMember | User-project relationship with role |
| Design | Active design state with layout JSON |
| DesignVersion | Immutable snapshot of design at a point in time |
| LayoutObject | Individual canvas objects (optional, for fine-grained logging) |
| ActivityLog | All important system events |
| ChangeLog | Field-level change records linked to ActivityLog |
| ExportRecord | Export history per project |
| ScraperSource | Permitted data sources |
| ScraperRun | Data pipeline run history |

---

### Recommended API Routes (Summary)

```
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me

GET    /api/workspaces
POST   /api/workspaces
GET    /api/workspaces/:id
PUT    /api/workspaces/:id
DELETE /api/workspaces/:id
POST   /api/workspaces/:id/invite
PUT    /api/workspaces/:id/members/:memberId/role
DELETE /api/workspaces/:id/members/:memberId

POST   /api/projects
GET    /api/projects
GET    /api/projects/:id
PUT    /api/projects/:id
DELETE /api/projects/:id
POST   /api/projects/:id/duplicate
GET    /api/projects/:id/activity

POST   /api/design/generate
POST   /api/design/refine
GET    /api/designs
GET    /api/designs/:id
PUT    /api/designs/:id
DELETE /api/designs/:id

GET    /api/projects/:id/versions
POST   /api/projects/:id/versions
GET    /api/projects/:id/versions/:versionId
POST   /api/projects/:id/restore-version

POST   /api/logs/activity
GET    /api/logs/system
GET    /api/projects/:id/logs

POST   /api/export/image
POST   /api/export/pdf
POST   /api/share/:projectId
DELETE /api/share/:projectId

POST   /api/scraper/run
GET    /api/scraper/status
GET    /api/scraper/sources

GET    /api/health
```

---

### What to Build First and Why

**1. Authentication (Sprint 1)**
Everything else depends on knowing who the user is. Without auth, no project ownership, no team roles, no activity logging. Build this first.

**2. Project and Backend API Foundation (Sprint 2)**
Projects are the container for everything else. Build the project CRUD API and error handling foundation before the UI, so the frontend has real endpoints to connect to.

**3. Frontend Shell (Sprint 3)**
Build the navigation, layout, and page structure so all future UI work has a consistent home. Keep pages empty/stubbed — the structure matters more than content at this stage.

**4. 3D Canvas with Selection and Movement (Sprint 4)**
This is the core product differentiator. Getting object selection and mouse drag-and-drop working on a hardcoded scene (before connecting to generation) proves the technical approach early, when it is cheapest to change.

**5. Layout Generation (Sprint 5)**
Connect the prompt input to the backend layout engine and render the result in the canvas. This completes the core user loop: describe → see → edit.

From Sprint 5 onward, all subsequent work builds on this foundation: refining the editing experience, adding persistence and version history, building team features, improving generation quality, and preparing for launch.

---

*Document prepared as part of ArchiAI Sprint 0 — Product Planning.*
*Next step: Begin Sprint 1 implementation following this strategy.*
