const TASKS_BY_AGENT: Record<string, string[]> = {
  academic: [
    "Fetching CGPA and semester results…",
    "Looking up course registration status…",
    "Checking attendance summary…",
  ],
  library: [
    "Searching catalog for available books…",
    "Retrieving journal article PDF…",
    "Checking due dates for borrowed items…",
  ],
  campus: [
    "Fetching latest campus notices…",
    "Checking room booking availability…",
    "Looking up shuttle departure times…",
  ],
  career: [
    "Scanning job board for internships…",
    "Analyzing CV against job requirements…",
    "Building personalized career roadmap…",
  ],
  coding: [
    "Debugging Python assignment code…",
    "Generating unit tests for function…",
    "Explaining algorithm time complexity…",
  ],
  research: [
    "Searching academic papers on topic…",
    "Formatting citations in APA style…",
    "Summarizing literature review section…",
  ],
  wellness: [
    "Suggesting stress-relief techniques…",
    "Recommending study-break schedule…",
    "Sharing mindfulness exercises…",
  ],
  finance: [
    "Checking tuition fee balance…",
    "Looking up scholarship eligibility…",
    "Reviewing payment deadline…",
  ],
  vision: [
    "Analyzing uploaded screenshot…",
    "Extracting text from PDF document…",
    "Identifying objects in camera feed…",
  ],
  voice: [
    "Transcribing voice input…",
    "Generating spoken response…",
    "Processing live conversation stream…",
  ],
  exam: [
    "Fetching upcoming exam schedule…",
    "Checking result publication date…",
    "Reviewing academic calendar events…",
  ],
  hostel: [
    "Checking hostel room availability…",
    "Submitting maintenance request…",
    "Looking up mess menu schedule…",
  ],
  transport: [
    "Tracking live shuttle location…",
    "Fetching route map and stops…",
    "Booking campus vehicle…",
  ],
  event: [
    "Listing upcoming campus events…",
    "Registering for workshop…",
    "Finding club meeting schedule…",
  ],
  complaint: [
    "Filing student grievance report…",
    "Checking complaint ticket status…",
    "Routing feedback to department…",
  ],
  notification: [
    "Fetching unread announcements…",
    "Updating notification preferences…",
    "Sending alert to student groups…",
  ],
  fee: [
    "Calculating outstanding fee balance…",
    "Checking waiver application status…",
    "Generating payment receipt…",
  ],
  general: [
    "Handling open-ended student query…",
    "Clarifying user intent…",
    "Providing general campus information…",
  ],
  computer_use: [
    "Moving cursor to target element…",
    "Typing into application form…",
    "Capturing screen state…",
  ],
  copycat: [
    "Replaying recorded login workflow…",
    "Recording new user action sequence…",
    "Validating automation script steps…",
  ],
  planning: [
    "Decomposing goal into plan steps…",
    "Assigning steps to specialist agents…",
    "Monitoring parallel task execution…",
  ],
  routine: [
    "Setting assignment deadline reminder…",
    "Building daily study routine…",
    "Scheduling weekly revision blocks…",
  ],
};

const CATEGORY_TASKS: Record<string, string[]> = {
  orchestration: ["Routing request to planning agent…", "Coordinating multi-agent workflow…"],
  computer: ["Delegating to automation agent…", "Preparing screen control task…"],
  productivity: ["Assigning coding/research task…", "Queueing productivity workflow…"],
  university: ["Routing to campus service agent…", "Matching query to university agent…"],
  ai: ["Dispatching to vision/voice agent…", "Preparing multimodal analysis…"],
  general: ["Forwarding to general handler…", "Escalating unmatched query…"],
};

const MODEL_TASKS = [
  "Reasoning over student intent with Gemini…",
  "Selecting specialist agents for parallel execution…",
  "Synthesizing multi-agent tool results…",
  "Applying supervisor policies and skills…",
];

let taskIndex = 0;

export function getSimulatedModelTask(engine = "antigravity"): string {
  const task = MODEL_TASKS[taskIndex % MODEL_TASKS.length];
  taskIndex += 1;
  return engine === "legacy" ? `Legacy supervisor: ${task}` : task;
}

export function getSimulatedTask(agentId: string, category?: string): string {
  const pool = TASKS_BY_AGENT[agentId];
  if (pool?.length) {
    const task = pool[taskIndex % pool.length];
    taskIndex += 1;
    return task;
  }
  const catPool = category ? CATEGORY_TASKS[category] : undefined;
  if (catPool?.length) return catPool[taskIndex++ % catPool.length];
  return "Processing student request…";
}

export function formatRoutingEvent(category: string): string {
  const label =
    {
      orchestration: "Orchestration",
      computer: "Computer Use",
      productivity: "Productivity",
      university: "University",
      ai: "AI & Vision",
      general: "General",
    }[category] ?? category;
  return `Routing → ${label}`;
}
