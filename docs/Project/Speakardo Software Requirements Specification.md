# **Speakardo Software Requirements Specification** 

# **(SRS)** 

Version: 1.0 

Product: Speakardo 

Category: AI Life Assistant 

Status: Living Technical Document 

# **1. Introduction** 

## **1.1 Purpose** 

This document defines the technical and functional requirements for Speakardo, an AI-powered life assistant that enables users to create reminders, manage personal memory, receive notifications, and eventually automate parts of their daily life through natural conversation. 

This SRS serves as the source of truth for engineering, design, AI systems, infrastructure, and future product expansion. 

# **2. Product Scope** 

Speakardo is not a traditional reminder application. 

Speakardo is an AI Life Assistant that: 

- Understands natural language 

- Creates reminders automatically 

- Learns user behavior 

- Maintains personal memory 

- Delivers reminders through multiple channels 

- Supports collaborative reminders 

- Evolves toward autonomous assistance 

1 

# **3. User Roles** 

## **3.1 Guest** 

Capabilities: 

- Landing page access • Signup • Login 

Restrictions: 

- Cannot create reminders • Cannot access assistant 

## **3.2 User** 

Capabilities: 

- Chat with AI 

- Create reminders 

- Manage reminders • Voice interaction • Receive notifications • Manage profile • Invite others 

## **3.3 Team Member** 

Capabilities: 

- Receive shared reminders • Collaborate on reminders • Participate in shared workspaces 

## **3.4 Family Member** 

Capabilities: 

- Receive family reminders 

- Share household reminders 

2 

## **3.5 Admin** 

Capabilities: 

- User management 

- System monitoring 

- Abuse prevention 

- Analytics access 

# **4. Functional Requirements** 

# **Module 1: Authentication** 

## **Features** 

- Email signup 

- Email login 

- Password reset 

- Social login 

- Google login 

- Apple login 

- Session management 

- JWT authentication 

- Refresh tokens 

### **Acceptance Criteria** 

User can: 

- Register account 

- Login securely 

- Logout securely 

- Recover account 

3 

# **Module 2: AI Chat Assistant** 

## **Features** 

### **Natural Language Reminder Creation** 

Examples: 

"Remind me to call Ali tomorrow at 5" 

"Wake me at 7 AM" 

"Pay electricity bill every month" 

### **AI Responsibilities** 

Extract: 

- Task • Date • Time • Recurrence • Priority 

Generate confirmation: 

"Got it. I'll remind you tomorrow at 5 PM." 

## **AI Parsing Pipeline** 

### **Level 1** 

Rule-based extraction 

Tools: 

- Regex • DateParser 

- Duckling 

### **Level 2** 

AI fallback 

4 

Providers: 

- OpenAI • Gemini 

- Claude 

Used when confidence is low. 

# **Module 3: Reminder Management** 

## **Reminder Types** 

### **One-Time Reminder** 

Example: 

Call Mom at 5 PM 

### **Recurring Reminder** 

Examples: 

Every day 

Every week 

Every month 

Custom schedules 

### **Location Reminder** 

Examples: 

Remind me when I reach office 

Remind me when I leave home 

### **Context Reminder** 

Examples: 

5 

Remind me after my meeting 

Remind me before my flight 

### **Smart Reminder** 

AI determines optimal time. 

## **Reminder Actions** 

Create 

Update 

Delete 

Archive 

Complete 

Snooze 

Reschedule 

Duplicate 

Share 

# **Module 4: Notifications** 

## **Notification Channels** 

### **Push Notification** 

Android 

iOS 

Web 

6 

### **Voice Notification** 

TTS reminder playback 

### **Email Notification** 

Optional 

### **SMS Notification** 

Premium feature 

### **AI Call Reminder** 

Premium feature 

Example: 

"Hello Nouman. 

This is your reminder. 

Take your medicine." 

Features: 

- Human-like AI voice 

- Personalized voice 

- Multiple languages 

- Retry if unanswered 

# **Module 5: Shared Reminders** 

## **Shared Reminder System** 

Users can assign reminders to others. 

Example: 

Manager → Employee 

7 

Parent → Child 

Husband → Wife 

Friend → Friend 

### **Shared Reminder States** 

Pending 

Accepted 

Declined 

Completed Expired 

### **Features** 

Assign reminder 

Transfer reminder 

Track completion 

Send follow-ups 

View history 

# **Module 6: Team Workspaces** 

## **Workspace Features** 

Create team 

Invite members 

Assign reminders 

Shared schedules 

8 

Shared tasks 

Shared notifications 

Team analytics 

## **Roles** 

Owner 

Admin 

Member 

Viewer 

# **Module 7: Voice Assistant** 

## **Features** 

Voice Input 

Speech-to-text 

Voice Commands 

Hands-free usage 

Wake words 

Future: 

"Hey Speakardo" 

## **Supported Languages** 

English 

Urdu 

9 

Arabic 

Hindi 

Future multilingual support 

# **Module 8: AI Memory System** 

## **Personal Memory** 

Store: 

Important dates 

Preferences 

Relationships 

Health information 

Personal notes 

Life events 

### **Examples** 

"My mother's birthday is June 10." 

"I prefer meetings after 10 AM." 

## **Memory Retrieval** 

"What did I tell you about my mother?" 

"When is my next dentist appointment?" 

# **Module 9: Calendar Integration** 

Integrations: 

10 

Google Calendar 

Apple Calendar 

Outlook 

## **Features** 

Sync events 

Conflict detection 

Smart scheduling 

Availability checking 

# **Module 10: AI Scheduling Assistant** 

Examples: 

"Find time next week for a dentist appointment." 

"Move all meetings after 3 PM." 

Capabilities: 

Schedule optimization 

Conflict resolution 

Time blocking 

Priority management 

# **Module 11: Autonomous Assistant** 

Future System 

Capabilities: 

11 

Book appointments 

Send messages 

Reschedule meetings 

Order services 

Manage daily routines 

Take actions with permission 

# **Module 12: Analytics** 

User Analytics 

Completed reminders 

Missed reminders 

Reminder categories 

Behavior trends 

Productivity metrics 

# **5. Database Design** 

## **Users** 

Fields: 

id 

email 

password_hash 

name 

avatar_url 

12 

timezone 

language 

created_at 

updated_at 

## **Devices** 

Fields: 

id 

user_id 

device_token 

platform 

last_seen 

## **Reminders** 

Fields: 

id 

user_id 

title 

description 

datetime_utc 

repeat_rule 

priority 

status 

13 

source 

created_at 

updated_at 

## **ReminderAssignments** 

Fields: 

id 

reminder_id 

sender_id 

receiver_id 

status 

assigned_at 

completed_at 

## **Notifications** 

Fields: 

id 

user_id 

reminder_id 

channel 

status 

sent_at 

opened_at 

14 

## **Memories** 

Fields: 

id 

user_id 

memory_type 

content 

importance_score 

created_at 

## **Teams** 

Fields: 

id 

name 

owner_id 

created_at 

## **TeamMembers** 

Fields: 

id 

team_id 

user_id 

role 

15 

## **AIInteractions** 

Fields: 

id 

user_id 

prompt 

response 

provider 

tokens 

cost 

created_at 

# **6. API Requirements** 

Authentication 

POST /auth/register 

POST /auth/login 

POST /auth/logout 

POST /auth/refresh 

Chat 

POST /chat 

POST /voice 

GET /chat/history 

Reminders 

16 

POST /reminders 

GET /reminders 

GET /reminders/{id} 

PUT /reminders/{id} 

DELETE /reminders/{id} 

Shared Reminders 

POST /shared 

GET /shared 

PUT /shared/{id} 

Teams 

POST /teams 

GET /teams 

POST /teams/invite 

Memory 

POST /memory 

GET /memory 

DELETE /memory/{id} 

Devices 

POST /devices/register 

DELETE /devices/{id} 

17 

# **7. Non-Functional Requirements** 

## **Performance** 

Reminder creation: 

< 2 seconds 

AI response: 

< 5 seconds 

Notification latency: 

< 30 seconds 

## **Scalability** 

Support: 

100,000+ users 

1M reminders/day 

Horizontal scaling support 

## **Security** 

JWT authentication 

HTTPS only 

Encrypted passwords 

Rate limiting 

Secret management 

Data isolation 

Audit logs 

18 

## **Reliability** 

99.9% uptime 

Retry mechanisms 

Dead-letter queue support 

Backup system 

# **8. UI/UX Requirements** 

## **Design Principles** 

Futuristic 

Premium 

Immersive 

AI-native 

Memorable 

## **Requirements** 

Unique layouts 

3D elements 

Animated assistant 

Glassmorphism 

Dark mode 

Micro interactions 

Voice-first experience 

19 

Responsive design 

Accessibility support 

# **9. Technical Architecture** 

Frontend 

Flutter 

Backend 

Python 

FastAPI 

Database 

PostgreSQL 

Cache 

Redis 

Queue 

Celery 

AI Providers 

OpenAI 

Gemini 

Claude 

Notifications 

20 

Firebase Cloud Messaging 

Voice 

Whisper 

ElevenLabs 

OpenAI TTS 

Infrastructure 

Docker 

AWS 

Cloud Run 

Render 

Railway 

# **10. MVP Scope** 

Included: 

Authentication 

Chat interface 

Reminder extraction 

Reminder management 

Push notifications 

Voice input 

Basic AI parsing 

Device registration 

21 

PostgreSQL 

FCM integration 

Excluded: 

AI memory 

Team workspaces 

AI calls 

Calendar integrations 

Autonomous actions 

Advanced analytics 

# **11. Future Roadmap** 

Phase 1 

AI Reminder Assistant 

Phase 2 

Voice Assistant 

Phase 3 

Shared Reminders 

Phase 4 

AI Memory 

Phase 5 

22 

Calendar Assistant 

Phase 6 

AI Phone Calls 

Phase 7 

Team Collaboration 

Phase 8 

Autonomous Life Assistant 

Phase 9 

AI Life Operating System 

# **12. Risks & Assumptions** 

## **Risks** 

High AI costs 

Notification delivery failures 

User retention challenges 

Platform restrictions 

Voice infrastructure costs 

Privacy concerns 

## **Assumptions** 

Users prefer natural language over forms 

23 

Users trust AI for reminders 

Push notifications remain effective 

AI accuracy remains high 

Mobile-first experience is preferred 

Future automation demand will increase 

# **North Star Requirement** 

The user should be able to say: 

"Speakardo, handle it." 

And trust that it will. 

24 

