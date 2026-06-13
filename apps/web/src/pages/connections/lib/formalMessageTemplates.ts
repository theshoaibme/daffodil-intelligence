import type { ResearchConnection } from "../types";

export type MessagePurpose = "collaboration" | "research-discussion" | "institutional-inquiry";

export function formalSalutation(connection: ResearchConnection): string {
  if (connection.kind === "institution") {
    return `Dear ${connection.name} Research Office,`;
  }

  const name = connection.name.trim();
  if (/^prof/i.test(name)) {
    return `Dear ${name},`;
  }

  const trailingLast = name.match(/\b([A-Z][a-z]{2,})$/);
  if (trailingLast) {
    return `Dear Dr. ${trailingLast[1]},`;
  }

  const commaLast = name.match(/^([A-Z][a-z]{2,}),/);
  if (commaLast) {
    return `Dear Dr. ${commaLast[1]},`;
  }

  return `Dear ${name},`;
}

export function defaultClosing(senderName: string): string {
  return `Sincerely,\n${senderName || "Research Scholar"}\nDaffodil Intelligence Network`;
}

export function buildFormalTemplate(
  purpose: MessagePurpose,
  connection: ResearchConnection,
  senderName: string,
): { subject: string; body: string; closing: string } {
  const paperRef = connection.featuredPaper?.title ?? "your recent publication";
  const focus = connection.focus;
  const recipient = connection.kind === "institution" ? connection.name : connection.name;

  const templates: Record<MessagePurpose, { subject: string; body: string }> = {
    collaboration: {
      subject: `Collaboration inquiry — ${paperRef}`,
      body: `I hope this message finds you well. I am writing to express my interest in potential collaboration with ${recipient} regarding work in ${focus}.

Your research on "${paperRef}" aligns closely with my current academic interests. I would welcome the opportunity to discuss shared objectives, methodological approaches, or co-authorship possibilities at your convenience.

Please let me know if you would be open to a brief correspondence or virtual meeting to explore this further.`,
    },
    "research-discussion": {
      subject: `Research discussion — ${focus}`,
      body: `I am reaching out respectfully to inquire about your research in ${focus}, particularly in relation to "${paperRef}".

I would appreciate any guidance you might offer on the direction of this work, relevant literature, or opportunities for scholarly exchange within your network.

Thank you for your time and consideration.`,
    },
    "institutional-inquiry": {
      subject: `Institutional research partnership inquiry`,
      body: `I am writing on behalf of my academic interests to inquire about research engagement opportunities with ${recipient}.

Our shared focus on ${focus}, including publications such as "${paperRef}", suggests meaningful scope for institutional collaboration, student exchange, or joint research initiatives.

I would be grateful for information on appropriate channels to submit a formal partnership proposal.`,
    },
  };

  const chosen = templates[purpose];
  return {
    subject: chosen.subject,
    body: chosen.body,
    closing: defaultClosing(senderName),
  };
}

export function formatFormalMessage(message: {
  subject: string;
  salutation: string;
  body: string;
  closing: string;
}): string {
  return `${message.salutation}\n\n${message.body}\n\n${message.closing}`;
}

export function formatMessageDate(iso: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(iso));
}
